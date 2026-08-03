"""
editor/viewport/viewport_toolbar_overlay.py
─────────────────────────────────────────────────────────────────────────────
Toolbar flutuante com stats (FPS, Draw Calls, Triângulos) e seletores de ferramentas (Q, W, E, R, T).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush


class ViewportToolbarOverlay:
    """Toolbar estilo Unity flutuante na Viewport."""

    def __init__(self) -> None:
        self.active_tool = "W"  # Q, W, E, R, T
        self.grid_enabled = True
        self.gizmos_enabled = True
        self.snap_enabled = False
        self.snap_value = 1.0
        self.fps = 60
        self.draw_calls = 12
        self.triangles = 340

    def draw(self, painter: QPainter, width: float, height: float) -> None:
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # ── 1. Toolbar Principal Superior (Ferramentas W E R) ─────────────────
        tools = [("Q", "Pan"), ("W", "Move"), ("E", "Rotate"), ("R", "Scale"), ("T", "Rect")]
        bar_w = len(tools) * 36 + 10
        bar_h = 30
        bar_x = 12
        bar_y = 12

        # Fundo semi-transparente escuro premium
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
        painter.setBrush(QBrush(QColor(20, 24, 30, 210)))
        painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 6, 6)

        font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(font)

        for i, (tool, label) in enumerate(tools):
            tx = bar_x + 5 + i * 36
            ty = bar_y + 3
            tw = 32
            th = 24
            is_active = (tool == self.active_tool)

            if is_active:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(0, 150, 255, 220)))
                painter.drawRoundedRect(QRectF(tx, ty, tw, th), 4, 4)
                painter.setPen(QColor(255, 255, 255))
            else:
                painter.setPen(QColor(180, 190, 200))

            painter.drawText(QRectF(tx, ty, tw, th), Qt.AlignCenter, tool)

        # ── 2. Overlay de Estatísticas (Stats Box) ───────────────────────────
        stats_w = 170
        stats_h = 60
        stats_x = width - stats_w - 12
        stats_y = 12

        painter.setPen(QPen(QColor(255, 255, 255, 25)))
        painter.setBrush(QBrush(QColor(15, 18, 22, 200)))
        painter.drawRoundedRect(QRectF(stats_x, stats_y, stats_w, stats_h), 6, 6)

        stats_font = QFont("Segoe UI", 8)
        painter.setFont(stats_font)
        painter.setPen(QColor(0, 225, 140)) # Verde limão neon para FPS
        painter.drawText(QPointF(stats_x + 10, stats_y + 18), f"FPS: {self.fps}")
        painter.setPen(QColor(200, 210, 220))
        painter.drawText(QPointF(stats_x + 10, stats_y + 34), f"Draw Calls: {self.draw_calls}")
        painter.drawText(QPointF(stats_x + 10, stats_y + 50), f"Triângulos: {self.triangles}")

        painter.restore()
