from __future__ import annotations
"""
engine/ui/panel.py
─────────────────────────────────────────────────────────────
Panel — container com fundo colorido / semi-transparente.
Usado para agrupar outros widgets (HUD, menus, janelas).
"""

from typing import Optional, Tuple
import pygame
from .base import UIElement, Anchor, Pivot


class Panel(UIElement):
    """
    Container visual retangular.

    Parameters
    ----------
    color         : tuple – Fundo sólido RGBA (A controla transparência).
    border_color  : tuple – Cor da borda (None = sem borda).
    border_width  : int   – Espessura da borda.
    border_radius : int   – Arredondamento.
    blur          : bool  – Efeito de vidro fosco (faz blit de surface escurecida).
    """

    def __init__(
        self,
        x:             float = 0.0,
        y:             float = 0.0,
        width:         float = 200.0,
        height:        float = 100.0,
        color:         Tuple = (20, 20, 40, 180),
        border_color:  Optional[Tuple] = (80, 80, 120, 200),
        border_width:  int   = 1,
        border_radius: int   = 8,
        anchor: Anchor = Anchor.TOP_LEFT,
        pivot:  Pivot  = Pivot.TOP_LEFT,
        name:   str    = "",
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height,
                         anchor=anchor, pivot=pivot, name=name)
        self.color         = color
        self.border_color  = border_color
        self.border_width  = border_width
        self.border_radius = border_radius
        self._surf_cache:  Optional[pygame.Surface] = None
        self._cache_size:  Tuple[int, int] = (0, 0)

    def _draw_self(self, screen: pygame.Surface) -> None:
        rect = self.get_rect(screen)
        w, h = rect.width, rect.height
        if w <= 0 or h <= 0:
            return

        # Recria surface apenas quando o tamanho muda
        if self._surf_cache is None or self._cache_size != (w, h):
            self._surf_cache = pygame.Surface((w, h), pygame.SRCALPHA)
            self._cache_size = (w, h)

        self._surf_cache.fill((0, 0, 0, 0))

        r, g, b, a = (self.color + (255,))[:4]
        pygame.draw.rect(
            self._surf_cache,
            (r, g, b, a),
            pygame.Rect(0, 0, w, h),
            border_radius=self.border_radius,
        )

        if self.border_color:
            br, bg_, bb, ba = (self.border_color + (255,))[:4]
            pygame.draw.rect(
                self._surf_cache,
                (br, bg_, bb, ba),
                pygame.Rect(0, 0, w, h),
                width=self.border_width,
                border_radius=self.border_radius,
            )

        screen.blit(self._surf_cache, rect.topleft)
