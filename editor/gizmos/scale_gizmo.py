"""
editor/gizmos/scale_gizmo.py
─────────────────────────────────────────────────────────────────────────────
Overlay Qt/Pygame para a Scale Tool (R) da Fase 1.
"""
from __future__ import annotations

import math
from typing import Any, Callable

from PySide6.QtCore import QPointF, Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QPen


class QtScaleGizmoOverlay:
    """Gizmo Qt para a ferramenta Scale (eixos X/Y com cubos nas extremidades + quadrado central de escala uniforme)."""

    def __init__(
        self,
        axis_length: int = 70,
        handle_size: int = 10,
        tolerance: int = 12,
    ) -> None:
        self.axis_length = axis_length
        self.handle_size = handle_size
        self.tolerance = tolerance
        self.color_x = QColor(235, 75, 75)   # Vermelho
        self.color_y = QColor(75, 215, 95)   # Verde
        self.color_center = QColor(245, 245, 245) # Branco

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
        length = self.axis_length
        hs = self.handle_size

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # ── Eixo X (Vermelho) ──────────────────────────────────────────────────
        pen_x = QPen(self.color_x, 3, Qt.SolidLine)
        painter.setPen(pen_x)
        painter.drawLine(QPointF(cx, cy), QPointF(cx + length, cy))
        painter.setBrush(QBrush(self.color_x))
        painter.drawRect(QRectF(cx + length - hs/2, cy - hs/2, hs, hs))

        # ── Eixo Y (Verde) ───────────────────────────────────────────────────
        pen_y = QPen(self.color_y, 3, Qt.SolidLine)
        painter.setPen(pen_y)
        painter.drawLine(QPointF(cx, cy), QPointF(cx, cy - length))
        painter.setBrush(QBrush(self.color_y))
        painter.drawRect(QRectF(cx - hs/2, cy - length - hs/2, hs, hs))

        # ── Centro Uniforme (Quadrado Branco) ─────────────────────────────────
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(self.color_center))
        painter.drawRect(QRectF(cx - hs, cy - hs, hs * 2, hs * 2))

        painter.restore()

    def hit_test(
        self,
        x: float,
        y: float,
        selected: Any,
        world_to_viewport: Callable[[Any], tuple[float, float]],
    ) -> str | None:
        """Retorna 'x', 'y', 'center' ou None."""
        if selected is None or not hasattr(selected, "transform"):
            return None
        pos = getattr(selected.transform, "position", None)
        if pos is None:
            return None

        cx, cy = world_to_viewport(pos)
        length = self.axis_length
        hs = self.handle_size

        # Teste Centro (Uniforme)
        if abs(x - cx) <= hs and abs(y - cy) <= hs:
            return "center"

        # Teste Eixo X
        if (cx <= x <= cx + length + hs) and abs(y - cy) <= self.tolerance:
            return "x"

        # Teste Eixo Y
        if (cy - length - hs <= y <= cy) and abs(x - cx) <= self.tolerance:
            return "y"

        return None
