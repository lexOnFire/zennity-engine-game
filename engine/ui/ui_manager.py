from __future__ import annotations
"""
engine/ui/ui_manager.py
─────────────────────────────────────────────────────────────
UIManager — singleton que gerencia todos os canvases da cena.

Uso:
    ui = UIManager.instance()
    ui.add_canvas(hud_canvas)
    ui.add_canvas(pause_canvas)

    # Na scene:
    ui.handle_event(event, screen)
    ui.update(dt)
    ui.draw(screen)          # chamado depois do draw do mundo
"""

import pygame
from typing import List, Optional
from .canvas import UICanvas


class UIManager:
    _inst: Optional["UIManager"] = None

    def __init__(self) -> None:
        self._canvases: List[UICanvas] = []

    @classmethod
    def instance(cls) -> "UIManager":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    @classmethod
    def reset(cls) -> None:
        """Limpa o singleton — útil ao trocar de cena."""
        cls._inst = None

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    def add_canvas(self, canvas: UICanvas) -> UICanvas:
        """Registra um canvas. Mantém ordenação por z_order."""
        self._canvases.append(canvas)
        self._canvases.sort(key=lambda c: c.z_order)
        return canvas

    def remove_canvas(self, canvas: UICanvas) -> None:
        if canvas in self._canvases:
            self._canvases.remove(canvas)

    def get_canvas(self, name: str) -> Optional[UICanvas]:
        for c in self._canvases:
            if c.name == name:
                return c
        return None

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event, screen: pygame.Surface) -> bool:
        """Passa evento pelos canvases do mais alto ao mais baixo z_order."""
        for canvas in reversed(self._canvases):
            if canvas.handle_event(event, screen):
                return True
        return False

    def update(self, dt: float) -> None:
        for canvas in self._canvases:
            canvas.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Desenha todos os canvases em ordem de z_order (menor = atrás)."""
        for canvas in self._canvases:
            canvas.draw(screen)
