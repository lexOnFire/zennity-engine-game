"""Régua Temporal (TimelineRuler) do Animation Studio Visual.

Suporta:
- Formatador de tempo (Segundos / Frames / Timecode)
- Zoom (scroll da roda do mouse)
- Pan (drag com botão do meio ou Shift+drag)
- Playhead com arraste interativo (scrubbing)
- Snapping ajustável (ex: 1/10s, 1/30s, 1/60s)
- Marcadores de tempo customizados
"""
from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QWidget


class TimelineMarker:
    def __init__(self, time: float, label: str = "", color: str = "#F5A623") -> None:
        self.time = float(time)
        self.label = str(label)
        self.color = QColor(color)


class TimelineRuler(QWidget):
    """Widget de Régua Temporal para o Animation Studio Visual."""

    time_changed = Signal(float)  # Emitido quando o playhead é movido

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setMouseTracking(True)

        # Estado da Régua
        self.current_time: float = 0.0
        self.duration: float = 5.0
        self.fps: int = 30
        self.zoom_factor: float = 100.0  # Pixels por segundo
        self.pan_offset_x: float = 0.0   # Offset de pan em pixels
        self.snap_interval: float = 0.1  # Segundos para snapping

        self.markers: List[TimelineMarker] = []
        self._is_dragging_playhead: bool = False
        self._is_panning: bool = False
        self._last_mouse_pos: QPoint = QPoint()

    def time_to_pixel(self, time_seconds: float) -> float:
        return (time_seconds * self.zoom_factor) + self.pan_offset_x

    def pixel_to_time(self, pixel_x: float) -> float:
        t = (pixel_x - self.pan_offset_x) / max(self.zoom_factor, 1.0)
        return max(0.0, t)

    def snap_time(self, t: float) -> float:
        if self.snap_interval <= 0:
            return t
        return round(t / self.snap_interval) * self.snap_interval

    def set_current_time(self, time_seconds: float) -> None:
        self.current_time = max(0.0, float(time_seconds))
        self.update()
        self.time_changed.emit(self.current_time)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fundo
        rect = self.rect()
        painter.fillRect(rect, QColor("#1E1E24"))

        # Borda inferior
        painter.setPen(QPen(QColor("#33333D"), 1))
        painter.drawLine(0, rect.height() - 1, rect.width(), rect.height() - 1)

        # Marcas de tempo
        painter.setFont(QFont("Segoe UI", 8))

        # Calcula o intervalo visual de marcações
        sec_step = 1.0
        if self.zoom_factor < 40:
            sec_step = 2.0
        elif self.zoom_factor > 200:
            sec_step = 0.5

        start_time = max(0.0, self.pixel_to_time(0))
        end_time = self.pixel_to_time(rect.width()) + sec_step

        t = int(start_time / sec_step) * sec_step
        while t <= end_time:
            x = self.time_to_pixel(t)
            if 0 <= x <= rect.width():
                # Tracinho principal
                painter.setPen(QPen(QColor("#888899"), 1))
                painter.drawLine(int(x), rect.height() - 12, int(x), rect.height() - 2)

                # Texto de tempo (ex: 01:15 ou 1.5s)
                time_str = f"{t:.1f}s" if sec_step < 1.0 else f"{int(t)}s"
                painter.setPen(QColor("#AAAAEE"))
                painter.drawText(int(x) + 4, rect.height() - 14, time_str)

                # Sub-divisões (ticks menores)
                sub_step = sec_step / 5.0
                for sub_i in range(1, 5):
                    sub_t = t + sub_i * sub_step
                    sub_x = self.time_to_pixel(sub_t)
                    if 0 <= sub_x <= rect.width():
                        painter.setPen(QPen(QColor("#444455"), 1))
                        painter.drawLine(int(sub_x), rect.height() - 6, int(sub_x), rect.height() - 2)

            t += sec_step

        # Desenhar Marcadores
        for marker in self.markers:
            mx = self.time_to_pixel(marker.time)
            if 0 <= mx <= rect.width():
                painter.setPen(QPen(marker.color, 1))
                painter.drawLine(int(mx), 0, int(mx), rect.height())

        # Desenhar Playhead
        px = self.time_to_pixel(self.current_time)
        if 0 <= px <= rect.width():
            # Cabeça do playhead (Triângulo vermelho)
            painter.setBrush(QColor("#E74C3C"))
            painter.setPen(Qt.NoPen)
            poly = [
                QPoint(int(px) - 6, 0),
                QPoint(int(px) + 6, 0),
                QPoint(int(px) + 6, 8),
                QPoint(int(px), 14),
                QPoint(int(px) - 6, 8),
            ]
            painter.drawPolygon(poly)

            # Linha vertical
            painter.setPen(QPen(QColor("#E74C3C"), 2))
            painter.drawLine(int(px), 14, int(px), rect.height())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging_playhead = True
            raw_time = self.pixel_to_time(event.position().x())
            snapped = self.snap_time(raw_time)
            self.set_current_time(snapped)
        elif event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_mouse_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_dragging_playhead:
            raw_time = self.pixel_to_time(event.position().x())
            snapped = self.snap_time(raw_time)
            self.set_current_time(snapped)
        elif self._is_panning:
            delta = event.globalPosition().toPoint() - self._last_mouse_pos
            self._last_mouse_pos = event.globalPosition().toPoint()
            self.pan_offset_x += delta.x()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging_playhead = False
        elif event.button() == Qt.MiddleButton:
            self._is_panning = False

    def wheelEvent(self, event: QWheelEvent) -> None:
        # Zoom com roda do mouse
        delta = event.angleDelta().y()
        mouse_x = event.position().x()
        time_under_mouse = self.pixel_to_time(mouse_x)

        if delta > 0:
            self.zoom_factor = min(self.zoom_factor * 1.25, 1000.0)
        else:
            self.zoom_factor = max(self.zoom_factor / 1.25, 10.0)

        # Ajusta pan para manter o tempo sob o cursor estático
        self.pan_offset_x = mouse_x - (time_under_mouse * self.zoom_factor)
        self.update()
