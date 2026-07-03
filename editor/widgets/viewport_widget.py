import time
import pygame
import numpy as np
from typing import Optional
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Slot, QPoint, QSize
from PySide6.QtGui import QPainter, QImage, QPixmap, QMouseEvent, QKeyEvent, QWheelEvent

# Barramento de Eventos do Editor
from editor.core.event_bus import (
    EventBus, EVENT_PLAY_STATE_CHANGED, EVENT_SELECTION_CHANGED, EVENT_PROPERTY_CHANGED
)

# Core da Engine
from engine.core import Scene
from editor.viewmodels.scene_viewmodel import SceneViewModel


class ViewportWidget(QOpenGLWidget):
    """
    Viewport gráfica baseada em QOpenGLWidget.
    
    Implementação da Semana 9:
      - Sincronização dos Gizmos de Transformação (Mover, Rotacionar, Escalar)
      - Propagação bidirecional de arrasto de gizmo/handles para o Inspector
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
        
        # Framebuffer do Pygame
        self.pg_surface: Optional[pygame.Surface] = None
        self.width_pv, self.height_pv = 800, 600
        
        self.last_time = time.time()
        
        # Inscreve-se no EventBus para ouvir a simulação e ferramentas
        EventBus.subscribe(EVENT_PLAY_STATE_CHANGED, self.on_bus_play_state_changed)
        EventBus.subscribe(EVENT_SELECTION_CHANGED, self.on_bus_selection_changed)
        EventBus.subscribe(EVENT_PROPERTY_CHANGED, self.on_bus_property_changed)
        
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

    def initializeGL(self) -> None:
        pass

    def resizeGL(self, w: int, h: int) -> None:
        self.width_pv = max(32, w)
        self.height_pv = max(32, h)
        self.pg_surface = pygame.Surface((self.width_pv, self.height_pv), pygame.SRCALPHA)
        
        if self.active_scene and hasattr(self.active_scene, "vp_w"):
            self.active_scene.vp_left = 10
            self.active_scene.vp_top = 10
            self.active_scene.vp_right = self.width_pv - 10
            self.active_scene.vp_bottom = self.height_pv - 10
            self.active_scene.vp_w = self.width_pv - 20
            self.active_scene.vp_h = self.height_pv - 20

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
            
        if state == "play" and not self.active_scene.playing:
            self.active_scene.toggle_play()
        elif state == "stop" and self.active_scene.playing:
            self.active_scene.toggle_play()

    def on_bus_selection_changed(self, obj: Optional[object]) -> None:
        if not self.active_scene or not hasattr(self.active_scene, "editable_objects"):
            return
            
        if obj in self.active_scene.editable_objects:
            self.active_scene.selected_index = self.active_scene.editable_objects.index(obj)
        else:
            self.active_scene.selected_index = -1

    def on_bus_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        """Ouve alterações de configurações e ferramentas na interface do editor."""
        if component_name == "Editor" and property_name == "tool_mode" and self.active_scene:
            tool_name = str(value)
            # Sincroniza a ferramenta de transform ativa com os gizmos da cena Pygame
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

    # ── Mapeamento de Eventos ──────────────────────────────────────────────────

    def translate_mouse_button(self, qt_btn: Qt.MouseButton) -> int:
        if qt_btn == Qt.LeftButton:   return 1
        if qt_btn == Qt.MiddleButton: return 2
        if qt_btn == Qt.RightButton:  return 3
        return 0

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self.active_scene:
            return
        btn = self.translate_mouse_button(event.button())
        pg_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            pos=(event.x(), event.y()),
            button=btn
        )
        self.active_scene.handle_event(pg_event)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self.active_scene:
            return
        btn = self.translate_mouse_button(event.button())
        pg_event = pygame.event.Event(
            pygame.MOUSEBUTTONUP,
            pos=(event.x(), event.y()),
            button=btn
        )
        self.active_scene.handle_event(pg_event)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.active_scene:
            return
        pg_event = pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=(event.x(), event.y()),
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

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if not self.active_scene:
            return
        key_map = {
            Qt.Key_Escape: pygame.K_ESCAPE,
            Qt.Key_Delete: pygame.K_DELETE,
            Qt.Key_Backspace: pygame.K_BACKSPACE,
            Qt.Key_Left: pygame.K_LEFT,
            Qt.Key_Right: pygame.K_RIGHT,
            Qt.Key_Up: pygame.K_UP,
            Qt.Key_Down: pygame.K_DOWN,
            Qt.Key_F1: pygame.K_F1,
            Qt.Key_Z: pygame.K_z,
            Qt.Key_Y: pygame.K_y,
            Qt.Key_D: pygame.K_d
        }
        pg_key = key_map.get(event.key())
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
