from __future__ import annotations
"""
engine/ui/base.py
─────────────────────────────────────────────────────────────

UIElement — classe base de todos os widgets de UI.

Coordenadas em Screen Space (pixels, origem top-left).
Suporte a Anchor (onde o elemento se ancora na tela/pai)
e Pivot (ponto de referência do próprio elemento).
"""

from enum import Enum, auto
from typing import List, Optional, Tuple
import pygame


class Anchor(Enum):
    """Ponto de ancoragem relativo ao container pai (ou tela)."""
    TOP_LEFT      = auto()
    TOP_CENTER    = auto()
    TOP_RIGHT     = auto()
    MIDDLE_LEFT   = auto()
    MIDDLE_CENTER = auto()
    MIDDLE_RIGHT  = auto()
    BOTTOM_LEFT   = auto()
    BOTTOM_CENTER = auto()
    BOTTOM_RIGHT  = auto()


class Pivot(Enum):
    """Ponto de origem do próprio elemento (onde x/y apontam)."""
    TOP_LEFT      = auto()
    TOP_CENTER    = auto()
    TOP_RIGHT     = auto()
    MIDDLE_LEFT   = auto()
    MIDDLE_CENTER = auto()
    MIDDLE_RIGHT  = auto()
    BOTTOM_LEFT   = auto()
    BOTTOM_CENTER = auto()
    BOTTOM_RIGHT  = auto()


# Fatores (fx, fy) para cada enum — multiplicam (container_w, container_h)
_ANCHOR_FACTORS = {
    Anchor.TOP_LEFT:      (0.0, 0.0), Anchor.TOP_CENTER:    (0.5, 0.0),
    Anchor.TOP_RIGHT:     (1.0, 0.0), Anchor.MIDDLE_LEFT:   (0.0, 0.5),
    Anchor.MIDDLE_CENTER: (0.5, 0.5), Anchor.MIDDLE_RIGHT:  (1.0, 0.5),
    Anchor.BOTTOM_LEFT:   (0.0, 1.0), Anchor.BOTTOM_CENTER: (0.5, 1.0),
    Anchor.BOTTOM_RIGHT:  (1.0, 1.0),
}
_PIVOT_FACTORS = {
    Pivot.TOP_LEFT:      (0.0, 0.0), Pivot.TOP_CENTER:    (0.5, 0.0),
    Pivot.TOP_RIGHT:     (1.0, 0.0), Pivot.MIDDLE_LEFT:   (0.0, 0.5),
    Pivot.MIDDLE_CENTER: (0.5, 0.5), Pivot.MIDDLE_RIGHT:  (1.0, 0.5),
    Pivot.BOTTOM_LEFT:   (0.0, 1.0), Pivot.BOTTOM_CENTER: (0.5, 1.0),
    Pivot.BOTTOM_RIGHT:  (1.0, 1.0),
}


class UIElement:
    """
    Elemento base da UI.

    Parameters
    ----------
    x, y     : offset relativo ao ponto de âncora do container.
    width    : largura em pixels (0 = auto, calculado pelo widget filho).
    height   : altura em pixels (0 = auto).
    anchor   : ponto de ancoragem no container.
    pivot    : ponto de origem do próprio widget.
    visible  : se False, não é desenhado nem recebe eventos.
    name     : nome opcional para debug.
    """

    def __init__(
        self,
        x:       float = 0.0,
        y:       float = 0.0,
        width:   float = 0.0,
        height:  float = 0.0,
        anchor:  Anchor = Anchor.TOP_LEFT,
        pivot:   Pivot  = Pivot.TOP_LEFT,
        visible: bool   = True,
        name:    str    = "",
    ) -> None:
        self.x       = x
        self.y       = y
        self.width   = width
        self.height  = height
        self.anchor  = anchor
        self.pivot   = pivot
        self.visible = visible
        self.name    = name

        self.parent:   Optional["UIElement"] = None
        self.children: List["UIElement"]     = []

    # ------------------------------------------------------------------
    # Hierarquia
    # ------------------------------------------------------------------

    def add_child(self, child: "UIElement") -> "UIElement":
        """Adiciona um filho. Retorna o filho para encadeamento."""
        child.parent = self
        self.children.append(child)
        return child

    def remove_child(self, child: "UIElement") -> None:
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    # ------------------------------------------------------------------
    # Geometria
    # ------------------------------------------------------------------

    def _get_container_rect(self, screen: pygame.Surface) -> pygame.Rect:
        """Retorna o rect do container (pai ou tela)."""
        if self.parent:
            return self.parent.get_rect(screen)
        return screen.get_rect()

    def get_rect(self, screen: pygame.Surface) -> pygame.Rect:
        """Calcula e retorna o pygame.Rect absoluto deste elemento."""
        container = self._get_container_rect(screen)
        cw, ch    = container.width, container.height

        # Ponto de âncora no container
        af = _ANCHOR_FACTORS[self.anchor]
        ax = container.x + af[0] * cw
        ay = container.y + af[1] * ch

        # Dimensões do elemento
        w = self.width  if self.width  > 0 else self._natural_width(screen)
        h = self.height if self.height > 0 else self._natural_height(screen)

        # Offset de pivot
        pf = _PIVOT_FACTORS[self.pivot]
        px = pf[0] * w
        py = pf[1] * h

        left = int(ax + self.x - px)
        top  = int(ay + self.y - py)
        return pygame.Rect(left, top, int(w), int(h))

    def _natural_width(self, screen: pygame.Surface) -> float:
        """Largura intrínseca — subclasses podem sobrescrever."""
        return 100.0

    def _natural_height(self, screen: pygame.Surface) -> float:
        """Altura intrínseca — subclasses podem sobrescrever."""
        return 30.0

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event, screen: pygame.Surface) -> bool:
        """
        Processa um evento pygame. Retorna True se consumido
        (para que elementos abaixo não o recebam).
        """
        if not self.visible:
            return False
        for child in reversed(self.children):
            if child.handle_event(event, screen):
                return True
        return False

    def update(self, dt: float) -> None:
        if not self.visible:
            return
        for child in self.children:
            child.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.visible:
            return
        self._draw_self(screen)
        for child in self.children:
            child.draw(screen)

    def _draw_self(self, screen: pygame.Surface) -> None:
        """Subclasses implementam o próprio visual aqui."""
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def contains_point(self, point: Tuple[int, int], screen: pygame.Surface) -> bool:
        return self.get_rect(screen).collidepoint(point)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' {self.width}x{self.height}>"
