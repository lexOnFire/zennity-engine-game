import time
import pygame
import numpy as np
from typing import Optional
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, Slot, QPoint, QSize
from PySide6.QtGui import QPainter, QImage, QPixmap, QMouseEvent, QKeyEvent, QWheelEvent

# Imports da Engine e Cenas do Editor
from engine.core import Scene
from editor.viewmodels.scene_viewmodel import SceneViewModel


class ViewportWidget(QOpenGLWidget):
    """
    Viewport gráfica baseada em QOpenGLWidget.
    
    Renderiza o framebuffer do Pygame usando aceleração gráfica e traduz
    eventos de mouse, teclado e scroll para o sistema interno de eventos.
    Componente 'View' na arquitetura MVVM do editor (Semana 6).
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName("ViewportWidget")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        
        # Inicializa o Pygame de forma local e as fontes
        pygame.init()
        pygame.font.init()
        
        self.viewmodel: Optional[SceneViewModel] = None
        self.active_scene: Optional[Scene] = None
        
        # Framebuffer do Pygame
        self.pg_surface: Optional[pygame.Surface] = None
        self.width_pv, self.height_pv = 800, 600
        
        # Controle de tempo
        self.last_time = time.time()
        
        # Timer de atualização periódica (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)  # ~60 FPS

    def set_viewmodel(self, viewmodel: SceneViewModel) -> None:
        """Define o ViewModel e carrega a cena inicial."""
        self.viewmodel = viewmodel
        
        # Importa a cena do editor legado de forma dinâmica para carregar na Viewport
        from editor_legacy.editor_2d import Editor2DScene
        self.active_scene = Editor2DScene()
        
        # Prepara a cena
        self.active_scene.start()
        
        # Opcional: sincroniza os objetos iniciais da cena com o SceneModel do editor
        if self.viewmodel:
            # Limpa o model
            self.viewmodel._model.clear()
            # Adiciona os objetos iniciais
            for obj in self.active_scene.editable_objects:
                self.viewmodel._model.add_object(obj)
            # Sincroniza a seleção
            if self.active_scene.selected_index >= 0:
                self.viewmodel.selected_object = self.active_scene.editable_objects[self.active_scene.selected_index]
                
            # Ouve quando a seleção muda na UI externa do editor e aplica na cena da viewport
            self.viewmodel.selection_changed.connect(self.on_editor_selection_changed)

    @Slot(object)
    def on_editor_selection_changed(self, obj: Optional[object]) -> None:
        """Chamado quando a seleção externa do editor muda."""
        if not self.active_scene or not hasattr(self.active_scene, "editable_objects"):
            return
            
        if obj in self.active_scene.editable_objects:
            self.active_scene.selected_index = self.active_scene.editable_objects.index(obj)
        else:
            self.active_scene.selected_index = -1

    def initializeGL(self) -> None:
        """Inicialização básica do contexto OpenGL."""
        pass

    def resizeGL(self, w: int, h: int) -> None:
        """Chamado quando o widget é redimensionado."""
        self.width_pv = max(32, w)
        self.height_pv = max(32, h)
        # Recria o framebuffer do Pygame no novo tamanho
        self.pg_surface = pygame.Surface((self.width_pv, self.height_pv), pygame.SRCALPHA)
        
        # Se a cena tiver parâmetros de viewport, atualiza-os
        if self.active_scene:
            if hasattr(self.active_scene, "vp_w"):
                # Atualiza as margens e dimensões internas da viewport do editor 2D
                self.active_scene.vp_left = 10
                self.active_scene.vp_top = 10
                self.active_scene.vp_right = self.width_pv - 10
                self.active_scene.vp_bottom = self.height_pv - 10
                self.active_scene.vp_w = self.width_pv - 20
                self.active_scene.vp_h = self.height_pv - 20

    def paintGL(self) -> None:
        """Renderiza a imagem do Pygame usando aceleração na viewport."""
        if self.pg_surface is None or not self.active_scene:
            return
            
        # Desenha a cena no framebuffer local do Pygame
        self.active_scene.draw(self.pg_surface)
        
        # Obtém buffer bruto de pixels no formato RGBA do Pygame
        buffer = pygame.image.tostring(self.pg_surface, "RGBA")
        
        # Cria QImage a partir do buffer
        qimage = QImage(
            buffer,
            self.width_pv,
            self.height_pv,
            self.width_pv * 4,
            QImage.Format_RGBA8888
        )
        
        # Desenha a QImage no widget usando QPainter
        painter = QPainter(self)
        painter.drawImage(0, 0, qimage)
        painter.end()

    @Slot()
    def tick(self) -> None:
        """Loop lógico de frames da simulação da cena."""
        now = time.time()
        dt = min(now - self.last_time, 0.1)
        self.last_time = now
        
        if self.active_scene:
            # Repassa o estado de simulação (PLAY/STOP)
            if self.viewmodel and hasattr(self.active_scene, "playing"):
                # Para fins de demonstração, sincroniza com o botão Play da MainWindow
                pass
            
            # Roda lógica de física/updates da cena
            self.active_scene.update(dt)
            
        # Solicita redesenho
        self.update()

    # ──────────────────────────────────────────────────────────────────────────
    # Tradução de Eventos para o Pygame
    # ──────────────────────────────────────────────────────────────────────────

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
        # QWheelEvent delta
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
        # Mapeamento de teclas simples
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
            # Roda evento keyDown
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
