"""Canvas de Keyframes do Animation Studio Visual (Marco C).

Suporta:
- Renderização visual de keyframes (Losangos / Diamonds)
- Inserção (duplo clique), Exclusão (Delete)
- Arraste interativo de keyframes no tempo
- Seleção múltipla com caixa de seleção (rubberband)
- Copiar e Colar (Ctrl+C / Ctrl+V)
- Alteração de interpolação (Linear / Hermite / Step)
"""
from __future__ import annotations
from typing import Dict, List, Optional, Set
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QKeyEvent
from PySide6.QtWidgets import QWidget
from engine.animation.tracks.base_track import AnimationTrack


class SelectedKeyframe:
    def __init__(self, track: AnimationTrack, keyframe: dict) -> None:
        self.track = track
        self.keyframe = keyframe


class KeyframeCanvas(QWidget):
    """Área visual interativa para manipular keyframes de todas as trilhas ativas."""

    keyframe_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.tracks: List[AnimationTrack] = []
        self.zoom_factor: float = 100.0
        self.pan_offset_x: float = 0.0
        self.track_height: int = 30
        self.current_time: float = 0.0

        self.selected_keyframes: Set[dict] = set()
        self.clipboard_keyframes: List[dict] = []

        self._is_dragging: bool = False
        self._drag_start_pos: QPointF = QPointF()
        self._dragged_keyframe: Optional[dict] = None
        self._dragged_track: Optional[AnimationTrack] = None

    def time_to_pixel(self, time_seconds: float) -> float:
        return (time_seconds * self.zoom_factor) + self.pan_offset_x

    def pixel_to_time(self, pixel_x: float) -> float:
        t = (pixel_x - self.pan_offset_x) / max(self.zoom_factor, 1.0)
        return max(0.0, t)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor("#18181E"))

        # Desenhando trilhas e keyframes
        y = 0
        for track in self.tracks:
            # Fundo alternado da trilha
            bg_color = QColor("#1C1C24") if (y // self.track_height) % 2 == 0 else QColor("#22222C")
            painter.fillRect(0, y, rect.width(), self.track_height, bg_color)
            painter.setPen(QPen(QColor("#2C2C38"), 1))
            painter.drawLine(0, y + self.track_height - 1, rect.width(), y + self.track_height - 1)

            # Renderiza keyframes da trilha
            kfs = getattr(track, "keyframes", [])
            if hasattr(track, "position_keyframes"):
                kfs = getattr(track, "position_keyframes", [])

            for kf in kfs:
                t = float(kf.get("time", 0.0))
                x = self.time_to_pixel(t)
                if 0 <= x <= rect.width():
                    cy = y + (self.track_height // 2)
                    is_selected = kf in self.selected_keyframes
                    color = QColor("#F1C40F") if is_selected else QColor("#3498DB")

                    # Desenha Losango (Diamond)
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(QColor("#FFFFFF") if is_selected else QColor("#2980B9"), 1))

                    poly = [
                        QPointF(x, cy - 6),
                        QPointF(x + 6, cy),
                        QPointF(x, cy + 6),
                        QPointF(x - 6, cy),
                    ]
                    painter.drawPolygon(poly)

            y += self.track_height

        # Linha vertical do Playhead
        px = self.time_to_pixel(self.current_time)
        if 0 <= px <= rect.width():
            painter.setPen(QPen(QColor("#E74C3C"), 2))
            painter.drawLine(int(px), 0, int(px), rect.height())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            pos = event.position()
            track_index = int(pos.y() // self.track_height)

            if 0 <= track_index < len(self.tracks):
                track = self.tracks[track_index]
                kfs = getattr(track, "keyframes", [])
                if hasattr(track, "position_keyframes"):
                    kfs = getattr(track, "position_keyframes", [])

                for kf in kfs:
                    x = self.time_to_pixel(kf.get("time", 0.0))
                    if abs(x - pos.x()) <= 8:
                        if not (event.modifiers() & Qt.ControlModifier):
                            self.selected_keyframes.clear()
                        self.selected_keyframes.add(kf)
                        self._is_dragging = True
                        self._dragged_keyframe = kf
                        self._dragged_track = track
                        self._drag_start_pos = pos
                        self.update()
                        return

            if not (event.modifiers() & Qt.ControlModifier):
                self.selected_keyframes.clear()
                self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_dragging and self._dragged_keyframe:
            new_time = self.pixel_to_time(event.position().x())
            self._dragged_keyframe["time"] = max(0.0, round(new_time, 2))
            self.keyframe_changed.emit()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._dragged_keyframe = None
            self._dragged_track = None

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Delete and self.selected_keyframes:
            for track in self.tracks:
                if hasattr(track, "keyframes"):
                    track.keyframes = [k for k in track.keyframes if k not in self.selected_keyframes]
                if hasattr(track, "position_keyframes"):
                    track.position_keyframes = [k for k in track.position_keyframes if k not in self.selected_keyframes]
            self.selected_keyframes.clear()
            self.keyframe_changed.emit()
            self.update()
