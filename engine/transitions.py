from __future__ import annotations
"""
engine/transitions.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Transições visuais entre cenas.

Cada transição tem duas fases:
  OUT  — cobre a cena atual  (progress 0.0 → 1.0)
  IN   — revela a nova cena  (progress 0.0 → 1.0)

Quando OUT termina, a SceneManager faz o swap da cena.
Quando IN termina, a transição está completa.

Transições disponíveis:
  FadeTransition       — fade para cor sólida
  SlideTransition      — desliza em 4 direções (LEFT/RIGHT/UP/DOWN)
  WipeTransition       — varredura horizontal ou vertical
  CrossfadeTransition  — cross-dissolve entre screenshots das duas cenas

Easing disponível:
  linear, ease_in, ease_out, ease_in_out
"""

import math
import pygame
from enum import Enum, auto
from typing import Optional, Tuple, Callable


# ─── Easing ───────────────────────────────────────────────────────────────────

def _linear(t: float) -> float:    return t
def _ease_in(t: float) -> float:   return t * t
def _ease_out(t: float) -> float:  return 1 - (1 - t) ** 2
def _ease_in_out(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2

EASING: dict[str, Callable[[float], float]] = {
    "linear":      _linear,
    "ease_in":     _ease_in,
    "ease_out":    _ease_out,
    "ease_in_out": _ease_in_out,
}


# ─── Base ─────────────────────────────────────────────────────────────────────

class TransitionPhase(Enum):
    OUT      = auto()   # saindo da cena atual
    SWAP     = auto()   # momento do troca (frame único)
    IN       = auto()   # entrando na nova cena
    DONE     = auto()   # concluída


class Transition:
    """
    Classe base para todas as transições.

    Parameters
    ----------
    duration_out : float  — duração da fase OUT em segundos.
    duration_in  : float  — duração da fase IN  em segundos.
    easing       : str    — nome do easing (ver EASING dict).
    """

    def __init__(
        self,
        duration_out: float = 0.35,
        duration_in:  float = 0.35,
        easing:       str   = "ease_in_out",
    ) -> None:
        self.duration_out = max(duration_out, 0.01)
        self.duration_in  = max(duration_in,  0.01)
        self._ease        = EASING.get(easing, _ease_in_out)

        self._phase:    TransitionPhase = TransitionPhase.OUT
        self._timer:    float = 0.0
        self._progress: float = 0.0   # 0.0 → 1.0 dentro da fase atual

        # Screenshots capturadas pelo SceneManager
        self.snapshot_out: Optional[pygame.Surface] = None
        self.snapshot_in:  Optional[pygame.Surface] = None

    # ── Ciclo de vida ────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._phase == TransitionPhase.DONE:
            return

        if self._phase == TransitionPhase.SWAP:
            # Fase instantânea: avança para IN no próximo update
            self._phase   = TransitionPhase.IN
            self._timer   = 0.0
            self._progress = 0.0
            return

        duration = (
            self.duration_out if self._phase == TransitionPhase.OUT
            else self.duration_in
        )
        self._timer += dt
        raw = min(1.0, self._timer / duration)
        self._progress = self._ease(raw)

        if raw >= 1.0:
            if self._phase == TransitionPhase.OUT:
                self._phase   = TransitionPhase.SWAP
                self._timer   = 0.0
                self._progress = 1.0
            else:  # IN
                self._phase   = TransitionPhase.DONE
                self._progress = 1.0

    def draw(self, screen: pygame.Surface) -> None:
        """Subclasses implementam o visual aqui."""
        pass

    # ── Queries ──────────────────────────────────────────────────────

    @property
    def is_done(self) -> bool:
        return self._phase == TransitionPhase.DONE

    @property
    def should_swap(self) -> bool:
        """True no frame exato em que a cena deve ser trocada."""
        return self._phase == TransitionPhase.SWAP

    @property
    def phase(self) -> TransitionPhase:
        return self._phase

    @property
    def progress(self) -> float:
        return self._progress


# ─── FadeTransition ───────────────────────────────────────────────────────────

class FadeTransition(Transition):
    """
    Fade-out para uma cor sólida, depois fade-in para a nova cena.

    Parameters
    ----------
    color        : tuple — cor do fade (padrão: preto).
    duration_out : float — duração do fade-out.
    duration_in  : float — duração do fade-in.
    """

    def __init__(
        self,
        color:        Tuple[int, int, int] = (0, 0, 0),
        duration_out: float = 0.35,
        duration_in:  float = 0.35,
        easing:       str   = "ease_in_out",
    ) -> None:
        super().__init__(duration_out, duration_in, easing)
        self.color = color
        self._overlay = pygame.Surface((1, 1))  # será redimensionada

    def draw(self, screen: pygame.Surface) -> None:
        if self._phase == TransitionPhase.DONE:
            return

        w, h = screen.get_size()

        if self._phase == TransitionPhase.OUT:
            # Desenha snapshot da cena antiga, depois overlay com alpha
            if self.snapshot_out:
                screen.blit(self.snapshot_out, (0, 0))
            alpha = int(self._progress * 255)
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((*self.color, alpha))
            screen.blit(overlay, (0, 0))

        elif self._phase in (TransitionPhase.SWAP, TransitionPhase.IN):
            # Desenha snapshot da nova cena, depois overlay saindo
            if self.snapshot_in:
                screen.blit(self.snapshot_in, (0, 0))
            alpha = int((1.0 - self._progress) * 255)
            if alpha > 0:
                overlay = pygame.Surface((w, h), pygame.SRCALPHA)
                overlay.fill((*self.color, alpha))
                screen.blit(overlay, (0, 0))


# ─── SlideTransition ──────────────────────────────────────────────────────────

class SlideDirection(Enum):
    LEFT  = auto()
    RIGHT = auto()
    UP    = auto()
    DOWN  = auto()


class SlideTransition(Transition):
    """
    A nova cena desliza por cima da atual.

    Parameters
    ----------
    direction    : SlideDirection — direção do deslize.
    duration_out : float          — tempo (a cena atual fica parada).
    duration_in  : float          — tempo do deslize da nova cena.
    """

    def __init__(
        self,
        direction:    SlideDirection = SlideDirection.LEFT,
        duration_out: float = 0.0,
        duration_in:  float = 0.45,
        easing:       str   = "ease_out",
    ) -> None:
        super().__init__(max(duration_out, 0.01), duration_in, easing)
        self.direction = direction

    def draw(self, screen: pygame.Surface) -> None:
        if self._phase == TransitionPhase.DONE:
            return

        w, h = screen.get_size()

        # Base: cena de saída (estática)
        if self.snapshot_out:
            screen.blit(self.snapshot_out, (0, 0))

        if self._phase in (TransitionPhase.SWAP, TransitionPhase.IN) and self.snapshot_in:
            t = self._progress
            d = self.direction
            if d == SlideDirection.LEFT:
                x = int((1 - t) * w);  y = 0
            elif d == SlideDirection.RIGHT:
                x = int(-(1 - t) * w); y = 0
            elif d == SlideDirection.UP:
                x = 0;  y = int((1 - t) * h)
            else:  # DOWN
                x = 0;  y = int(-(1 - t) * h)
            screen.blit(self.snapshot_in, (x, y))


# ─── WipeTransition ───────────────────────────────────────────────────────────

class WipeTransition(Transition):
    """
    Varredura horizontal ou vertical que revela a nova cena.

    Parameters
    ----------
    horizontal   : bool  — True = varre da esquerda; False = varre de cima.
    duration_out : float — duração da fase OUT (varredura saindo).
    duration_in  : float — duração da fase IN  (varredura entrando).
    """

    def __init__(
        self,
        horizontal:   bool  = True,
        duration_out: float = 0.30,
        duration_in:  float = 0.30,
        easing:       str   = "ease_in_out",
    ) -> None:
        super().__init__(duration_out, duration_in, easing)
        self.horizontal = horizontal

    def draw(self, screen: pygame.Surface) -> None:
        if self._phase == TransitionPhase.DONE:
            return

        w, h = screen.get_size()

        if self._phase == TransitionPhase.OUT:
            if self.snapshot_out:
                screen.blit(self.snapshot_out, (0, 0))
            # Cobre com retângulo crescente
            t = self._progress
            if self.horizontal:
                pygame.draw.rect(screen, (0, 0, 0), (0, 0, int(w * t), h))
            else:
                pygame.draw.rect(screen, (0, 0, 0), (0, 0, w, int(h * t)))

        elif self._phase in (TransitionPhase.SWAP, TransitionPhase.IN):
            # Mostra nova cena coberta por retângulo decrescente
            if self.snapshot_in:
                screen.blit(self.snapshot_in, (0, 0))
            t = 1.0 - self._progress
            if self.horizontal:
                pygame.draw.rect(screen, (0, 0, 0), (0, 0, int(w * t), h))
            else:
                pygame.draw.rect(screen, (0, 0, 0), (0, 0, w, int(h * t)))


# ─── CrossfadeTransition ──────────────────────────────────────────────────────

class CrossfadeTransition(Transition):
    """
    Cross-dissolve: blends snapshot_out → snapshot_in sem cor sólida.

    Parameters
    ----------
    duration : float — duração total do crossfade (split igual OUT/IN).
    """

    def __init__(
        self,
        duration: float = 0.50,
        easing:   str   = "ease_in_out",
    ) -> None:
        half = duration / 2.0
        super().__init__(half, half, easing)
        self._alpha_surf: Optional[pygame.Surface] = None

    def draw(self, screen: pygame.Surface) -> None:
        if self._phase == TransitionPhase.DONE:
            return

        w, h = screen.get_size()

        # Garante surface SRCALPHA com tamanho correto
        if self._alpha_surf is None or self._alpha_surf.get_size() != (w, h):
            self._alpha_surf = pygame.Surface((w, h), pygame.SRCALPHA)

        if self._phase == TransitionPhase.OUT:
            # snapshot_out some (alpha cai)
            if self.snapshot_out:
                screen.blit(self.snapshot_out, (0, 0))
            alpha = int((1.0 - self._progress) * 255)
            if self.snapshot_out and alpha < 255:
                # overlay transparente sobre o fundo preto
                screen.fill((0, 0, 0))
                self._alpha_surf.blit(self.snapshot_out, (0, 0))
                self._alpha_surf.set_alpha(alpha)
                screen.blit(self._alpha_surf, (0, 0))

        elif self._phase in (TransitionPhase.SWAP, TransitionPhase.IN):
            # snapshot_in aparece (alpha sobe)
            if self.snapshot_in:
                screen.fill((0, 0, 0))
                alpha = int(self._progress * 255)
                self._alpha_surf.blit(self.snapshot_in, (0, 0))
                self._alpha_surf.set_alpha(alpha)
                screen.blit(self._alpha_surf, (0, 0))
