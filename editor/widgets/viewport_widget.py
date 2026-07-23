"""
editor/widgets/viewport_widget.py
==================================
Widget de Viewport gráfica PySide6/Pygame.

Arquitetura:
  - O SceneModel/SceneViewModel define a identidade canônica dos GameObjects no editor.
  - A viewport renderiza e interage com a cena ativa, mas delega criação/remoção/duplicação ao ViewModel.
  - A seleção é sincronizada por UUID para evitar instâncias duplicadas entre painéis.
  - Monkey-patches silenciam os painéis legados do Pygame (toolbar, painel esq/dir, statusbar).
"""

import time
import pygame
import numpy as np
from typing import Optional, List
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QPainter, QImage, QMouseEvent, QKeyEvent, QWheelEvent

from editor.core.event_bus import (
    EventBus,
    EVENT_PLAY_STATE_CHANGED,
    EVENT_SELECTION_CHANGED,
    EVENT_PROPERTY_CHANGED,
    EVENT_HIERARCHY_UPDATED,
)
from editor.render.frame_invalidation import FrameInvalidation, FrameInvalidationStats
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.widgets.viewport_qt_events import ViewportQtEventsMixin


class ViewportWidget(ViewportQtEventsMixin, QOpenGLWidget):
    """
    Viewport gráfica embarcando o loop do Pygame dentro de um QOpenGLWidget.

    Regras de sincronização:
      1. O SceneViewModel é a porta de entrada para criar, deletar e duplicar objetos no editor.
      2. A cena ativa espelha e renderiza os GameObjects canônicos do editor.
      3. A seleção entre viewport e painéis é sincronizada por UUID.
      4. Os painéis legados do Pygame são silenciados via monkey-patch no draw.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportWidget")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

        pygame.init()
        pygame.font.init()

        self.viewmodel: Optional[SceneViewModel] = None
        self.active_scene = None
        self._selection_scene = None
        self._last_scene_selected_index: int | None = None
        self.editor_mode: str = "2D"

        self._qt_mouse_pos: tuple = (0, 0)
        pygame.mouse.get_pos = lambda: self._qt_mouse_pos

        self.pg_surface: Optional[pygame.Surface] = None
        self._vp_w: int = 800
        self._vp_h: int = 600

        self._last_time: float = time.time()
        self._frame_invalidation = FrameInvalidation()

        EventBus.subscribe(EVENT_PLAY_STATE_CHANGED,  self._on_play_state_changed)
        EventBus.subscribe(EVENT_SELECTION_CHANGED,   self._on_selection_changed)
        EventBus.subscribe(EVENT_PROPERTY_CHANGED,    self._on_property_changed)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def request_render(self, reason: str = "unspecified") -> bool:
        """Schedule one Qt repaint, coalescing duplicate invalidations."""
        should_schedule = self._frame_invalidation.invalidate(reason)
        if should_schedule:
            self.update()
        return should_schedule

    def render_stats(self) -> FrameInvalidationStats:
        """Expose repaint counters for the editor profiler and tests."""
        return self._frame_invalidation.snapshot()

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        """
        Conecta o ViewModel e inicializa a cena 2D padrão.
        Chamado pela MainWindow após criar os docks.
        """
        self.viewmodel = viewmodel

        from editor_legacy.editor_2d import Editor2DScene
        self.active_scene = Editor2DScene()
        self.active_scene.start()

        self._apply_qt_shims()
        self._sync_scene_from_model()

    # ──────────────────────────────────────────────────────────────────────────
    # Sincronização Modelo ↔ Cena
    # ──────────────────────────────────────────────────────────────────────────

    def _sync_scene_from_model(self) -> None:
        """
        Reespelha a cena ativa a partir do SceneModel canônico do editor.
        Deve ser chamado após criação, deleção, duplicação ou troca de modo.
        """
        if not self.viewmodel or not self.active_scene:
            return

        root_objects = list(self.viewmodel.get_root_objects())

        existing_objects = list(
            getattr(
                self.active_scene,
                "editable_objects",
                getattr(self.active_scene, "game_objects", []),
            )
        )

        for obj in existing_objects:
            if hasattr(self.active_scene, "_remove_go"):
                self.active_scene._remove_go(obj)
            else:
                for component in list(getattr(obj, "components", [])):
                    destroy = getattr(component, "destroy", None)
                    if callable(destroy):
                        destroy()

                if obj in getattr(self.active_scene, "game_objects", []):
                    self.active_scene.game_objects.remove(obj)

                obj.scene = None

        if hasattr(self.active_scene, "editable_objects"):
            self.active_scene.editable_objects.clear()

        if hasattr(self.active_scene, "game_objects"):
            self.active_scene.game_objects.clear()

        for obj in root_objects:
            if hasattr(self.active_scene, "_add_go"):
                self.active_scene._add_go(obj)
            if hasattr(self.active_scene, "game_objects") and obj not in self.active_scene.game_objects:
                self.active_scene.game_objects.append(obj)
            if hasattr(self.active_scene, "editable_objects") and obj not in self.active_scene.editable_objects:
                self.active_scene.editable_objects.append(obj)

        selected_id = self.viewmodel.selected_id
        objs = getattr(self.active_scene, "editable_objects", [])
        self.active_scene.selected_index = -1
        if selected_id:
            for i, obj in enumerate(objs):
                if obj.id == selected_id:
                    self.active_scene.selected_index = i
                    break
        self._selection_scene = self.active_scene
        self._last_scene_selected_index = self.active_scene.selected_index

        self.request_render("scene-sync")

    def create_object(self, shape_type: str) -> None:
        """
        Ponto de entrada único para criação de objetos via menu Criar.
        Delega para o SceneViewModel e depois espelha a cena ativa.
        """
        if not self.viewmodel:
            return
        self.viewmodel.create_object(shape_type)
        self._sync_scene_from_model()

    def delete_selected_object(self) -> None:
        """Deleta o objeto selecionado via SceneViewModel."""
        if not self.viewmodel:
            return
        self.viewmodel.delete_selected()
        self._sync_scene_from_model()
        self.viewmodel.hierarchy_updated.emit()

    def selected_object(self):
        """Retorna o objeto atualmente selecionado, compatibilidade com testes e API antiga."""
        selected = self.viewmodel.selected_object if self.viewmodel else None
        self._sync_scene_selection(selected)
        return selected

    def duplicate_selected_object(self) -> None:
        """Duplica o objeto selecionado via SceneViewModel."""
        if not self.viewmodel:
            return
        self.viewmodel.duplicate_selected()
        self._sync_scene_from_model()

    # ──────────────────────────────────────────────────────────────────────────
    # Alternância de Modo 2D/3D
    # ──────────────────────────────────────────────────────────────────────────

    def change_editor_mode(self, mode: str) -> None:
        """Troca a cena ativa entre editor 2D e 3D preservando os objetos."""
        if self.editor_mode == mode or not self.active_scene:
            return

        self.editor_mode = mode

        if mode == "2D":
            from editor_legacy.editor_2d import Editor2DScene
            self.active_scene = Editor2DScene()
        else:
            from editor_legacy.scene import EditorScene
            self.active_scene = EditorScene()

        self.active_scene.start()
        self._apply_qt_shims()
        self.resizeGL(self.width(), self.height())
        self._sync_scene_from_model()
        self.request_render("editor-mode")

    # ──────────────────────────────────────────────────────────────────────────
    # Qt Shims — silencia painéis legados do Pygame
    # ──────────────────────────────────────────────────────────────────────────

    def _apply_qt_shims(self) -> None:
        if not self.active_scene:
            return

        widget = self
        scene = self.active_scene

        if hasattr(scene, "_layout") and not hasattr(scene, "_lay"):

            def _qt_layout_2d(_w=widget):
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

            for btn in getattr(scene, "_all_toolbar_btns", []):
                btn.rect.y = -9999

            def _qt_draw_2d(screen, _scene=scene):
                lay = _scene._layout()
                screen.fill((28, 29, 36))
                _scene._draw_viewport(screen, lay)
            scene.draw = _qt_draw_2d

            if not hasattr(scene.handle_event, "__wrapped__"):
                _orig_handle = scene.handle_event

                def _qt_handle_event_2d(event, _scene=scene, _orig=_orig_handle):
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
                        if _scene._in_viewport(mx, my, lay):
                            _orig(event)
                        return
                    _orig(event)

                _qt_handle_event_2d.__wrapped__ = _orig_handle
                scene.handle_event = _qt_handle_event_2d

        elif hasattr(scene, "_lay"):
            self._apply_qt_3d_shim(scene)

    def _apply_qt_3d_shim(self, scene) -> None:
        widget = self

        def _sync_3d_layout(_w=widget, _lay=scene._lay):
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

        _sync_3d_layout()
        scene._lay.update = lambda sw, sh: None

        def _qt_draw_3d(screen, _scene=scene):
            _sync_3d_layout()

            _scene.showing_welcome = False
            _scene.showing_templates = False
            _scene.showing_help_modal = False
            if hasattr(_scene, "code_editor"):
                _scene.code_editor.is_open = False

            lay = _scene._lay
            cam = _scene.camera_comp
            cam.viewport_x = 0
            cam.viewport_y = 0
            cam.viewport_width = lay.viewport_rect.width
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
                    renderer = go.get_component(MeshRenderer3D)
                    if renderer:
                        old_style = renderer.wireframe, renderer.color, renderer.line_width
                        renderer.wireframe, renderer.color, renderer.line_width = (
                            True, (80, 160, 255), 3
                        )
                        renderer.draw(screen)
                        renderer.wireframe, renderer.color, renderer.line_width = old_style

            _scene._draw_gizmo(screen)

        scene.draw = _qt_draw_3d

    def focus_camera_on_selected(self) -> None:
        if not self.active_scene or not self.viewmodel:
            return
        obj = self.viewmodel.selected_object
        if not obj:
            return

        if hasattr(self.active_scene, "camera") and hasattr(self.active_scene, "cam_obj"):
            from engine.graphics.camera2d import Camera2D
            if Camera2D.main:
                Camera2D.main.transform.position[0] = obj.transform.position[0]
                Camera2D.main.transform.position[1] = obj.transform.position[1]
        elif hasattr(self.active_scene, "camera_comp"):
            ctrl = getattr(self.active_scene, "camera_controller", None)
            if ctrl:
                ctrl.target = obj.transform.position.copy()
                ctrl.distance = 5.0

        self.request_render("camera-focus")

    def initializeGL(self) -> None:
        pass

    def resizeGL(self, w: int, h: int) -> None:
        self._vp_w = max(32, w)
        self._vp_h = max(32, h)
        self.pg_surface = pygame.Surface((self._vp_w, self._vp_h), pygame.SRCALPHA)
        self._apply_qt_shims()
        self._frame_invalidation.invalidate("resize")

    def paintGL(self) -> None:
        if not self.pg_surface or not self.active_scene:
            return

        self._frame_invalidation.consume()

        self.active_scene.draw(self.pg_surface)

        raw = pygame.image.tostring(self.pg_surface, "RGBA")
        img = QImage(raw, self._vp_w, self._vp_h,
                     self._vp_w * 4, QImage.Format_RGBA8888)

        p = QPainter(self)
        p.drawImage(0, 0, img)
        if self.active_scene and getattr(self.active_scene, "playing", False):
            from PySide6.QtGui import QPen, QColor, QFont
            import math
            # Smooth neon pulsing glow
            opacity = int(120 + 70 * math.sin(time.time() * 5.0))
            # Draw ciano neon border
            pen = QPen(QColor(0, 173, 181, opacity), 3)
            p.setPen(pen)
            p.drawRect(1, 1, self.width() - 2, self.height() - 2)

            # Draw 'PLAY MODE ACTIVE' overlay text
            p.setFont(QFont("Segoe UI", 9, QFont.Bold))
            p.setPen(QColor(0, 173, 181, 220))
            p.drawText(self.width() - 130, 24, "PLAY MODE ACTIVE")
        p.end()

    @Slot()
    def _tick(self) -> None:
        now = time.time()
        dt = min(now - self._last_time, 0.1)
        self._last_time = now

        if self.active_scene:
            self.active_scene.update(dt)
            self._sync_selection_to_model()

        if bool(getattr(self.active_scene, "playing", False)):
            self.request_render("play-mode")
        else:
            self._frame_invalidation.record_idle_tick()

    def _sync_selection_to_model(self) -> None:
        """Propaga a mudança de selected_index da cena para o ViewModel por UUID."""
        if not self.viewmodel or not self.active_scene:
            return

        idx = getattr(self.active_scene, "selected_index", -1)
        if self._selection_scene is self.active_scene and idx == self._last_scene_selected_index:
            return
        self._selection_scene = self.active_scene
        self._last_scene_selected_index = idx
        objs = getattr(self.active_scene, "editable_objects", [])
        sel = objs[idx] if 0 <= idx < len(objs) else None

        current_id = self.viewmodel.selected_id
        new_id = sel.id if sel else None
        if current_id != new_id:
            self.viewmodel.selected_object = sel

    def _on_play_state_changed(self, state: str) -> None:
        if not self.active_scene or not hasattr(self.active_scene, "playing"):
            return

        if state == "play" and not self.active_scene.playing:
            self.active_scene.toggle_play()
        elif state in ("stop", "pause") and self.active_scene.playing:
            self.active_scene.toggle_play()
        self.request_render("play-state")

    def _on_selection_changed(self, obj) -> None:
        """Propaga seleção vinda do Outliner → cena ativa por UUID."""
        self._sync_scene_selection(obj)
        self.request_render("selection")

    def _sync_scene_selection(self, obj) -> None:
        """Mantém o índice legado alinhado à seleção canônica do ViewModel."""
        if not self.active_scene:
            return
        objs = getattr(self.active_scene, "editable_objects", [])
        selected_id = obj.id if obj else None
        self.active_scene.selected_index = -1
        if selected_id:
            for i, candidate in enumerate(objs):
                if candidate.id == selected_id:
                    self.active_scene.selected_index = i
                    break
        self._selection_scene = self.active_scene
        self._last_scene_selected_index = self.active_scene.selected_index

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
        self.request_render("property")


