import time
import pygame
import numpy as np
from typing import Optional, Dict, Tuple
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Slot, QPoint, QSize
from PySide6.QtGui import QPainter, QImage, QPixmap, QMouseEvent, QKeyEvent, QWheelEvent

# Barramento de Eventos do Editor
from editor.core.event_bus import (
    EventBus, EVENT_PLAY_STATE_CHANGED, EVENT_SELECTION_CHANGED, EVENT_PROPERTY_CHANGED,
    EVENT_HIERARCHY_UPDATED
)

# Core da Engine
from engine.core import Scene
from editor.viewmodels.scene_viewmodel import SceneViewModel


class ViewportWidget(QOpenGLWidget):
    """
    Viewport gráfica baseada em QOpenGLWidget.
    
    Implementação da Semana 13 & Melhorias de Interação:
      - Suporte à tecla 'F' para focar a câmera no objeto selecionado
      - Alternância dinâmica entre visualização 2D (Ortográfica) e 3D (Perspectiva)
      - Monkey-patch de layouts 2D/3D e mouse.get_pos para sincronização e hit-test de mouse perfeitos no Qt
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportWidget")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        
        # Inicializa o Pygame localmente
        pygame.init()
        pygame.font.init()
        
        self.viewmodel: Optional[SceneViewModel] = None
        self.active_scene: Optional[Scene] = None
        self.editor_mode = "2D"  # '2D' ou '3D'
        
        # Monkey-patch para pygame.mouse.get_pos obter coordenadas locais da viewport do Qt
        self.mouse_pos_qt = (0, 0)
        pygame.mouse.get_pos = lambda: self.mouse_pos_qt
        
        # Framebuffer do Pygame
        self.pg_surface: Optional[pygame.Surface] = None
        self.width_pv, self.height_pv = 800, 600
        
        self.last_time = time.time()
        
        # Inscreve-se no EventBus para ouvir a simulação, ferramentas e modos
        EventBus.subscribe(EVENT_PLAY_STATE_CHANGED, self.on_bus_play_state_changed)
        EventBus.subscribe(EVENT_SELECTION_CHANGED, self.on_bus_selection_changed)
        EventBus.subscribe(EVENT_PROPERTY_CHANGED, self.on_bus_property_changed)
        EventBus.subscribe(EVENT_HIERARCHY_UPDATED, self.on_bus_hierarchy_updated)
        
        # Timer (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        """Conecta o ViewModel e extrai a cena inicial."""
        self.viewmodel = viewmodel
        
        from editor_legacy.editor_2d import Editor2DScene
        self.active_scene = Editor2DScene()
        self.active_scene.start()
        
        # Popula o modelo inicial a partir da cena
        if self.viewmodel:
            self.viewmodel._model.clear()
            for obj in self.active_scene.editable_objects:
                self.viewmodel._model.add_object(obj)
            if self.active_scene.selected_index >= 0:
                self.viewmodel.selected_object = self.active_scene.editable_objects[self.active_scene.selected_index]
                
        # Aplica patches iniciais de layout de tela cheia
        self._apply_qt_shims()

    def change_editor_mode(self, mode: str) -> None:
        """Alterna dinamicamente a cena da Viewport entre editor 2D e editor 3D."""
        if not self.active_scene or self.editor_mode == mode:
            return
            
        # Salva referências dos objetos da cena atual
        objs = list(self.active_scene.editable_objects) if hasattr(self.active_scene, "editable_objects") else []
        selected_obj = self.viewmodel.selected_object if self.viewmodel else None
        
        self.editor_mode = mode
        
        # Instancia a nova cena correspondente
        if mode == "2D":
            from editor_legacy.editor_2d import Editor2DScene
            self.active_scene = Editor2DScene()
        elif mode == "3D":
            from editor_legacy.scene import EditorScene
            self.active_scene = EditorScene()
            
        self.active_scene.start()
        
        # Transfere os objetos salvos
        if hasattr(self.active_scene, "editable_objects"):
            self.active_scene.editable_objects.clear()
            self.active_scene.game_objects.clear()
            for obj in objs:
                self.active_scene.add_game_object(obj)
                self.active_scene.editable_objects.append(obj)
                
        # Sincroniza a seleção
        if selected_obj in objs:
            self.active_scene.selected_index = objs.index(selected_obj)
        else:
            self.active_scene.selected_index = -1
            
        # Reaplica shims de tamanho e layout
        self._apply_qt_shims()
        self.resizeGL(self.width(), self.height())
        self.update()

    def _apply_qt_shims(self) -> None:
        """Aplica monkey-patches dinâmicos na cena ativa para fazê-la rodar perfeitamente no Qt sem painéis legados duplicados."""
        if not self.active_scene:
            return
            
        w, h = self.width_pv, self.height_pv
        
        # ── 1. Monkey-patch do Layout e render do Editor 2D ──────────────────
        if hasattr(self.active_scene, "_layout"):
            def qt_layout_2d():
                return {
                    "sw": w, "sh": h,
                    "vp_left": 0,
                    "vp_top": 0,
                    "vp_right": w,
                    "vp_bottom": h,
                    "vp_w": w,
                    "vp_h": h,
                    "panel_left_w": 0,
                    "panel_right_x": w,
                    "panel_right_w": 0,
                    "status_y": h
                }
            self.active_scene._layout = qt_layout_2d
            
            # Sobrescreve o draw para renderizar apenas a viewport
            def qt_draw_2d(screen):
                lay = self.active_scene._layout()
                screen.fill((30, 31, 38))  # Fundo escuro do tema
                self.active_scene._draw_viewport(screen, lay)
            self.active_scene.draw = qt_draw_2d
            
        # ── 2. Monkey-patch do Layout e render do Editor 3D ──────────────────
        if hasattr(self.active_scene, "_lay"):
            lay = self.active_scene._lay
            lay.left_panel_rect = pygame.Rect(0, 0, 0, 0)
            lay.right_panel_rect = pygame.Rect(w, 0, 0, 0)
            lay.top_bar_rect = pygame.Rect(0, 0, w, 0)
            lay.status_bar_rect = pygame.Rect(0, h, w, 0)
            lay.viewport_rect = pygame.Rect(0, 0, w, h)
            lay.viewport_edit_rect = pygame.Rect(0, 0, w, h)
            lay.viewport_game_rect = pygame.Rect(0, 0, w, h)
            lay.right_x = w
            lay.viewport_y = 0
            lay.viewport_h = h
            lay.viewport_w = w
            
            # Trava a atualização de layout
            lay.update = lambda sw, sh: None
            
            # Sobrescreve o draw para ocultar modais legados e barras laterais no Qt
            def qt_draw_3d(screen):
                self.active_scene.showing_welcome = False
                self.active_scene.showing_templates = False
                self.active_scene.showing_help_modal = False
                self.active_scene.code_editor.is_open = False
                
                # Sincroniza a câmera 3D com a viewport cheia do widget
                self.active_scene.camera_comp.viewport_x = lay.viewport_rect.x
                self.active_scene.camera_comp.viewport_y = lay.viewport_rect.y
                self.active_scene.camera_comp.viewport_width = lay.viewport_rect.width
                self.active_scene.camera_comp.viewport_height = lay.viewport_rect.height
                self.active_scene.camera_comp.update(0.0)
                
                from engine.graphics.renderer3d import Camera3D, MeshRenderer3D
                Camera3D.main = self.active_scene.camera_comp
                
                pygame.draw.rect(screen, (30, 31, 38), lay.viewport_rect)
                self.active_scene._draw_floor_grid(screen)
                
                # Renderiza e destaca objeto ativo
                for go in self.active_scene.game_objects:
                    go.draw(screen)
                    if self.active_scene.selected_index >= 0 and go == self.active_scene.editable_objects[self.active_scene.selected_index]:
                        r = go.get_component(MeshRenderer3D)
                        if r:
                            ow, oc, olw = r.wireframe, r.color, r.line_width
                            r.wireframe, r.color, r.line_width = True, (64, 156, 255), 3  # Azul Destaque
                            r.draw(screen)
                            r.wireframe, r.color, r.line_width = ow, oc, olw
                self.active_scene._draw_gizmo(screen)
                
            self.active_scene.draw = qt_draw_3d

    def focus_camera_on_selected(self) -> None:
        """Foca suave ou instantaneamente a câmera no objeto selecionado na viewport."""
        if not self.active_scene or not self.viewmodel or not self.viewmodel.selected_object:
            return
            
        obj = self.viewmodel.selected_object
        
        # Modo 2D: centraliza câmera
        if hasattr(self.active_scene, "cam_x"):
            self.active_scene.cam_x = obj.transform.position[0]
            self.active_scene.cam_y = obj.transform.position[1]
            self.active_scene.zoom = 1.0  # Reseta o zoom para ver o objeto
            
        # Modo 3D: centraliza câmera orbital
        elif hasattr(self.active_scene, "camera_controller") and self.active_scene.camera_controller:
            ctrl = self.active_scene.camera_controller
            ctrl.target = obj.transform.position.copy()
            ctrl.distance = 5.0
            
        self.update()

    def initializeGL(self) -> None:
        pass

    def resizeGL(self, w: int, h: int) -> None:
        self.width_pv = max(32, w)
        self.height_pv = max(32, h)
        self.pg_surface = pygame.Surface((self.width_pv, self.height_pv), pygame.SRCALPHA)
        
        # Reaplica o patch de layout no redimensionamento da janela do Qt
        self._apply_qt_shims()
        
        if self.active_scene and hasattr(self.active_scene, "vp_w"):
            self.active_scene.vp_left = 0
            self.active_scene.vp_top = 0
            self.active_scene.vp_right = self.width_pv
            self.active_scene.vp_bottom = self.height_pv
            self.active_scene.vp_w = self.width_pv
            self.active_scene.vp_h = self.height_pv

    def paintGL(self) -> None:
        if self.pg_surface is None or not self.active_scene:
            return
            
        self.active_scene.draw(self.pg_surface)
        buffer = pygame.image.tostring(self.pg_surface, "RGBA")
        
        qimage = QImage(
            buffer,
            self.width_pv,
            self.height_pv,
            self.width_pv * 4,
            QImage.Format_RGBA8888
        )
        
        painter = QPainter(self)
        painter.drawImage(0, 0, qimage)
        painter.end()

    @Slot()
    def tick(self) -> None:
        now = time.time()
        dt = min(now - self.last_time, 0.1)
        self.last_time = now
        
        if self.active_scene:
            self.active_scene.update(dt)
            
            # Executa os scripts de comportamento no PLAY
            if getattr(self.active_scene, "playing", False):
                from editor_legacy.script_manager import ScriptManager
                ScriptManager.update_all(self.active_scene.editable_objects, dt)
            
            # ── Binding Bidirecional: Sincronização do Arrasto com o Inspector ──
            is_dragging = False
            # Cena 3D: arrastando o gizmo
            if getattr(self.active_scene, "is_dragging_gizmo", False):
                is_dragging = True
            # Cena 2D: arrastando o corpo do objeto ou arrastando os handles de escala
            elif getattr(self.active_scene, "_dragging_target", None) is not None:
                is_dragging = True
            else:
                scale_handle = getattr(self.active_scene, "_scale_handle_idx", -1)
                if scale_handle is not None and scale_handle >= 0:
                    is_dragging = True
                
            if is_dragging and self.viewmodel and self.viewmodel.selected_object:
                # Dispara notificação genérica de mudança para forçar o redesenho dos spinboxes no Inspector
                EventBus.emit(
                    EVENT_PROPERTY_CHANGED,
                    component_name="Transform",
                    property_name="position",
                    value=None
                )
            
        self.update()

    # ── Handlers do EventBus ──────────────────────────────────────────────────

    def on_bus_play_state_changed(self, state: str) -> None:
        if not self.active_scene or not hasattr(self.active_scene, "playing"):
            return
            
        from editor_legacy.script_manager import ScriptManager
            
        if state == "play" and not self.active_scene.playing:
            self.active_scene.toggle_play()
            
            # Carrega e inicializa os scripts associados
            for obj in self.active_scene.editable_objects:
                if getattr(obj, "script_path", ""):
                    ScriptManager.load(obj)
        elif state == "stop" and self.active_scene.playing:
            self.active_scene.toggle_play()
            
            # Remove referências temporárias dos scripts
            for obj in self.active_scene.editable_objects:
                ScriptManager.unload(obj)

    def on_bus_selection_changed(self, obj: Optional[object]) -> None:
        if not self.active_scene or not hasattr(self.active_scene, "editable_objects"):
            return
            
        if obj in self.active_scene.editable_objects:
            self.active_scene.selected_index = self.active_scene.editable_objects.index(obj)
        else:
            self.active_scene.selected_index = -1

    def on_bus_hierarchy_updated(self) -> None:
        """Sincroniza os objetos da cena do Pygame com o modelo sempre que a hierarquia mudar."""
        if not self.active_scene or not self.viewmodel:
            return
            
        objs = self.viewmodel.get_root_objects()
        
        # Sincroniza as listas internas da cena ativa
        if hasattr(self.active_scene, "editable_objects"):
            self.active_scene.editable_objects.clear()
            self.active_scene.game_objects.clear()
            for obj in objs:
                self.active_scene.add_game_object(obj)
                self.active_scene.editable_objects.append(obj)
                
        # Sincroniza a seleção na cena ativa
        selected_obj = self.viewmodel.selected_object
        if selected_obj in objs:
            self.active_scene.selected_index = objs.index(selected_obj)
        else:
            self.active_scene.selected_index = -1
            
        self.update()

    def on_bus_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        if component_name == "Editor" and property_name == "tool_mode" and self.active_scene:
            tool_name = str(value)
            if tool_name == "select":
                pass
            elif tool_name == "move":
                if hasattr(self.active_scene, "gizmo_mode"):
                    self.active_scene.gizmo_mode = "translate"
            elif tool_name == "rotate":
                if hasattr(self.active_scene, "gizmo_mode"):
                    self.active_scene.gizmo_mode = "rotate"
            elif tool_name == "scale":
                if hasattr(self.active_scene, "gizmo_mode"):
                    self.active_scene.gizmo_mode = "scale"
        elif component_name == "Editor" and property_name == "camera_mode":
            self.change_editor_mode(str(value))

    # ── Mapeamento de Eventos ──────────────────────────────────────────────────

    def translate_mouse_button(self, qt_btn: Qt.MouseButton) -> int:
        if qt_btn == Qt.LeftButton:   return 1
        if qt_btn == Qt.MiddleButton: return 2
        if qt_btn == Qt.RightButton:  return 3
        return 0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self.active_scene:
            return
        self.mouse_pos_qt = (event.x(), event.y())
        btn = self.translate_mouse_button(event.button())
        pg_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=self.mouse_pos_qt,
            button=btn
        )
        self.active_scene.handle_event(pg_event)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self.active_scene:
            return
        self.mouse_pos_qt = (event.x(), event.y())
        btn = self.translate_mouse_button(event.button())
        pg_event = pygame.event.Event(
            pygame.MOUSEBUTTONUP,
            pos=self.mouse_pos_qt,
            button=btn
        )
        self.active_scene.handle_event(pg_event)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.active_scene:
            return
        self.mouse_pos_qt = (event.x(), event.y())
        pg_event = pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=self.mouse_pos_qt,
            buttons=(
                1 if event.buttons() & Qt.LeftButton else 0,
                1 if event.buttons() & Qt.MiddleButton else 0,
                1 if event.buttons() & Qt.RightButton else 0
            ),
            rel=(0, 0)
        )
        self.active_scene.handle_event(pg_event)
        event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self.active_scene:
            return
        y_steps = event.angleDelta().y() // 120
        pg_event = pygame.event.Event(
            pygame.MOUSEWHEEL,
            x=0,
            y=y_steps,
            flipped=False
        )
        self.active_scene.handle_event(pg_event)
        event.accept()

    def get_pygame_key(self, qt_key: Qt.Key) -> Optional[int]:
        """Traduz dinamicamente códigos de teclas do Qt para códigos correspondentes do Pygame."""
        key_map = {
            Qt.Key_Escape: pygame.K_ESCAPE,
            Qt.Key_Delete: pygame.K_DELETE,
            Qt.Key_Backspace: pygame.K_BACKSPACE,
            Qt.Key_Left: pygame.K_LEFT,
            Qt.Key_Right: pygame.K_RIGHT,
            Qt.Key_Up: pygame.K_UP,
            Qt.Key_Down: pygame.K_DOWN,
            Qt.Key_Space: pygame.K_SPACE,
            Qt.Key_Return: pygame.K_RETURN,
            Qt.Key_Enter: pygame.K_KP_ENTER,
            Qt.Key_Shift: pygame.K_LSHIFT,
            Qt.Key_Control: pygame.K_LCTRL,
            Qt.Key_Alt: pygame.K_LALT,
            Qt.Key_Tab: pygame.K_TAB,
            Qt.Key_F1: pygame.K_F1,
            Qt.Key_F2: pygame.K_F2,
            Qt.Key_F3: pygame.K_F3,
            Qt.Key_F4: pygame.K_F4,
            Qt.Key_F5: pygame.K_F5,
            Qt.Key_F6: pygame.K_F6,
            Qt.Key_F7: pygame.K_F7,
            Qt.Key_F8: pygame.K_F8,
            Qt.Key_F9: pygame.K_F9,
            Qt.Key_F10: pygame.K_F10,
            Qt.Key_F11: pygame.K_F11,
            Qt.Key_F12: pygame.K_F12,
        }
        
        # Mapeia dinamicamente letras A-Z (Pygame K_a=97, Qt Key_A=65)
        if Qt.Key_A <= qt_key <= Qt.Key_Z:
            return qt_key - Qt.Key_A + pygame.K_a
        # Mapeia dinamicamente números 0-9
        elif Qt.Key_0 <= qt_key <= Qt.Key_9:
            return qt_key - Qt.Key_0 + pygame.K_0
            
        return key_map.get(qt_key)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Atalho de Foco ('F')
        if event.key() == Qt.Key_F:
            self.focus_camera_on_selected()
            event.accept()
            return
            
        if not self.active_scene:
            return
            
        pg_key = self.get_pygame_key(event.key())
        if pg_key is not None:
            mod = pygame.KMOD_NONE
            if event.modifiers() & Qt.ControlModifier:
                mod |= pygame.KMOD_CTRL
            pg_event = pygame.event.Event(
                pygame.KEYDOWN,
                key=pg_key,
                mod=mod,
                unicode=event.text()
            )
            self.active_scene.handle_event(pg_event)
            event.accept()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if not self.active_scene:
            return
            
        pg_key = self.get_pygame_key(event.key())
        if pg_key is not None:
            mod = pygame.KMOD_NONE
            if event.modifiers() & Qt.ControlModifier:
                mod |= pygame.KMOD_CTRL
            pg_event = pygame.event.Event(
                pygame.KEYUP,
                key=pg_key,
                mod=mod,
                unicode=""
            )
            self.active_scene.handle_event(pg_event)
            event.accept()
        else:
            super().keyReleaseEvent(event)
