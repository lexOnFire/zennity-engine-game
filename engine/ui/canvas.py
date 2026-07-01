from __future__ import annotations
"""
engine/ui/canvas.py
─────────────────────────────────────────────────────────────
UICanvas — raiz da árvore de UI.

O canvas é o nó-raiz. Todos os elementos de UI são filhos
(diretos ou indiretos) de um canvas. Pode haver múltiplos
canvases por cena (ex: HUD + PauseMenu).
"""

import pygame
from typing import List
from .base import UIElement


class UICanvas(UIElement):
    """
    Raiz da árvore de UI. Ocupa toda a tela.

    Parameters
    ----------
    name    : str  – Nome para debug.
    visible : bool – Oculta toda a árvore se False.
    z_order : int  – Canvases são desenhados em ordem crescente de z_order.
    """

    def __init__(
        self,
        name:    str  = "Canvas",
        visible: bool = True,
        z_order: int  = 0,
    ) -> None:
        super().__init__(visible=visible, name=name)
        self.z_order = z_order

    def get_rect(self, screen: pygame.Surface) -> pygame.Rect:
        """O Canvas sempre ocupa a tela inteira."""
        return screen.get_rect()

    def draw(self, screen: pygame.Surface) -> None:
        if not self.visible:
            return
        for child in self.children:
            child.draw(screen)

    def update(self, dt: float) -> None:
        if not self.visible:
            return
        for child in self.children:
            child.update(dt)

    def handle_event(self, event: pygame.event.Event, screen: pygame.Surface) -> bool:
        if not self.visible:
            return False
        for child in reversed(self.children):
            if child.handle_event(event, screen):
                return True
        return False
