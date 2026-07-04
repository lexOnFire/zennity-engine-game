"""
editor/viewport/viewport_overlay.py
─────────────────────────────────────────────────────────────────────────────
Desenho de HUD informativo da Viewport, exibindo estatísticas de FPS, câmera,
tamanho do grid, snap e coordenadas reais do mouse.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen


class ViewportOverlay:
    """Renderiza painéis flutuantes (HUD) informativos da Viewport usando QPainter."""

    def __init__(self) -> None:
        pass

    def draw_hud(
        self,
        painter: QPainter,
        vp_w: int,
        vp_h: int,
        camera_name: str,
        fps: float,
        object_count: int,
        active_tool: str,
    ) -> None:
        """Desenha o HUD superior esquerdo com dados do status da viewport."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Retângulo translúcido de fundo
        hud_rect = QRectF(10.0, 10.0, 200.0, 92.0)
        painter.setBrush(QBrush(QColor(18, 19, 24, 180)))
        painter.setPen(QPen(QColor(60, 62, 74, 120), 1))
        painter.drawRoundedRect(hud_rect, 5.0, 5.0)

        # Textos informativos
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        
        # Nome da Câmera (negrito)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(QColor(240, 240, 245)))
        painter.drawText(20, 28, f"🎥 {camera_name}")
        
        # Outras métricas
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QPen(QColor(180, 182, 194)))
        painter.drawText(20, 48, f"FPS: {int(fps)}")
        painter.drawText(20, 66, f"Objetos: {object_count}")
        painter.drawText(20, 84, f"Ferramenta: {active_tool.upper()}")

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
        """Desenha a barra de status inferior esquerda com coordenadas mundiais."""
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

        # Caixa flutuante no rodapé
        bg_rect = QRectF(10.0, vp_h - 10.0 - text_height - 6.0, text_width + 16.0, text_height + 6.0)
        painter.setBrush(QBrush(QColor(18, 19, 24, 180)))
        painter.setPen(QPen(QColor(60, 62, 74, 120), 1))
        painter.drawRoundedRect(bg_rect, 4.0, 4.0)

        # Desenha texto
        font = QFont("Segoe UI", 8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(180, 182, 194)))
        painter.drawText(18, int(vp_h - 14.0), text)

        painter.restore()
