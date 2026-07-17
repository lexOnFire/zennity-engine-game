from __future__ import annotations

from typing import Any

import pygame


class MoveGizmo:
    """Gizmo 2D simples de movimentação.

    Esta primeira versão desenha os eixos X/Y no objeto selecionado e prepara a
    base para interação por mouse na próxima etapa.
    """

    def __init__(self) -> None:
        self.axis_length = 72
        self.handle_size = 8

    def draw(self, surface: pygame.Surface, selected: Any) -> None:
        if selected is None or not hasattr(selected, "transform"):
            return

        transform = selected.transform
        pos = getattr(transform, "position", None)
        if pos is None:
            return

        cx = int(float(pos[0]))
        cy = int(float(pos[1]))
        length = self.axis_length

        # eixo X
        pygame.draw.line(surface, (230, 70, 70), (cx, cy), (cx + length, cy), 3)
        pygame.draw.polygon(
            surface,
            (230, 70, 70),
            [(cx + length + 12, cy), (cx + length, cy - 7), (cx + length, cy + 7)],
        )

        # eixo Y
        pygame.draw.line(surface, (70, 210, 90), (cx, cy), (cx, cy - length), 3)
        pygame.draw.polygon(
            surface,
            (70, 210, 90),
            [(cx, cy - length - 12), (cx - 7, cy - length), (cx + 7, cy - length)],
        )

        # centro
        pygame.draw.circle(surface, (245, 245, 245), (cx, cy), 6)
        pygame.draw.circle(surface, (15, 15, 15), (cx, cy), 6, 1)
