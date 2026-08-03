"""Dock do Profiler Visual (Cliente oficial da Diagnostics Platform)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSplitter,
)

from engine.core.context import EngineContext
from engine.diagnostics.service import DiagnosticsService


class ProfilerGraphWidget(QWidget):
    """Widget de gráfico de linhas em tempo real para contadores de performance."""

    def __init__(self, counter_name: str = "fps", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProfilerChart")
        self.counter_name = counter_name
        self.history: list[float] = []

    def set_history(self, history: list[float]) -> None:
        self.history = history
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor("#16161D"))
        painter.setPen(QPen(QColor("#2E2E3E"), 1))
        painter.drawRect(rect)

        if not self.history or len(self.history) < 2:
            return

        max_val = max(max(self.history), 60.0)
        step_x = rect.width() / max(len(self.history) - 1, 1)

        painter.setPen(QPen(QColor("#2ECC71"), 2))
        for idx in range(len(self.history) - 1):
            x1 = idx * step_x
            y1 = rect.height() - (self.history[idx] / max_val * rect.height())
            x2 = (idx + 1) * step_x
            y2 = rect.height() - (self.history[idx + 1] / max_val * rect.height())
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))


class ProfilerDock(QDockWidget):
    """Dock do Profiler Visual (Cliente da Diagnostics Platform)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("📊 Profiler Visual", parent)
        self.setObjectName("ProfilerDock")
        self.setMinimumHeight(240)

        container = QWidget(self)
        container.setObjectName("ProfilerPanel")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Toolbar & Indicadores numéricos
        stats_layout = QHBoxLayout()
        self.lbl_fps = QLabel("FPS: 60", self)
        self.lbl_fps.setStyleSheet("font-weight: bold; color: #2ECC71; font-size: 14px;")

        self.lbl_frame_time = QLabel("Frame: 16.6 ms", self)
        self.lbl_frame_time.setStyleSheet("font-weight: bold; color: #3498DB; font-size: 14px;")

        self.lbl_memory = QLabel("Mem: 42 MB", self)
        self.lbl_memory.setStyleSheet("font-weight: bold; color: #F1C40F; font-size: 14px;")

        self.lbl_draw_calls = QLabel("Draws: 12", self)
        self.lbl_draw_calls.setStyleSheet("font-weight: bold; color: #E74C3C; font-size: 14px;")

        for label in (
            self.lbl_fps,
            self.lbl_frame_time,
            self.lbl_memory,
            self.lbl_draw_calls,
        ):
            label.setObjectName("ProfilerMetric")

        stats_layout.addWidget(self.lbl_fps)
        stats_layout.addWidget(self.lbl_frame_time)
        stats_layout.addWidget(self.lbl_memory)
        stats_layout.addWidget(self.lbl_draw_calls)
        stats_layout.addStretch(1)

        main_layout.addLayout(stats_layout)

        # Gráfico de tempo real
        self.graph = ProfilerGraphWidget("fps", container)
        main_layout.addWidget(self.graph, 1)

        self.setWidget(container)

        # Timer de atualização (60 FPS)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(100)  # 10 Hz refresh rate
        self._refresh_timer.timeout.connect(self._on_refresh)
        self._refresh_timer.start()

    def _on_refresh(self) -> None:
        context = EngineContext.current()
        if not context:
            return
        diag_service = context.services.get_optional(DiagnosticsService)
        if not diag_service:
            return

        fps_c = diag_service.get_counter("fps")
        if fps_c:
            self.lbl_fps.setText(f"FPS: {fps_c.current_value:.0f}")
            self.graph.set_history(fps_c.history)

        ft_c = diag_service.get_counter("frame_time")
        if ft_c:
            self.lbl_frame_time.setText(f"Frame: {ft_c.current_value:.1f} ms")

        mem_c = diag_service.get_counter("memory_heap")
        if mem_c:
            self.lbl_memory.setText(f"Mem: {mem_c.current_value:.1f} MB")

        draw_c = diag_service.get_counter("draw_calls")
        if draw_c:
            self.lbl_draw_calls.setText(f"Draws: {draw_c.current_value:.0f}")
