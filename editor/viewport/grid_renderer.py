"""
editor/viewport/grid_renderer.py
─────────────────────────────────────────────────────────────────────────────
Renderizador de Grid Infinito usando QPainter.
Desenha grids principal e secundário, com a origem (0,0) destacada.
"""
from __future__ import annotations

import math
from typing import Any, Callable
from PySide6.QtCore import QLineF, Qt
from PySide6.QtGui import QColor, QPainter, QPen


class GridRenderer:
    """Renderizador do Grid Infinito da Viewport usando QPainter."""

    def __init__(self) -> None:
        self.grid_size: int = 32
        self.axis_color = QColor(140, 150, 170, 220)       # Origem destacada (0,0)
        self.primary_color = QColor(80, 85, 100, 160)       # Múltiplos de 5
        self.secondary_color = QColor(60, 62, 74, 80)       # Grade secundária

    def draw(
        self,
        painter: QPainter,
        vp_w: int,
        vp_h: int,
        zoom: float,
        camera_pos: Any,
        world_to_viewport: Callable[[tuple[float, float] | Any], tuple[float, float]],
    ) -> None:
        """Desenha o grid infinito alinhado à câmera usando QPainter.

        Garante que eixos X/Y principais e secundários acompanhem o pan/zoom.
        """
        # Limites visíveis no mundo
        # Como world_to_viewport(world) = (world - cam) * zoom + center
        # world = (screen - center) / zoom + cam
        left_w = (0.0 - vp_w / 2.0) / zoom + camera_pos[0]
        right_w = (vp_w - vp_w / 2.0) / zoom + camera_pos[0]
        top_w = (0.0 - vp_h / 2.0) / zoom + camera_pos[1]
        bottom_w = (vp_h - vp_h / 2.0) / zoom + camera_pos[1]

        # Espaçamento do grid secundário em tela
        spacing_px = self.grid_size * zoom
        # Fade das linhas secundárias (menor que 8px -> some, maior que 20px -> opacidade máxima)
        alpha_sec = max(0.0, min(1.0, (spacing_px - 8.0) / 12.0))

        # Espaçamento do grid principal em tela
        prim_spacing_px = spacing_px * 5
        alpha_prim = max(0.2, min(1.0, (prim_spacing_px - 8.0) / 12.0))

        painter.save()
        # Não usaremos antialiasing para linhas retas horizontais/verticais (deixa mais limpo/nítido)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # ── 1. Grid Secundário (múltiplos normais de grid_size) ────────────────
        if alpha_sec > 0.0:
            col = QColor(self.secondary_color)
            col.setAlpha(int(self.secondary_color.alpha() * alpha_sec))
            pen = QPen(col, 1, Qt.SolidLine)
            painter.setPen(pen)

            # Todas as linhas secundárias usam o mesmo pen, então acumulamos
            # em uma lista e desenhamos com uma única chamada a drawLines(),
            # em vez de criar 2 QPointF + 1 chamada drawLine() por linha
            # (isso gerava ~100 alocações Qt por frame só do grid).
            secondary_lines: list[QLineF] = []

            # Linhas Verticais
            start_x = math.floor(left_w / self.grid_size) * self.grid_size
            curr_x = start_x
            while curr_x <= right_w:
                is_primary = abs(curr_x % (self.grid_size * 5)) < 0.1
                if not is_primary:
                    sx, _ = world_to_viewport((curr_x, 0.0))
                    if 0 <= sx < vp_w:
                        secondary_lines.append(QLineF(sx, 0.0, sx, vp_h))
                curr_x += self.grid_size

            # Linhas Horizontais
            start_y = math.floor(top_w / self.grid_size) * self.grid_size
            curr_y = start_y
            while curr_y <= bottom_w:
                is_primary = abs(curr_y % (self.grid_size * 5)) < 0.1
                if not is_primary:
                    _, sy = world_to_viewport((0.0, curr_y))
                    if 0 <= sy < vp_h:
                        secondary_lines.append(QLineF(0.0, sy, vp_w, sy))
                curr_y += self.grid_size

            if secondary_lines:
                painter.drawLines(secondary_lines)

        # ── 2. Grid Principal (múltiplos de 5x grid_size) + Eixos (0,0) ───────
        if alpha_prim > 0.0:
            col_p = QColor(self.primary_color)
            col_p.setAlpha(int(self.primary_color.alpha() * alpha_prim))

            step_x = self.grid_size * 5

            # Linhas normais e linhas de eixo usam pens diferentes, então
            # acumulamos cada grupo separadamente e desenhamos cada um com
            # uma única chamada a drawLines() (no máximo 2 chamadas no total
            # em vez de 1 chamada de drawLine() por linha do grid principal).
            primary_lines: list[QLineF] = []
            axis_lines: list[QLineF] = []

            # Linhas Verticais Principais
            start_x = math.floor(left_w / step_x) * step_x
            curr_x = start_x
            while curr_x <= right_w:
                sx, _ = world_to_viewport((curr_x, 0.0))
                if 0 <= sx < vp_w:
                    is_axis = abs(curr_x) < 0.1
                    line = QLineF(sx, 0.0, sx, vp_h)
                    if is_axis:
                        axis_lines.append(line)
                    else:
                        primary_lines.append(line)
                curr_x += step_x

            # Linhas Horizontais Principais
            step_y = self.grid_size * 5
            start_y = math.floor(top_w / step_y) * step_y
            curr_y = start_y
            while curr_y <= bottom_w:
                _, sy = world_to_viewport((0.0, curr_y))
                if 0 <= sy < vp_h:
                    is_axis = abs(curr_y) < 0.1
                    line = QLineF(0.0, sy, vp_w, sy)
                    if is_axis:
                        axis_lines.append(line)
                    else:
                        primary_lines.append(line)
                curr_y += step_y

            if primary_lines:
                painter.setPen(QPen(col_p, 1, Qt.SolidLine))
                painter.drawLines(primary_lines)
            if axis_lines:
                painter.setPen(QPen(self.axis_color, 2, Qt.SolidLine))
                painter.drawLines(axis_lines)

        painter.restore()
