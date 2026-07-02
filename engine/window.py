"""
Window — responsável exclusivamente pelo ciclo de vida da janela Pygame.

Responsabilidades:
  - Criar e destruir a janela (pygame.display)
  - Redimensionar / fullscreen
  - Expor `screen` (Surface) e dimensões atuais
  - Flip do display ao final do frame

Não tem conhecimento de cenas, input ou física.
"""
from __future__ import annotations
import pygame


class Window:
    """Janela do jogo. Gerenciada pela Application."""

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "Zennity Engine",
        resizable: bool = True,
    ) -> None:
        info = pygame.display.Info()
        desktop_w, desktop_h = info.current_w, info.current_h
        if width >= desktop_w or height >= desktop_h:
            width  = int(desktop_w * 0.9)
            height = int(desktop_h * 0.85)

        self._title     = title
        self._resizable = resizable
        self._saved_w   = width
        self._saved_h   = height
        self._fullscreen = False

        flags = pygame.RESIZABLE if resizable else 0
        self.screen: pygame.Surface = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption(title)

    # ------------------------------------------------------------------ #
    # Dimensões
    # ------------------------------------------------------------------ #

    @property
    def width(self) -> int:
        return self.screen.get_width()

    @property
    def height(self) -> int:
        return self.screen.get_height()

    @property
    def size(self) -> tuple[int, int]:
        return self.screen.get_size()

    # ------------------------------------------------------------------ #
    # Fullscreen
    # ------------------------------------------------------------------ #

    @property
    def is_fullscreen(self) -> bool:
        return self._fullscreen

    def toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self._saved_w, self._saved_h = self.width, self.height
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode(
                (info.current_w, info.current_h), pygame.FULLSCREEN
            )
        else:
            flags = pygame.RESIZABLE if self._resizable else 0
            self.screen = pygame.display.set_mode(
                (self._saved_w, self._saved_h), flags
            )

    # ------------------------------------------------------------------ #
    # Resize (chamado pela Application ao receber VIDEORESIZE)
    # ------------------------------------------------------------------ #

    def on_resize(self, w: int, h: int) -> None:
        """Atualiza a surface sem entrar em fullscreen."""
        if not self._fullscreen:
            flags = pygame.RESIZABLE if self._resizable else 0
            self.screen = pygame.display.set_mode((w, h), flags)

    # ------------------------------------------------------------------ #
    # Frame
    # ------------------------------------------------------------------ #

    def flip(self) -> None:
        pygame.display.flip()

    def set_title(self, title: str) -> None:
        self._title = title
        pygame.display.set_caption(title)
