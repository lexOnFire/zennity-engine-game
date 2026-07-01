from __future__ import annotations
"""
engine/ui/image.py
─────────────────────────────────────────────────────────────
UIImage — exibe uma Surface pygame como elemento de UI.
"""

from typing import Optional, Tuple
import pygame
from .base import UIElement, Anchor, Pivot


class UIImage(UIElement):
    """
    Exibe uma imagem (pygame.Surface) no canvas.

    Parameters
    ----------
    surface : pygame.Surface – Imagem a exibir.
    tint    : tuple | None   – (R,G,B,A) para colorir a imagem.
    alpha   : int            – Opacidade global 0-255.
    """

    def __init__(
        self,
        surface: Optional[pygame.Surface] = None,
        x:       float = 0.0,
        y:       float = 0.0,
        width:   float = 0.0,
        height:  float = 0.0,
        tint:    Optional[Tuple] = None,
        alpha:   int   = 255,
        anchor:  Anchor = Anchor.TOP_LEFT,
        pivot:   Pivot  = Pivot.TOP_LEFT,
        name:    str    = "",
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height,
                         anchor=anchor, pivot=pivot, name=name)
        self.surface = surface
        self.tint    = tint
        self.alpha   = alpha

    def set_surface(self, surface: pygame.Surface) -> None:
        self.surface = surface

    def _natural_width(self, screen) -> float:
        return float(self.surface.get_width())  if self.surface else 64.0

    def _natural_height(self, screen) -> float:
        return float(self.surface.get_height()) if self.surface else 64.0

    def _draw_self(self, screen: pygame.Surface) -> None:
        if self.surface is None:
            return
        rect = self.get_rect(screen)
        img  = self.surface

        # Escala se o rect difere do tamanho original
        if rect.width != img.get_width() or rect.height != img.get_height():
            img = pygame.transform.scale(img, (rect.width, rect.height))
        else:
            img = img.copy()

        if self.alpha < 255:
            img.set_alpha(self.alpha)
        if self.tint:
            img.fill(self.tint[:3], special_flags=pygame.BLEND_RGB_MULT)

        screen.blit(img, rect.topleft)
