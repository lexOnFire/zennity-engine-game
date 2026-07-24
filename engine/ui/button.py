from __future__ import annotations
"""
engine/ui/button.py
─────────────────────────────────────────────────────────────
Button — widget clicável com estados visual (normal / hover / pressed).
"""

from typing import Callable, Optional, Tuple
import pygame
from .base import UIElement, Anchor, Pivot


class Button(UIElement):
    """
    Botão retangular com texto, animação de hover/press e callback.

    Parameters
    ----------
    text           : str      – Rótulo do botão.
    on_click       : Callable – Chamado ao soltar o botão (mouse up).
    width / height : float    – Tamanho em px; 0 = auto-fit ao texto + padding.
    color_normal   : tuple    – Cor de fundo em estado normal.
    color_hover    : tuple    – Cor de fundo em hover.
    color_pressed  : tuple    – Cor de fundo ao pressionar.
    color_text     : tuple    – Cor do texto.
    border_radius  : int      – Arredondamento das bordas.
    font_size      : int      – Tamanho da fonte.
    padding_x/y    : float    – Padding interno.
    """

    def __init__(
        self,
        text:           str   = "Button",
        x:              float = 0.0,
        y:              float = 0.0,
        width:          float = 0.0,
        height:         float = 0.0,
        on_click:       Optional[Callable[[], None]] = None,
        color_normal:   Tuple = (60,  80, 120),
        color_hover:    Tuple = (80, 110, 170),
        color_pressed:  Tuple = (40,  55,  90),
        color_disabled: Tuple = (60,  60,  60),
        color_text:     Tuple = (230, 230, 230),
        border_radius:  int   = 6,
        font_size:      int   = 18,
        font_name:      Optional[str] = None,
        padding_x:      float = 18.0,
        padding_y:      float = 10.0,
        anchor: Anchor = Anchor.TOP_LEFT,
        pivot:  Pivot  = Pivot.TOP_LEFT,
        name:   str    = "",
        enabled: bool  = True,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height,
                         anchor=anchor, pivot=pivot, name=name)
        self.text           = text
        self.on_click       = on_click
        self.color_normal   = color_normal
        self.color_hover    = color_hover
        self.color_pressed  = color_pressed
        self.color_disabled = color_disabled
        self.color_text     = color_text
        self.border_radius  = border_radius
        self.font_size      = font_size
        self.font_name      = font_name
        self.padding_x      = padding_x
        self.padding_y      = padding_y
        self.enabled        = enabled

        self._font:    Optional[pygame.font.Font] = None
        self._hovered: bool = False
        self._pressed: bool = False
        self._hover_t: float = 0.0   # lerp para animação suave

    # ------------------------------------------------------------------

    def _ensure_font(self) -> None:
        if self._font is None:
            self._font = pygame.font.SysFont(
                self.font_name or "sans", self.font_size, bold=True
            )

    def _text_size(self) -> Tuple[int, int]:
        self._ensure_font()
        return self._font.size(self.text)

    def _natural_width(self, screen) -> float:
        tw, _ = self._text_size()
        return tw + self.padding_x * 2

    def _natural_height(self, screen) -> float:
        _, th = self._text_size()
        return th + self.padding_y * 2

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event, screen: pygame.Surface) -> bool:
        if not self.visible or not self.enabled:
            return False
        # Propaga para filhos primeiro
        if super().handle_event(event, screen):
            return True

        rect = self.get_rect(screen)

        if event.type == pygame.MOUSEMOTION:
            self._hovered = rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if rect.collidepoint(event.pos):
                self._pressed = True
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and rect.collidepoint(event.pos):
                self._pressed = False
                if self.on_click:
                    self.on_click()
                return True
            self._pressed = False

        return False

    # ------------------------------------------------------------------
    # Update (animação suave de hover)
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        super().update(dt)
        target = 1.0 if self._hovered else 0.0
        speed  = 8.0
        self._hover_t += (target - self._hover_t) * min(1.0, dt * speed)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _lerp_color(self, a: Tuple, b: Tuple, t: float) -> Tuple:
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def _draw_self(self, screen: pygame.Surface) -> None:
        self._ensure_font()
        rect = self.get_rect(screen)

        if not self.enabled:
            bg = self.color_disabled
        elif self._pressed:
            bg = self.color_pressed
        else:
            bg = self._lerp_color(self.color_normal, self.color_hover, self._hover_t)

        # Fundo
        pygame.draw.rect(screen, bg, rect, border_radius=self.border_radius)

        # Borda sutil
        border_color = tuple(min(255, c + 30) for c in bg[:3])
        pygame.draw.rect(screen, border_color, rect,
                         width=1, border_radius=self.border_radius)

        # Sombra interna ao pressionar
        if self._pressed:
            inner = rect.inflate(-2, -2)
            pygame.draw.rect(screen, tuple(max(0, c-20) for c in bg[:3]),
                             inner, border_radius=max(0, self.border_radius-1))

        # Texto
        text_surf = self._font.render(self.text, True, self.color_text)
        tx = rect.x + (rect.width  - text_surf.get_width())  // 2
        ty = rect.y + (rect.height - text_surf.get_height()) // 2
        if self._pressed:  # leve deslocamento ao pressionar
            ty += 1
        screen.blit(text_surf, (tx, ty))
