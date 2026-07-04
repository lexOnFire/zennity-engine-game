"""
editor/viewport/bounding_box.py
─────────────────────────────────────────────────────────────────────────────
Caixa delimitadora (Bounding Box) e 8 alças de controle/escala rotacionadas.
"""
from __future__ import annotations

from typing import Any, Callable
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen


class BoundingBoxRenderer:
    """Desenha a caixa limite e 8 pontos de ancoragem sobre o objeto selecionado.

    Essa caixa representa os limites de colisão/transformação do objeto, rotacionando
    em sincronia e preparando o suporte para a futura Scale Tool.
    """

    def __init__(
        self,
        border_color: QColor = QColor(240, 240, 250, 180),
        handle_color: QColor = QColor(80, 160, 255),
        handle_size: float = 6.0,
    ) -> None:
        self.border_color: QColor = border_color
        self.handle_color: QColor = handle_color
        self.handle_size: float = handle_size

    def draw(
        self,
        painter: QPainter,
        selected: Any,
        world_to_viewport: Callable[[Any], tuple[float, float]],
    ) -> None:
        """Renderiza a linha limite (tracejada) e as 8 alças quadradas."""
        if selected is None or not hasattr(selected, "transform"):
            return
        pos = getattr(selected.transform, "position", None)
        scale = getattr(selected.transform, "scale", None)
        if pos is None or scale is None:
            return

        cx, cy = world_to_viewport(pos)

        # Determina largura e altura na tela
        p0 = world_to_viewport((pos[0] - scale[0] / 2.0, pos[1] - scale[1] / 2.0, pos[2]))
        p1 = world_to_viewport((pos[0] + scale[0] / 2.0, pos[1] + scale[1] / 2.0, pos[2]))
        sw = abs(p1[0] - p0[0])
        sh = abs(p1[1] - p0[1])

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # ── 1. Caixa Delimitadora (Tracejada) ─────────────────────────────────
        pen = QPen(self.border_color, 1, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        # Translada o painter para o centro do objeto e aplica rotação
        painter.translate(cx, cy)
        rz = float(getattr(selected.transform, "rz", 0.0))
        painter.rotate(rz)

        # Bounding box rente à escala visual
        painter.drawRect(QRectF(-sw / 2.0, -sh / 2.0, sw, sh))

        # ── 2. Plota os 8 Pontos de Controle (Alças Quadradas) ────────────────
        painter.setPen(QPen(self.handle_color.darker(120), 1))
        painter.setBrush(QBrush(self.handle_color))

        hs = self.handle_size
        # Mapeamento local das 8 alças ao redor do centro (0,0)
        points = [
            (-sw / 2.0, -sh / 2.0),  # Top-Left (TL)
            (0.0, -sh / 2.0),        # Top-Center (TC)
            (sw / 2.0, -sh / 2.0),   # Top-Right (TR)
            (sw / 2.0, 0.0),         # Right-Center (RC)
            (sw / 2.0, sh / 2.0),    # Bottom-Right (BR)
            (0.0, sh / 2.0),         # Bottom-Center (BC)
            (-sw / 2.0, sh / 2.0),   # Bottom-Left (BL)
            (-sw / 2.0, 0.0),        # Left-Center (LC)
        ]

        for px, py in points:
            # Desenha quadrado local
            painter.drawRect(QRectF(px - hs / 2.0, py - hs / 2.0, hs, hs))

        painter.restore()
