"""Widgets de GUI para o editor — sistema visual coeso com theme.py."""
from typing import Tuple, Optional
import pygame
from . import theme as T


class GuiButton:
    """Botão retangular com hover, bordas arredondadas e suporte a ícone."""

    def __init__(
        self,
        x: int, y: int, w: int, h: int,
        text: str,
        bg_color:    Tuple[int, int, int] = T.BTN_SECONDARY,
        hover_color: Tuple[int, int, int] = T.BTN_SECONDARY_HOVER,
        text_color:  Tuple[int, int, int] = T.TEXT_PRIMARY,
        **kwargs
    ) -> None:
        self.rect        = pygame.Rect(x, y, w, h)
        self.text        = text
        self.bg_color    = kwargs.get("bg", bg_color)
        self.hover_color = kwargs.get("hover", hover_color)
        self.text_color  = text_color
        # estado interno
        self._hovered    = False

    # ------------------------------------------------------------------
    @property
    def x(self) -> int: return self.rect.x
    @x.setter
    def x(self, val: int) -> None: self.rect.x = val

    @property
    def y(self) -> int: return self.rect.y
    @y.setter
    def y(self, val: int) -> None: self.rect.y = val

    @property
    def w(self) -> int: return self.rect.width
    @w.setter
    def w(self, val: int) -> None: self.rect.width = val

    @property
    def h(self) -> int: return self.rect.height
    @h.setter
    def h(self, val: int) -> None: self.rect.height = val

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        mouse_pos   = pygame.mouse.get_pos()
        self._hovered = self.rect.collidepoint(mouse_pos)
        fill  = self.hover_color if self._hovered else self.bg_color

        # sombra sutil (1px deslocada)
        shadow = pygame.Rect(self.rect.x + 1, self.rect.y + 2,
                             self.rect.w,     self.rect.h)
        pygame.draw.rect(screen, T.BG, shadow, border_radius=5)

        # corpo
        pygame.draw.rect(screen, fill, self.rect, border_radius=5)

        # borda — mais visível no hover
        border_col = T.ACCENT_DIM if self._hovered else T.BORDER_SOFT
        pygame.draw.rect(screen, border_col, self.rect, 1, border_radius=5)

        # texto
        txt_surf = font.render(self.text, True, self.text_color)
        screen.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class SectionHeader:
    """Label de seção com linha decorativa — substitui render() avulso de título."""

    def __init__(self, x: int, y: int, w: int, text: str) -> None:
        self.x, self.y, self.w = x, y, w
        self.text = text

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        # linha horizontal esquerda
        pygame.draw.line(screen, T.BORDER,
                         (self.x, self.y + 7),
                         (self.x + 8, self.y + 7), 1)
        # texto
        surf = font.render(self.text.upper(), True, T.TEXT_MUTED)
        screen.blit(surf, (self.x + 12, self.y))
        # linha horizontal direita
        text_w = surf.get_width()
        pygame.draw.line(screen, T.BORDER,
                         (self.x + 14 + text_w, self.y + 7),
                         (self.x + self.w - 4,  self.y + 7), 1)


class Divider:
    """Linha horizontal separadora."""

    def __init__(self, x: int, y: int, w: int) -> None:
        self.x, self.y, self.w = x, y, w

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.line(screen, T.BORDER,
                         (self.x, self.y),
                         (self.x + self.w, self.y), 2)


class Badge:
    """Pill colorido de status (tag, modo ativo, etc)."""

    def __init__(self, x: int, y: int, text: str,
                 color: Tuple[int,int,int] = T.ACCENT,
                 bg: Tuple[int,int,int]    = T.ACCENT_BG) -> None:
        self.x, self.y = x, y
        self.text, self.color, self.bg = text, color, bg

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        surf = font.render(self.text, True, self.color)
        w, h = surf.get_width() + 12, surf.get_height() + 4
        rect = pygame.Rect(self.x, self.y, w, h)
        pygame.draw.rect(screen, self.bg,   rect, border_radius=10)
        pygame.draw.rect(screen, self.color, rect, 1, border_radius=10)
        screen.blit(surf, (self.x + 6, self.y + 2))
