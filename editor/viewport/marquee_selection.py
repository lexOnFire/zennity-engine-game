"""
editor/viewport/marquee_selection.py
─────────────────────────────────────────────────────────────────────────────
Seleção por caixa retangular (Marquee Drag Select) para o Viewport AAA.
"""
from __future__ import annotations

from typing import Any, Callable, List
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QColor, QPainter, QPen


class MarqueeSelection:
    """Gerencia a caixa de seleção drag na Viewport."""

    def __init__(self) -> None:
        self.is_selecting = False
        self.start_pos: tuple[float, float] | None = None
        self.current_pos: tuple[float, float] | None = None
        self.box_color = QColor(0, 150, 255, 60)
        self.border_color = QColor(0, 180, 255, 220)

    def start(self, x: float, y: float) -> None:
        self.is_selecting = True
        self.start_pos = (x, y)
        self.current_pos = (x, y)

    def update(self, x: float, y: float) -> None:
        if self.is_selecting:
            self.current_pos = (x, y)

    def finish(self) -> QRectF | None:
        if not self.is_selecting or not self.start_pos or not self.current_pos:
            self.is_selecting = False
            return None
        rect = self.get_rect()
        self.is_selecting = False
        self.start_pos = None
        self.current_pos = None
        return rect

    def get_rect(self) -> QRectF:
        if not self.start_pos or not self.current_pos:
            return QRectF()
        x1, y1 = self.start_pos
        x2, y2 = self.current_pos
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)
        return QRectF(x, y, w, h)

    def draw(self, painter: QPainter) -> None:
        if not self.is_selecting:
            return
        rect = self.get_rect()
        if rect.width() < 2 or rect.height() < 2:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(QPen(self.border_color, 1, Qt.DashLine))
        painter.setBrush(QBrush(self.box_color))
        painter.drawRect(rect)
        painter.restore()

    def select_objects(
        self,
        objects: List[Any],
        world_to_viewport: Callable[[Any], tuple[float, float]],
    ) -> List[Any]:
        """Retorna todos os objetos contidos dentro da caixa de seleção."""
        rect = self.get_rect()
        selected = []
        if rect.width() < 2 or rect.height() < 2:
            return selected

        for obj in objects:
            if getattr(obj, "name", "") == "EditorCamera":
                continue
            pos = getattr(getattr(obj, "transform", None), "position", None)
            if pos is None:
                continue
            cx, cy = world_to_viewport(pos)
            if rect.contains(QPointF(cx, cy)):
                selected.append(obj)
        return selected
