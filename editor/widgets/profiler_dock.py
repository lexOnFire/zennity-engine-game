from collections import deque
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF
from PySide6.QtCore import QPointF
from editor.ui.tokens import DEFAULT_TOKENS


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
        self.setObjectName("ProfilerChart")

    def add_sample(self, value: float) -> None:
        self.history.append(value)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Desenha o fundo escuro
        painter.setBrush(QBrush(QColor(DEFAULT_TOKENS.input_bg)))
        painter.setPen(QPen(QColor(DEFAULT_TOKENS.border_strong), 1))
        painter.drawRoundedRect(0, 0, w, h, 6, 6)
        
        # Desenha linhas horizontais de grade de referência (FPS 30 e 60)
        painter.setPen(QPen(QColor(DEFAULT_TOKENS.border), 1, Qt.DashLine))
        
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
        
        fill_color = QColor(DEFAULT_TOKENS.accent)
        fill_color.setAlpha(40)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(poly)
        
        # Desenha a linha de contorno
        pen = QPen(QColor(DEFAULT_TOKENS.accent_hover), 2, Qt.SolidLine)
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
        content.setObjectName("ProfilerPanel")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        
        # 1. Painel de Métricas Rápidas
        metrics = QWidget()
        metrics.setObjectName("ProfilerMetrics")
        m_layout = QHBoxLayout(metrics)
        m_layout.setContentsMargins(2, 2, 2, 2)
        m_layout.setSpacing(16)
        
        self.lbl_fps = QLabel("FPS: --")
        self.lbl_frame_time = QLabel("Frame Time: -- ms")
        self.lbl_cpu = QLabel("CPU: -- ms")
        self.lbl_p95 = QLabel("P95: -- ms")
        self.lbl_memory = QLabel("Memória: -- MB")
        self.lbl_physics = QLabel("Física: 0 corpos / 0 colisores")
        
        for lbl in (
            self.lbl_fps,
            self.lbl_frame_time,
            self.lbl_cpu,
            self.lbl_p95,
            self.lbl_memory,
            self.lbl_physics,
        ):
            lbl.setObjectName("ProfilerMetric")
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
        self._profiler = None

    def set_profiler(self, profiler) -> None:
        self._profiler = profiler

    def _current_profiler(self):
        if self._profiler is not None:
            return self._profiler
        win = self.window()
        manager = getattr(win, "runtime_manager", None)
        runtime_scene = getattr(manager, "runtime_scene", None)
        if runtime_scene is not None:
            return getattr(runtime_scene, "profiler", None)
        viewport = getattr(win, "viewport", None)
        scene = getattr(viewport, "active_scene", None)
        return getattr(scene, "profiler", None)

    @Slot()
    def sample_metrics(self) -> None:
        """Coleta estatísticas de desempenho reais e atualiza o gráfico."""
        profiler = self._current_profiler()
        if profiler is None:
            return
        summary = profiler.summary(window=120)
        if summary.sample_count == 0:
            return
        self.chart.add_sample(summary.fps)
        self.lbl_fps.setText(f"FPS: {summary.fps:.0f}")
        self.lbl_frame_time.setText(
            f"Frame Time: {summary.average_frame_ms:.2f} ms"
        )
        self.lbl_cpu.setText(f"CPU: {summary.average_cpu_ms:.2f} ms")
        self.lbl_p95.setText(f"P95: {summary.p95_frame_ms:.2f} ms")
        self.lbl_memory.setText(f"Memória: {summary.memory_mb:.1f} MB")
        self.lbl_physics.setText(
            f"Física: {summary.physics_bodies} corpos"
        )
