"""Widgets simples de GUI para o editor (botões, etc)."""
from typing import Tuple
import pygame


class GuiButton:
    """Botão retangular simples com hover e bordas arredondadas."""

    def __init__(
        self,
        x: int, y: int, w: int, h: int,
        text: str,
        bg_color: Tuple[int, int, int] = (60, 70, 90),
        hover_color: Tuple[int, int, int] = (80, 95, 120),
        text_color: Tuple[int, int, int] = (240, 245, 255),
    ) -> None:
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color

    @property
    def x(self) -> int:
        return self.rect.x

    @x.setter
    def x(self, val: int) -> None:
        self.rect.x = val

    @property
    def y(self) -> int:
        return self.rect.y

    @y.setter
    def y(self, val: int) -> None:
        self.rect.y = val

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.bg_color
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        pygame.draw.rect(screen, (95, 110, 135), self.rect, 1, border_radius=4)
        txt_surf = font.render(self.text, True, self.text_color)
        screen.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )
