from __future__ import annotations
"""
engine/ui/label.py
─────────────────────────────────────────────────────────────
Label — texto estático ou dinâmico.
"""

from typing import Optional, Tuple
import pygame
from .base import UIElement, Anchor, Pivot


class Label(UIElement):
    """
    Exibe uma string na tela.

    Parameters
    ----------
    text      : str   – Conteúdo do label.
    font_size : int   – Tamanho da fonte em pt.
    color     : tuple – Cor RGBA ou RGB.
    bold      : bool  – Negrito.
    italic    : bool  – Itálico.
    shadow    : bool  – Sombra suave atrás do texto.
    font_name : str   – Nome da fonte do sistema (None = padrão).
    """

    def __init__(
        self,
        text:      str   = "",
        x:         float = 0.0,
        y:         float = 0.0,
        font_size: int   = 20,
        color:     Tuple = (255, 255, 255),
        bold:      bool  = False,
        italic:    bool  = False,
        shadow:    bool  = False,
        font_name: Optional[str] = None,
        anchor: Anchor = Anchor.TOP_LEFT,
        pivot:  Pivot  = Pivot.TOP_LEFT,
        name:   str    = "",
    ) -> None:
        super().__init__(x=x, y=y, anchor=anchor, pivot=pivot, name=name)
        self.text      = text
        self.font_size = font_size
        self.color     = color
        self.bold      = bold
        self.italic    = italic
        self.shadow    = shadow
        self.font_name = font_name
        self._font:    Optional[pygame.font.Font] = None
        self._surface: Optional[pygame.Surface]  = None
        self._dirty    = True

    # ------------------------------------------------------------------

    def _ensure_font(self) -> None:
        if self._font is None:
            self._font = pygame.font.SysFont(
                self.font_name or "sans",
                self.font_size,
                bold=self.bold,
                italic=self.italic,
            )

    def _rebuild(self) -> None:
        self._ensure_font()
        self._surface = self._font.render(self.text, True, self.color)
        self._dirty   = False

    def set_text(self, text: str) -> None:
        if self.text != text:
            self.text  = text
            self._dirty = True

    def set_color(self, color: Tuple) -> None:
        self.color  = color
        self._dirty = True

    # ------------------------------------------------------------------
    # Natural size
    # ------------------------------------------------------------------

    def _natural_width(self, screen) -> float:
        if self._dirty or self._surface is None:
            self._rebuild()
        return self._surface.get_width()

    def _natural_height(self, screen) -> float:
        if self._dirty or self._surface is None:
            self._rebuild()
        return self._surface.get_height()

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw_self(self, screen: pygame.Surface) -> None:
        if self._dirty or self._surface is None:
            self._rebuild()
        rect = self.get_rect(screen)
        if self.shadow:
            shadow_surf = self._font.render(self.text, True, (0, 0, 0, 160))
            screen.blit(shadow_surf, (rect.x + 1, rect.y + 1))
        screen.blit(self._surface, rect.topleft)
