"""
editor/widgets/viewport_widget.py
==================================
Widget de Viewport gráfica PySide6/Pygame.

Arquitetura:
  - A viewport desenha e adapta input Qt/Pygame para a cena ativa.
  - O SceneModel/ViewModel apenas espelha o estado da cena para o Outliner.
  - Qualquer criação/deleção de objeto passa pela cena ativa da viewport.
  - A seleção pertence ao SelectionManager do Editor Runtime.
  - Monkey-patches silenciam os painéis legados do Pygame (toolbar, painel esq/dir, statusbar).
"""

import time
import pygame
import numpy as np
from types import SimpleNamespace
from typing import Optional, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QPainter, QImage, QMouseEvent, QKeyEvent, QWheelEvent

from editor.core.event_bus import (
    EventBus,
    EVENT_PLAY_STATE_CHANGED,
    EVENT_PROPERTY_CHANGED,
    EVENT_HIERARCHY_UPDATED,
)
from editor.runtime.selection_manager import SelectionManager
from editor.viewmodels.scene_viewmodel import SceneViewModel


class ViewportWidget(QWidget):
    """
    Viewport gráfica embarcando o loop do Pygame dentro de um QOpenGLWidget.

    Regras de sincronização:
      1. A cena ativa (active_scene) mantém os GameObjects enquanto a Fase 1 migra.
      2. O SceneModel é apenas um espelho para o Outliner — alimentado daqui.
      3. Criar/deletar objetos: chamar sempre active_scene.spawn_object / delete_selected.
      4. A seleção é centralizada no SelectionManager.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportWidget")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        # Pygame (display headless — janela real fica no Qt)
        pygame.init()
        pygame.font.init()

        self.viewmodel: Optional[SceneViewModel] = None
        self.selection_manager: Optional[SelectionManager] = None
        self.runtime_manager = None
        self.active_scene = None          # Editor2DScene ou EditorScene (3D)
        self.editor_mode: str = "2D"

        # Coordenada local do cursor dentro deste widget (substituição de pygame.mouse.get_pos)
        self._qt_mouse_pos: tuple = (0, 0)
        pygame.mouse.get_pos = lambda: self._qt_mouse_pos

        # Surface de renderização Pygame (framebuffer)
        self.pg_surface: Optional[pygame.Surface] = None
        self._vp_w: int = 800
        self._vp_h: int = 600

        self._last_time: float = time.time()

        # Assina eventos globais
        EventBus.subscribe(EVENT_PLAY_STATE_CHANGED,  self._on_play_state_changed)
        EventBus.subscribe(EVENT_PROPERTY_CHANGED,    self._on_property_changed)

        # Tick a 60 FPS
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    # ──────────────────────────────────────────────────────────────────────────
    # Inicialização
    # ──────────────────────────────────────────────────────────────────────────

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        """
        Conecta o ViewModel e inicializa a cena 2D padrão.
        Chamado pela MainWindow após criar os docks.
        """
        self.viewmodel = viewmodel
        if self.selection_manager is not viewmodel.selection_manager:
            if self.selection_manager is not None:
                self.selection_manager.unsubscribe(self._on_runtime_selection_changed)
            self.selection_manager = viewmodel.selection_manager
            self.selection_manager.subscribe(self._on_runtime_selection_changed)

        # Cria a cena 2D inicial
        from editor_legacy.editor_2d import Editor2DScene
        self.active_scene = Editor2DScene()
        self.active_scene.start()

        # Aplica shims ANTES de sincronizar o modelo
        self._apply_qt_shims()

        # Espelha os objetos da cena no SceneModel (Outliner)
        self._sync_model_from_scene()

    def set_runtime_manager(self, runtime_manager) -> None:
        self.runtime_manager = runtime_manager

    # ──────────────────────────────────────────────────────────────────────────
    # Sincronização Cena ↔ Modelo
    # ──────────────────────────────────────────────────────────────────────────

    def _sync_model_from_scene(self) -> None:
        """
        Repopula o SceneModel com os objetos da cena ativa.
        Deve ser chamado sempre que a lista de objetos mudar.
        """
        if not self.viewmodel or not self.active_scene:
            return

        model = self.viewmodel._model
        model.clear()

        for obj in self.active_scene.editable_objects:
            model.add_object(obj)

        self.sync_selection_from_scene()

        # Notifica Outliner e Inspector via sinal de hierarquia
        self.viewmodel.on_model_hierarchy_changed()

    def _selected_from_scene(self):
        """Le a selecao da cena legada enquanto ela ainda usa selected_index."""
        if not self.active_scene:
            return None
        objs = getattr(self.active_scene, "editable_objects", [])
        idx = getattr(self.active_scene, "selected_index", -1)
        return objs[idx] if 0 <= idx < len(objs) else None

    def selected_object(self):
        """Retorna o objeto selecionado pelo SelectionManager."""
        if self.selection_manager is not None:
            return self.selection_manager.selected
        if self.viewmodel is not None:
            return self.viewmodel.selected_object
        return None

    def select_object(self, obj) -> None:
        """Seleciona um objeto via Editor Runtime."""
        if self.selection_manager is not None:
            self.selection_manager.set_selected(obj)
        elif self.viewmodel is not None:
            self.viewmodel.selected_object = obj
        else:
            self._on_runtime_selection_changed(obj)

    def clear_selection(self) -> None:
        self.select_object(None)

    def sync_selection_from_scene(self) -> None:
        """Sincroniza a selecao da cena legada com o SelectionManager."""
        self.select_object(self._selected_from_scene())

    def world_to_viewport(self, point) -> tuple[float, float]:
        """Converte coordenadas de mundo para coordenadas locais da viewport."""
        if self.active_scene is None:
            return float(point[0]), float(point[1])
        if hasattr(self.active_scene, "_layout") and hasattr(self.active_scene, "_world_to_vp"):
            return self.active_scene._world_to_vp(np.asarray(point, dtype=np.float32), self.active_scene._layout())
        return float(point[0]), float(point[1])

    def viewport_to_world(self, point) -> np.ndarray:
        """Converte coordenadas locais da viewport para coordenadas de mundo."""
        if self.active_scene is None:
            return np.array([float(point[0]), float(point[1]), 0.0], dtype=np.float32)
        if hasattr(self.active_scene, "_layout") and hasattr(self.active_scene, "_vp_to_world"):
            return self.active_scene._vp_to_world(float(point[0]), float(point[1]), self.active_scene._layout())
        return np.array([float(point[0]), float(point[1]), 0.0], dtype=np.float32)

    def create_object(self, shape_type: str) -> None:
        """
        Ponto de entrada único para criação de objetos via menu Criar.
        Delega para a cena ativa e depois sincroniza o modelo.
        """
        if not self.active_scene:
            return

        if hasattr(self.active_scene, "spawn_object"):
            self.active_scene.spawn_object(shape_type)
            self._sync_model_from_scene()

    def delete_selected_object(self) -> None:
        """Deleta o objeto selecionado na cena ativa."""
        if not self.active_scene:
            return
        if hasattr(self.active_scene, "delete_selected"):
            self.active_scene.delete_selected()
            self._sync_model_from_scene()

    def duplicate_selected_object(self) -> None:
        """Duplica o objeto selecionado na cena ativa."""
        if not self.active_scene:
            return
        if hasattr(self.active_scene, "duplicate_selected"):
            self.active_scene.duplicate_selected()
            self._sync_model_from_scene()

    # ──────────────────────────────────────────────────────────────────────────
    # Alternância de Modo 2D/3D
    # ──────────────────────────────────────────────────────────────────────────

    def change_editor_mode(self, mode: str) -> None:
        """Troca a cena ativa entre editor 2D e 3D preservando os objetos."""
        if self.editor_mode == mode or not self.active_scene:
            return

        # Salva objetos e seleção atuais
        objs = list(self.active_scene.editable_objects)
        sel_obj = self.selected_object()

        self.editor_mode = mode

        if mode == "2D":
            from editor_legacy.editor_2d import Editor2DScene
            self.active_scene = Editor2DScene()
        else:
            from editor_legacy.scene import EditorScene
            self.active_scene = EditorScene()

        self.active_scene.start()

        # Transfere objetos (limpa os objetos padrão da nova cena e reinsere os salvos)
        self.active_scene.editable_objects.clear()
        self.active_scene.game_objects.clear()
        for obj in objs:
            self.active_scene._add_go(obj) if hasattr(self.active_scene, "_add_go") else None
            if obj not in self.active_scene.game_objects:
                self.active_scene.game_objects.append(obj)
            self.active_scene.editable_objects.append(obj)

        # Sincroniza seleção
        if sel_obj in objs:
            self.active_scene.selected_index = objs.index(sel_obj)
        else:
            self.active_scene.selected_index = -1

        self._apply_qt_shims()
        self.resizeGL(self.width(), self.height())
        self._sync_model_from_scene()
        self.update()

    # ──────────────────────────────────────────────────────────────────────────
    # Qt Shims — silencia painéis legados do Pygame
    # ──────────────────────────────────────────────────────────────────────────

    def _apply_qt_shims(self) -> None:
        """
        Monkey-patch nas cenas legadas do Pygame:
          1. Layout dinâmico: captura self._vp_w / self._vp_h em tempo de execução.
          2. Oculta toolbar, painel esq/dir e statusbar legados do Pygame.
          3. Editor 3D: desativa modais e configura câmera.
        Chamado após criar/trocar a cena e a cada resize.
        """
        if not self.active_scene:
            return

        widget = self  # captura por referência — sem valores fixos
        scene  = self.active_scene

        # ── Editor 2D ────────────────────────────────────────────────────────
        if hasattr(scene, "_layout") and not hasattr(scene, "_lay"):

            def _qt_layout_2d(_w=widget):
                """Layout que lê dimensões reais do widget a cada frame."""
                w, h = _w._vp_w, _w._vp_h
                return {
                    "sw": w, "sh": h,
                    "vp_left":   0,
                    "vp_top":    0,
                    "vp_right":  w,
                    "vp_bottom": h,
                    "vp_w":      w,
                    "vp_h":      h,
                    "panel_left_w":  0,
                    "panel_right_x": w,
                    "panel_right_w": 0,
                    "status_y":  h,
                }
            scene._layout = _qt_layout_2d

            # Move todos os botões legados do Pygame para fora da tela
            # (rect com y negativo garante que collidepoint() nunca dispare)
            for btn in getattr(scene, "_all_toolbar_btns", []):
                btn.rect.y = -9999

            def _qt_draw_2d(screen, _scene=scene):
                lay = _scene._layout()
                screen.fill((28, 29, 36))
                if hasattr(_scene, "_draw_viewport"):
                    _scene._draw_viewport(screen, lay)
                    return
                for idx, obj in enumerate(getattr(_scene, "game_objects", [])):
                    if obj is getattr(_scene, "cam_obj", None):
                        continue
                    if hasattr(_scene, "_draw_object"):
                        _scene._draw_object(screen, obj, idx, 1.0, lay)
                    elif hasattr(obj, "draw"):
                        obj.draw(screen)
            scene.draw = _qt_draw_2d

            # Guarda o original e substitui por wrapper que filtra eventos
            if not hasattr(scene.handle_event, "__wrapped__"):
                _orig_handle = scene.handle_event

                def _qt_handle_event_2d(event, _scene=scene, _orig=_orig_handle):
                    """
                    Wrapper que deixa passar apenas:
                      - Eventos de teclado e scroll (sempre).
                      - Eventos de mouse dentro da viewport (filtra a hierarquia
                        e o inspector legados que ficavam em x < 240 e x > sw-260).
                    """
                    import pygame as _pg
                    if event.type in (_pg.KEYDOWN, _pg.KEYUP):
                        _orig(event)
                        return
                    if event.type == _pg.MOUSEWHEEL:
                        _orig(event)
                        return
                    if event.type in (_pg.MOUSEBUTTONDOWN, _pg.MOUSEBUTTONUP, _pg.MOUSEMOTION):
                        lay = _scene._layout()
                        mx, my = _pg.mouse.get_pos()
                        # Só processa se o mouse está dentro da viewport completa
                        if hasattr(_scene, "_in_viewport"):
                            inside_viewport = _scene._in_viewport(mx, my, lay)
                        else:
                            left = int(lay.get("vp_left", lay.get("viewport_x", 0)))
                            top = int(lay.get("vp_top", lay.get("viewport_y", 0)))
                            width = int(lay.get("vp_w", lay.get("viewport_w", 0)))
                            height = int(lay.get("vp_h", lay.get("viewport_h", 0)))
                            inside_viewport = left <= mx <= left + width and top <= my <= top + height
                        if inside_viewport:
                            _orig(event)
                        return
                    _orig(event)

                _qt_handle_event_2d.__wrapped__ = _orig_handle
                scene.handle_event = _qt_handle_event_2d

        # ── Editor 3D ────────────────────────────────────────────────────────
        elif hasattr(scene, "_lay"):

            def _sync_3d_layout(_w=widget, _lay=scene._lay):
                """Atualiza os Rects de layout do editor 3D com dimensões reais."""
                w, h = _w._vp_w, _w._vp_h
                _lay.left_panel_rect    = pygame.Rect(0, 0, 0, 0)
                _lay.right_panel_rect   = pygame.Rect(w, 0, 0, 0)
                _lay.top_bar_rect       = pygame.Rect(0, 0, w, 0)
                _lay.status_bar_rect    = pygame.Rect(0, h, w, 0)
                _lay.viewport_rect      = pygame.Rect(0, 0, w, h)
                _lay.viewport_edit_rect = pygame.Rect(0, 0, w, h)
                _lay.viewport_game_rect = pygame.Rect(0, 0, w, h)
                _lay.right_x    = w
                _lay.viewport_y = 0
                _lay.viewport_h = h
                _lay.viewport_w = w

            # Aplica imediatamente
            _sync_3d_layout()
            # Congela atualização interna de layout
            scene._lay.update = lambda sw, sh: None

            def _qt_draw_3d(screen, _scene=scene, _w=widget):
                # Sincroniza layout a cada frame (responde ao resize)
                _sync_3d_layout()

                # Suprime modais/painéis legados
                _scene.showing_welcome    = False
                _scene.showing_templates  = False
                _scene.showing_help_modal = False
                if hasattr(_scene, "code_editor"):
                    _scene.code_editor.is_open = False

                lay = _scene._lay

                # Câmera 3D ocupa toda a viewport
                cam = _scene.camera_comp
                cam.viewport_x      = 0
                cam.viewport_y      = 0
                cam.viewport_width  = lay.viewport_rect.width
                cam.viewport_height = lay.viewport_rect.height
                cam.update(0.0)

                from engine.graphics.renderer3d import Camera3D, MeshRenderer3D
                Camera3D.main = cam

                screen.fill((28, 29, 36))
                _scene._draw_floor_grid(screen)

                for go in _scene.game_objects:
                    go.draw(screen)
                    if (_scene.selected_index >= 0
                            and go is _scene.editable_objects[_scene.selected_index]):
                        r = go.get_component(MeshRenderer3D)
                        if r:
                            ow, oc, olw = r.wireframe, r.color, r.line_width
                            r.wireframe, r.color, r.line_width = True, (80, 160, 255), 3
                            r.draw(screen)
                            r.wireframe, r.color, r.line_width = ow, oc, olw

                _scene._draw_gizmo(screen)

            scene.draw = _qt_draw_3d

    # ──────────────────────────────────────────────────────────────────────────
    # Foco da câmera
    # ──────────────────────────────────────────────────────────────────────────

    def focus_camera_on_selected(self) -> None:
        """Tecla F — centraliza câmera no objeto selecionado."""
        if not self.active_scene or not self.viewmodel:
            return
        obj = self.selected_object()
        if not obj:
            return

        if hasattr(self.active_scene, "camera") and hasattr(self.active_scene, "cam_obj"):
            # Editor 2D: centraliza câmera 2D
            from engine.graphics.camera2d import Camera2D
            if Camera2D.main:
                Camera2D.main.transform.position[0] = obj.transform.position[0]
                Camera2D.main.transform.position[1] = obj.transform.position[1]
        elif hasattr(self.active_scene, "camera_comp"):
            # Editor 3D: orbita em torno do objeto
            ctrl = getattr(self.active_scene, "camera_controller", None)
            if ctrl:
                ctrl.target   = obj.transform.position.copy()
                ctrl.distance = 5.0

        self.update()

    # ──────────────────────────────────────────────────────────────────────────
    # GL + Render
    # ──────────────────────────────────────────────────────────────────────────

    def initializeGL(self) -> None:
        pass

    def resizeEvent(self, event) -> None:
        self.resizeGL(self.width(), self.height())
        super().resizeEvent(event)

    def resizeGL(self, w: int, h: int) -> None:
        self._vp_w = max(32, w)
        self._vp_h = max(32, h)
        self.pg_surface = pygame.Surface((self._vp_w, self._vp_h), pygame.SRCALPHA)
        self._apply_qt_shims()

    def paintEvent(self, event) -> None:
        self.paintGL()

    def closeEvent(self, event) -> None:
        self.shutdown()
        super().closeEvent(event)

    def shutdown(self) -> None:
        self._timer.stop()
        self.pg_surface = None

    def paintGL(self) -> None:
        if not self.pg_surface or not self.active_scene:
            return

        self.active_scene.draw(self.pg_surface)

        is_playing = (
            self.runtime_manager is not None
            and getattr(self.runtime_manager, "is_playing", False)
        )
        if not is_playing:
            from editor.gizmos.gizmo_registry import GizmoRegistry
            objs = getattr(self.active_scene, "editable_objects", getattr(self.active_scene, "game_objects", []))
            for obj in objs:
                if obj.name == "EditorCamera":
                    continue
                for comp in obj.components:
                    draw_func = GizmoRegistry.get_gizmo(comp.component_type)
                    if draw_func:
                        try:
                            draw_func(comp, self.pg_surface, self.active_scene)
                        except Exception:
                            pass

        raw = pygame.image.tostring(self.pg_surface, "RGBA")
        img = QImage(raw, self._vp_w, self._vp_h,
                     self._vp_w * 4, QImage.Format_RGBA8888)

        p = QPainter(self)
        p.drawImage(0, 0, img)
        p.end()

    @Slot()
    def _tick(self) -> None:
        now = time.time()
        dt  = min(now - self._last_time, 0.1)
        self._last_time = now

        if self.active_scene:
            if (
                self.runtime_manager is not None
                and getattr(self.runtime_manager, "is_playing", False)
                and getattr(self.runtime_manager, "runtime_scene", None) is self.active_scene
            ):
                self.runtime_manager.tick(dt)

            # Edit mode must not advance the scene. Calling Scene.update() here
            # also calls RigidBody.update(), which applies gravity and makes
            # objects fall before Play has started.
            self._sync_selection_to_model()

        self.update()

    def _sync_selection_to_model(self) -> None:
        """Propaga a mudança de selected_index da cena legada para o runtime."""
        if not self.active_scene:
            return
        sel = self._selected_from_scene()

        if sel is not self.selected_object():
            self.select_object(sel)

    # ──────────────────────────────────────────────────────────────────────────
    # Handlers de Eventos do EventBus
    # ──────────────────────────────────────────────────────────────────────────

    def _on_play_state_changed(self, state: str) -> None:
        if not self.active_scene or not hasattr(self.active_scene, "playing"):
            return

        if state == "play" and not self.active_scene.playing:
            self.active_scene.toggle_play()
        elif state in ("stop", "pause") and self.active_scene.playing:
            self.active_scene.toggle_play()

    def _on_runtime_selection_changed(self, obj) -> None:
        """Propaga seleção do runtime para a cena legada."""
        if not self.active_scene:
            return
        objs = getattr(self.active_scene, "editable_objects", [])
        if obj in objs:
            self.active_scene.selected_index = objs.index(obj)
        else:
            self.active_scene.selected_index = -1
        self.update()

    def _on_property_changed(self, component_name: str, property_name: str, value) -> None:
        if component_name != "Editor":
            return
        if property_name == "tool_mode" and self.active_scene:
            mode_map = {
                "move":   "translate",
                "rotate": "rotate",
                "scale":  "scale",
            }
            gizmo = mode_map.get(str(value))
            if gizmo and hasattr(self.active_scene, "gizmo_mode"):
                self.active_scene.gizmo_mode = gizmo
        elif property_name == "camera_mode":
            self.change_editor_mode(str(value))
        elif property_name == "grid_state" and self.active_scene:
            if hasattr(self.active_scene, "show_grid"):
                self.active_scene.show_grid = bool(value)

    # ──────────────────────────────────────────────────────────────────────────
    # Mapeamento de Eventos Qt → Pygame
    # ──────────────────────────────────────────────────────────────────────────

    def _qt_btn_to_pg(self, btn: Qt.MouseButton) -> int:
        if btn == Qt.LeftButton:   return 1
        if btn == Qt.MiddleButton: return 2
        if btn == Qt.RightButton:  return 3
        return 0

    def _runtime_input_active(self) -> bool:
        return bool(
            self.runtime_manager is not None
            and getattr(self.runtime_manager, "is_playing", False)
            and getattr(self.runtime_manager, "runtime_scene", None) is self.active_scene
        )

    def _qt_key_to_input_name(self, qt_key: Qt.Key) -> str:
        special = {
            Qt.Key_Escape: "Escape",
            Qt.Key_Delete: "Delete",
            Qt.Key_Backspace: "Backspace",
            Qt.Key_Left: "Left",
            Qt.Key_Right: "Right",
            Qt.Key_Up: "Up",
            Qt.Key_Down: "Down",
            Qt.Key_Space: "Space",
            Qt.Key_Return: "Enter",
            Qt.Key_Enter: "Enter",
            Qt.Key_Shift: "Shift",
            Qt.Key_Control: "Control",
            Qt.Key_Alt: "Alt",
            Qt.Key_Tab: "Tab",
        }
        for index in range(1, 13):
            if qt_key == getattr(Qt, f"Key_F{index}"):
                return f"F{index}"
        if Qt.Key_A <= qt_key <= Qt.Key_Z:
            return chr(ord("A") + int(qt_key - Qt.Key_A))
        if Qt.Key_0 <= qt_key <= Qt.Key_9:
            return chr(ord("0") + int(qt_key - Qt.Key_0))
        return special.get(qt_key, str(int(qt_key)))

    def _forward_runtime_input(self, event_type: str, **payload) -> None:
        if not self._runtime_input_active():
            return
        self.runtime_manager.handle_input_event(SimpleNamespace(type=event_type, **payload))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._qt_mouse_pos = (event.x(), event.y())
        self._forward_runtime_input(
            "mouse_down",
            pos=self._qt_mouse_pos,
            button=self._qt_btn_to_pg(event.button()),
        )
        if self.active_scene:
            pg_ev = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                pos=self._qt_mouse_pos,
                button=self._qt_btn_to_pg(event.button()),
            )
            self.active_scene.handle_event(pg_ev)
            # Sincroniza seleção imediatamente após o clique
            self._sync_selection_to_model()
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._qt_mouse_pos = (event.x(), event.y())
        self._forward_runtime_input(
            "mouse_up",
            pos=self._qt_mouse_pos,
            button=self._qt_btn_to_pg(event.button()),
        )
        if self.active_scene:
            pg_ev = pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                pos=self._qt_mouse_pos,
                button=self._qt_btn_to_pg(event.button()),
            )
            self.active_scene.handle_event(pg_ev)
            self._sync_selection_to_model()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._qt_mouse_pos = (event.x(), event.y())
        self._forward_runtime_input("mouse_move", pos=self._qt_mouse_pos)
        if self.active_scene:
            btns = event.buttons()
            pg_ev = pygame.event.Event(
                pygame.MOUSEMOTION,
                pos=self._qt_mouse_pos,
                buttons=(
                    1 if btns & Qt.LeftButton   else 0,
                    1 if btns & Qt.MiddleButton  else 0,
                    1 if btns & Qt.RightButton   else 0,
                ),
                rel=(0, 0),
            )
            self.active_scene.handle_event(pg_ev)
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.active_scene:
            steps = event.angleDelta().y() // 120
            pg_ev = pygame.event.Event(
                pygame.MOUSEWHEEL,
                x=0, y=steps, flipped=False,
            )
            self.active_scene.handle_event(pg_ev)
        event.accept()

    def _qt_key_to_pg(self, qt_key: Qt.Key) -> Optional[int]:
        """Converte tecla Qt → constante pygame.K_*"""
        _map = {
            Qt.Key_Escape:    pygame.K_ESCAPE,
            Qt.Key_Delete:    pygame.K_DELETE,
            Qt.Key_Backspace: pygame.K_BACKSPACE,
            Qt.Key_Left:      pygame.K_LEFT,
            Qt.Key_Right:     pygame.K_RIGHT,
            Qt.Key_Up:        pygame.K_UP,
            Qt.Key_Down:      pygame.K_DOWN,
            Qt.Key_Space:     pygame.K_SPACE,
            Qt.Key_Return:    pygame.K_RETURN,
            Qt.Key_Enter:     pygame.K_KP_ENTER,
            Qt.Key_Shift:     pygame.K_LSHIFT,
            Qt.Key_Control:   pygame.K_LCTRL,
            Qt.Key_Alt:       pygame.K_LALT,
            Qt.Key_Tab:       pygame.K_TAB,
            **{getattr(Qt, f"Key_F{i}"): getattr(pygame, f"K_F{i}") for i in range(1, 13)},
        }
        if Qt.Key_A <= qt_key <= Qt.Key_Z:
            return pygame.K_a + (qt_key - Qt.Key_A)
        if Qt.Key_0 <= qt_key <= Qt.Key_9:
            return pygame.K_0 + (qt_key - Qt.Key_0)
        return _map.get(qt_key)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_F and not self._runtime_input_active():
            self.focus_camera_on_selected()
            event.accept()
            return

        if not self.active_scene:
            return

        pg_key = self._qt_key_to_pg(event.key())
        if pg_key is not None:
            if not event.isAutoRepeat():
                self._forward_runtime_input("key_down", key=self._qt_key_to_input_name(event.key()))
            mod = pygame.KMOD_NONE
            if event.modifiers() & Qt.ControlModifier:
                mod |= pygame.KMOD_CTRL
            pg_ev = pygame.event.Event(
                pygame.KEYDOWN,
                key=pg_key, mod=mod, unicode=event.text(),
            )
            self.active_scene.handle_event(pg_ev)
            # Delete e Ctrl+D devem sincronizar o modelo
            if pg_key == pygame.K_DELETE:
                self._sync_model_from_scene()
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if not self.active_scene:
            return
        pg_key = self._qt_key_to_pg(event.key())
        if pg_key is not None:
            if not event.isAutoRepeat():
                self._forward_runtime_input("key_up", key=self._qt_key_to_input_name(event.key()))
            mod = pygame.KMOD_NONE
            if event.modifiers() & Qt.ControlModifier:
                mod |= pygame.KMOD_CTRL
            pg_ev = pygame.event.Event(
                pygame.KEYUP,
                key=pg_key, mod=mod, unicode="",
            )
            self.active_scene.handle_event(pg_ev)
            event.accept()
        else:
            super().keyReleaseEvent(event)
