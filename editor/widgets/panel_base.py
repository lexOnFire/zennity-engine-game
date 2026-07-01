"""
editor/widgets/panel_base.py
============================
Classe base para painéis do editor.
Recebe um Layout e sabe se desenhar dentro de seu rect.
"""
from __future__ import annotations
import pygame
from editor.layout import Layout


class PanelBase:
    """Interface mínima que todo painel do editor deve implementar."""

    def __init__(self, layout: Layout) -> None:
        self.layout = layout

    @property
    def rect(self) -> pygame.Rect:
        """Subclasses devem retornar o rect correto do Layout."""
        raise NotImplementedError

    def on_resize(self, layout: Layout) -> None:
        """Chamado quando a janela é redimensionada. Atualiza referência."""
        self.layout = layout

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Processa evento. Retorna True se consumiu o evento."""
        return False

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        raise NotImplementedError

    # Helpers ---------------------------------------------------------------
    def _clip(self, screen: pygame.Surface):
        """Context manager que restringe o desenho ao rect do painel."""
        return _ClipContext(screen, self.rect)


class _ClipContext:
    def __init__(self, surface: pygame.Surface, rect: pygame.Rect):
        self._surface = surface
        self._rect    = rect
        self._old_clip: pygame.Rect = pygame.Rect(0, 0, 0, 0)

    def __enter__(self):
        self._old_clip = self._surface.get_clip()
        self._surface.set_clip(self._rect)
        return self._surface

    def __exit__(self, *_):
        self._surface.set_clip(self._old_clip)
