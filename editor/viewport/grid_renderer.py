"""
editor/viewport/grid_renderer.py
─────────────────────────────────────────────────────────────────────────────
Renderizador de Grid Infinito baseado em Pygame.
Desenha grids principal e secundário, com fade inteligente conforme o nível de zoom.
"""
from __future__ import annotations

import math
import numpy as np
import pygame


class GridRenderer:
    """Renderizador do Grid Infinito da Viewport.

    Garante que as linhas do grid acompanhem o deslocamento da câmera e sejam
    redimensionadas de forma limpa. Desativa linhas finas automaticamente se estiver
    muito distante (zoom out) para evitar poluição visual (Moire effect).
    """

    def __init__(self) -> None:
        self.grid_size: int = 32
        self.axis_color = (110, 115, 130, 200)

    def draw_pygame(
        self,
        screen: pygame.Surface,
        zoom: float,
        camera_pos: np.ndarray,
        lay: dict,
    ) -> None:
        """Desenha o grid infinito em uma superfície Pygame.

        Args:
            screen: Superfície Pygame alvo.
            zoom: Nível de zoom atual da câmera.
            camera_pos: Posição [x, y, z] atual da câmera no mundo.
            lay: Dicionário com layout da viewport (vp_w, vp_h, vp_left, vp_top).
        """
        vp_w = lay["vp_w"]
        vp_h = lay["vp_h"]
        vp_left = lay["vp_left"]
        vp_top = lay["vp_top"]

        # Espaçamento do grid secundário em pixels de tela
        spacing_px = self.grid_size * zoom

        # Fator de atenuação (fade) para o grid secundário (fina)
        # Some se for menor que 8px, totalmente visível se for maior que 20px
        alpha_sec = max(0.0, min(1.0, (spacing_px - 8.0) / 12.0))

        # Espaçamento do grid principal (grossa, múltiplos de 5)
        prim_spacing_px = spacing_px * 5
        alpha_prim = max(0.2, min(1.0, (prim_spacing_px - 8.0) / 12.0))

        # Mapeamento reverso para achar os limites do mundo visíveis
        left_w = (vp_left - vp_w / 2.0) / zoom + camera_pos[0]
        right_w = (vp_left + vp_w - vp_w / 2.0) / zoom + camera_pos[0]
        top_w = (vp_top - vp_h / 2.0) / zoom + camera_pos[1]
        bottom_w = (vp_top + vp_h - vp_h / 2.0) / zoom + camera_pos[1]

        # Superfície de desenho intermediária com suporte a canal alfa
        grid_surf = pygame.Surface((vp_w, vp_h), pygame.SRCALPHA)

        # ── 1. Desenho do Grid Secundário (Espaçamento de 1x grid_size) ───────
        if alpha_sec > 0.0:
            col_sec = (60, 62, 74, int(50 * alpha_sec))

            # Linhas Verticais
            start_x = math.floor(left_w / self.grid_size) * self.grid_size
            curr_x = start_x
            while curr_x <= right_w:
                is_primary = abs(curr_x % (self.grid_size * 5)) < 0.1
                if not is_primary:
                    sx = int((curr_x - camera_pos[0]) * zoom + vp_w / 2.0)
                    if 0 <= sx < vp_w:
                        pygame.draw.line(grid_surf, col_sec, (sx, 0), (sx, vp_h))
                curr_x += self.grid_size

            # Linhas Horizontais
            start_y = math.floor(top_w / self.grid_size) * self.grid_size
            curr_y = start_y
            while curr_y <= bottom_w:
                is_primary = abs(curr_y % (self.grid_size * 5)) < 0.1
                if not is_primary:
                    sy = int((curr_y - camera_pos[1]) * zoom + vp_h / 2.0)
                    if 0 <= sy < vp_h:
                        pygame.draw.line(grid_surf, col_sec, (0, sy), (vp_w, sy))
                curr_y += self.grid_size

        # ── 2. Desenho do Grid Principal (Espaçamento de 5x grid_size) ────────
        if alpha_prim > 0.0:
            col_prim = (80, 85, 100, int(110 * alpha_prim))

            # Linhas Verticais
            step_x = self.grid_size * 5
            start_x = math.floor(left_w / step_x) * step_x
            curr_x = start_x
            while curr_x <= right_w:
                sx = int((curr_x - camera_pos[0]) * zoom + vp_w / 2.0)
                if 0 <= sx < vp_w:
                    is_axis = abs(curr_x) < 0.1
                    line_col = self.axis_color if is_axis else col_prim
                    width = 2 if is_axis else 1
                    pygame.draw.line(grid_surf, line_col, (sx, 0), (sx, vp_h), width)
                curr_x += step_x

            # Linhas Horizontais
            step_y = self.grid_size * 5
            start_y = math.floor(top_w / step_y) * step_y
            curr_y = start_y
            while curr_y <= bottom_w:
                sy = int((curr_y - camera_pos[1]) * zoom + vp_h / 2.0)
                if 0 <= sy < vp_h:
                    is_axis = abs(curr_y) < 0.1
                    line_col = self.axis_color if is_axis else col_prim
                    width = 2 if is_axis else 1
                    pygame.draw.line(grid_surf, line_col, (0, sy), (vp_w, sy), width)
                curr_y += step_y

        # Blita a grade na superfície principal da viewport
        screen.blit(grid_surf, (vp_left, vp_top))
