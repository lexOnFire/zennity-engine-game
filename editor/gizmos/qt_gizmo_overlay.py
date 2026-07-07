from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QPolygonF


class QtMoveGizmoOverlay:
    """Desenha o Move Gizmo como overlay Qt, sem tocar no input da cena."""

    def __init__(self) -> None:
        self.axis_length = 72

    def draw(
        self,
        painter: QPainter,
        selected: Any,
        world_to_viewport: Callable[[Any], tuple[float, float]],
    ) -> None:
        if selected is None or not hasattr(selected, "transform"):
            return
        pos = getattr(selected.transform, "position", None)
        if pos is None:
            return

        cx, cy = world_to_viewport(pos)
        center = QPointF(cx, cy)
        x_end = QPointF(cx + self.axis_length, cy)
        z_end = QPointF(cx, cy - self.axis_length)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        self._draw_axis(painter, center, x_end, QColor(230, 70, 70), "x")
        self._draw_axis(painter, center, z_end, QColor(70, 210, 90), "z")

        painter.setPen(QPen(QColor(15, 15, 15), 1))
        painter.setBrush(QBrush(QColor(245, 245, 245)))
        painter.drawEllipse(center, 6, 6)
        painter.restore()

    def _draw_axis(self, painter: QPainter, start: QPointF, end: QPointF, color: QColor, axis: str) -> None:
        painter.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(QBrush(color))
        painter.drawLine(start, end)

        if axis == "x":
            head = QPolygonF([
                QPointF(end.x() + 12, end.y()),
                QPointF(end.x(), end.y() - 7),
                QPointF(end.x(), end.y() + 7),
            ])
            label_pos = QPointF(end.x() + 18, end.y() + 5)
            label = "X"
        else:
            head = QPolygonF([
                QPointF(end.x(), end.y() - 12),
                QPointF(end.x() - 7, end.y()),
                QPointF(end.x() + 7, end.y()),
            ])
            label_pos = QPointF(end.x() + 8, end.y() - 14)
            label = "Z"
        painter.drawPolygon(head)
        painter.setPen(QPen(color, 1, Qt.SolidLine))
        painter.drawText(label_pos, label)
