"""
editor/viewport/viewport_overlay.py
Draws lightweight Scene View HUD overlays.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen


class ViewportOverlay:
    """Render floating informational panels for the Scene View."""

    def draw_hud(
        self,
        painter: QPainter,
        vp_w: int,
        vp_h: int,
        camera_name: str,
        fps: float,
        object_count: int,
        active_tool: str,
        scene_name: str = "Scene",
        view_mode: str = "Edit",
        is_playing: bool = False,
    ) -> None:
        """Draw the upper-left Scene View status panel."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        hud_rect = QRectF(10.0, 10.0, 230.0, 124.0)
        painter.setBrush(QBrush(QColor(18, 19, 24, 180)))
        painter.setPen(QPen(QColor(60, 62, 74, 120), 1))
        painter.drawRoundedRect(hud_rect, 5.0, 5.0)

        font = QFont("Segoe UI", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(240, 240, 245)))
        painter.drawText(20, 28, f"Scene: {scene_name}")

        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QPen(QColor(180, 182, 194)))
        mode_label = "PLAY" if is_playing else str(view_mode).upper()
        painter.drawText(20, 48, f"Mode: {mode_label}")
        painter.drawText(20, 66, f"Camera: {camera_name}")
        painter.drawText(20, 84, f"FPS: {int(fps)}")
        painter.drawText(20, 102, f"Objects: {object_count}")
        painter.drawText(20, 120, f"Tool: {str(active_tool).upper()}")

        painter.restore()

    def draw_coordinates(
        self,
        painter: QPainter,
        vp_w: int,
        vp_h: int,
        mouse_world: tuple[float, float],
        zoom_pct: int,
        grid_size: int,
        snap_on: bool,
    ) -> None:
        """Draw the lower-left coordinates and status panel."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        text = (
            f"X: {mouse_world[0]:.1f}  Y: {mouse_world[1]:.1f}   |   "
            f"Zoom: {zoom_pct}%   |   Grid: {grid_size}px   |   "
            f"Snap: {'ON' if snap_on else 'OFF'}"
        )

        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(text)
        text_height = metrics.height()

        bg_rect = QRectF(10.0, vp_h - 10.0 - text_height - 6.0, text_width + 16.0, text_height + 6.0)
        painter.setBrush(QBrush(QColor(18, 19, 24, 180)))
        painter.setPen(QPen(QColor(60, 62, 74, 120), 1))
        painter.drawRoundedRect(bg_rect, 4.0, 4.0)

        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(180, 182, 194)))
        painter.drawText(18, int(vp_h - 14.0), text)

        painter.restore()
