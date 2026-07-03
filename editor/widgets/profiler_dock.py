import os
import time
import pygame
from collections import deque
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QPolygonF
from PySide6.QtCore import QPointF


class PerformanceChartWidget(QWidget):
    """
    Widget de desenho customizado para exibir o gráfico de histórico de FPS.
    Utiliza QPainter para renderizar o traçado de forma ultra performática.
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.history = deque(maxlen=80)
        # Preenche com zeros iniciais
        for _ in range(80):
            self.history.append(0.0)
            
        self.setMinimumHeight(120)
        self.setStyleSheet("background-color: #111217; border-radius: 4px;")

    def add_sample(self, value: float) -> None:
        self.history.append(value)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Desenha o fundo escuro
        painter.setBrush(QBrush(QColor("#111217")))
        painter.setPen(QPen(QColor("#323846"), 1))
        painter.drawRoundedRect(0, 0, w, h, 6, 6)
        
        # Desenha linhas horizontais de grade de referência (FPS 30 e 60)
        painter.setPen(QPen(QColor("#242732"), 1, Qt.DashLine))
        
        # Linha 60 FPS
        y_60 = h - (60.0 / 100.0) * h
        painter.drawLine(0, y_60, w, y_60)
        painter.drawText(6, y_60 - 3, "60 FPS")
        
        # Linha 30 FPS
        y_30 = h - (30.0 / 100.0) * h
        painter.drawLine(0, y_30, w, y_30)
        painter.drawText(6, y_30 - 3, "30 FPS")
        
        # Desenha o traçado do gráfico
        samples = list(self.history)
        n = len(samples)
        if n < 2:
            painter.end()
            return
            
        points = []
        dx = w / (n - 1)
        
        for i, val in enumerate(samples):
            # Clampa o valor de FPS entre 0 e 100 para fins de escala no gráfico
            clamped_val = max(0.0, min(100.0, val))
            # Converte valor para coordenadas Y da tela
            py = h - (clamped_val / 100.0) * h
            px = i * dx
            points.append(QPointF(px, py))
            
        # Desenha a área preenchida sob a linha (efeito gradiente/translúcido)
        poly = QPolygonF(points)
        poly.append(QPointF(w, h))
        poly.append(QPointF(0, h))
        
        painter.setBrush(QBrush(QColor(93, 176, 255, 40)))  # Azul mais brilhante e translúcido
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(poly)
        
        # Desenha a linha de contorno
        pen = QPen(QColor("#5db0ff"), 2, Qt.SolidLine)
        painter.setPen(pen)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i+1])
            
        painter.end()


class ProfilerDock(QDockWidget):
    """
    Painel acoplável do Profiler de Performance e Estatísticas de Física.
    Componente 'View' na arquitetura MVVM do editor (Semana 15).
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Profiler & Performance", parent)
        self.setObjectName("ProfilerDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # 1. Painel de Métricas Rápidas
        metrics = QWidget()
        m_layout = QHBoxLayout(metrics)
        m_layout.setContentsMargins(2, 2, 2, 2)
        m_layout.setSpacing(16)
        
        self.lbl_fps = QLabel("FPS: --")
        self.lbl_frame_time = QLabel("Frame Time: -- ms")
        self.lbl_memory = QLabel("Memória: -- MB")
        self.lbl_physics = QLabel("Física: 0 corpos / 0 colisores")
        
        for lbl in (self.lbl_fps, self.lbl_frame_time, self.lbl_memory, self.lbl_physics):
            lbl.setStyleSheet("color: #cfd4de; font-family: 'JetBrains Mono', 'Cascadia Code', monospace; font-size: 11px; font-weight: 600;")
            m_layout.addWidget(lbl)
            
        m_layout.addStretch()
        layout.addWidget(metrics)
        
        # 2. Gráfico de histórico de FPS
        self.chart = PerformanceChartWidget(self)
        layout.addWidget(self.chart)
        
        self.setWidget(content)
        
        # Timer de amostragem periódica (100ms)
        self.sample_timer = QTimer(self)
        self.sample_timer.timeout.connect(self.sample_metrics)
        self.sample_timer.start(100)

    @Slot()
    def sample_metrics(self) -> None:
        """Coleta estatísticas de desempenho reais e atualiza o gráfico."""
        win = self.window()
        if not win or not hasattr(win, "viewport") or not win.viewport.active_scene:
            return
            
        viewport = win.viewport
        scene = viewport.active_scene
        
        # 1. Calcula FPS real a partir do Delta Time do último frame
        dt = max(0.0001, time.time() - viewport._last_time)
        # Se a simulação não estiver rodando ativamente, o tick do QTimer define a taxa
        fps = 1.0 / dt if dt < 0.2 else 60.0
        # Média simples para atenuar ruídos
        self.chart.add_sample(fps)
        
        self.lbl_fps.setText(f"FPS: {int(fps)}")
        self.lbl_frame_time.setText(f"Frame Time: {dt*1000:.1f} ms")
        
        # 2. Consumo de Memória (Estimado)
        mem = self.get_estimated_memory()
        self.lbl_memory.setText(f"Memória: {mem:.1f} MB")
        
        # 3. Estatísticas de Física da Cena
        num_bodies = 0
        num_colliders = 0
        
        objs = getattr(scene, "editable_objects", scene.game_objects)
        for obj in objs:
            from engine.physics.rigidbody import RigidBody
            from engine.physics.collider import BoxCollider, CircleCollider
            if obj.get_component(RigidBody):
                num_bodies += 1
            if obj.get_component(BoxCollider) or obj.get_component(CircleCollider):
                num_colliders += 1
                
        self.lbl_physics.setText(f"Física: {num_bodies} Corpos / {num_colliders} Colisores")

    def get_estimated_memory(self) -> float:
        """Retorna estimativa portátil de memória do processo."""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback seguro estimando com base nas janelas e caches do pygame
            base = 15.4
            if pygame.display.get_init() and pygame.display.get_surface():
                sz = pygame.display.get_surface().get_size()
                base += (sz[0] * sz[1] * 4) / (1024 * 1024)
            return base
