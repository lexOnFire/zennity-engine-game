from __future__ import annotations
"""
engine/ui/progress_bar.py
─────────────────────────────────────────────────────────────
ProgressBar — barra de progresso animada (HP, MP, XP, etc.).
"""

from typing import Tuple, Optional
import pygame
from .base import UIElement, Anchor, Pivot


class ProgressBar(UIElement):
    """
    Barra de progresso horizontal com animação suave.

    Parameters
    ----------
    value         : float – Valor atual  (0.0 – max_value).
    max_value     : float – Valor máximo.
    color_fill    : tuple – Cor do preenchimento.
    color_bg      : tuple – Cor do fundo da barra.
    color_border  : tuple – Cor da borda (None = sem borda).
    border_radius : int   – Arredondamento.
    smooth        : bool  – Anima a mudança de valor suavemente.
    smooth_speed  : float – Velocidade da animação (unidades/s).
    show_text     : bool  – Exibe "valor/max" no centro.
    """

    def __init__(
        self,
        x:             float = 0.0,
        y:             float = 0.0,
        width:         float = 200.0,
        height:        float = 20.0,
        value:         float = 100.0,
        max_value:     float = 100.0,
        color_fill:    Tuple = (80, 200, 100),
        color_bg:      Tuple = (40,  40,  40),
        color_border:  Optional[Tuple] = (20, 20, 20),
        border_radius: int   = 4,
        smooth:        bool  = True,
        smooth_speed:  float = 80.0,
        show_text:     bool  = False,
        font_size:     int   = 13,
        anchor: Anchor = Anchor.TOP_LEFT,
        pivot:  Pivot  = Pivot.TOP_LEFT,
        name:   str    = "",
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height,
                         anchor=anchor, pivot=pivot, name=name)
        self.value         = float(value)
        self.max_value     = float(max_value)
        self.color_fill    = color_fill
        self.color_bg      = color_bg
        self.color_border  = color_border
        self.border_radius = border_radius
        self.smooth        = smooth
        self.smooth_speed  = smooth_speed
        self.show_text     = show_text
        self.font_size     = font_size
        self._display_value = float(value)   # valor animado
        self._font: Optional[pygame.font.Font] = None

    @property
    def ratio(self) -> float:
        if self.max_value <= 0:
            return 0.0
        return max(0.0, min(1.0, self.value / self.max_value))

    def set_value(self, v: float) -> None:
        self.value = max(0.0, min(float(v), self.max_value))

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.smooth:
            diff = self.value - self._display_value
            step = self.smooth_speed * dt
            if abs(diff) <= step:
                self._display_value = self.value
            else:
                self._display_value += step * (1 if diff > 0 else -1)
        else:
            self._display_value = self.value

    def _draw_self(self, screen: pygame.Surface) -> None:
        rect = self.get_rect(screen)

        # Fundo
        pygame.draw.rect(screen, self.color_bg, rect,
                         border_radius=self.border_radius)

        # Preenchimento
        display_ratio = max(0.0, min(1.0,
            self._display_value / self.max_value if self.max_value > 0 else 0.0))
        fill_w = int(rect.width * display_ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
            pygame.draw.rect(screen, self.color_fill, fill_rect,
                             border_radius=self.border_radius)

        # Borda
        if self.color_border:
            pygame.draw.rect(screen, self.color_border, rect,
                             width=1, border_radius=self.border_radius)

        # Texto
        if self.show_text:
            if self._font is None:
                self._font = pygame.font.SysFont("sans", self.font_size)
            label = f"{int(self.value)}/{int(self.max_value)}"
            surf  = self._font.render(label, True, (220, 220, 220))
            tx = rect.x + (rect.width  - surf.get_width())  // 2
            ty = rect.y + (rect.height - surf.get_height()) // 2
            screen.blit(surf, (tx, ty))
