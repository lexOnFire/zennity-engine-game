from __future__ import annotations
"""
engine/animation/clip.py
───────────────────────────

AnimationClip  — sequencia de frames + metadata.
AnimationEvent — callback disparado em um frame específico.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
import pygame


@dataclass
class AnimationEvent:
    """
    Evento disparado quando o clip passa pelo frame `frame_index`.

    Parameters
    ----------
    frame_index : int      – Frame que dispara o evento.
    callback    : Callable – Função chamada sem argumentos.
    fired       : bool     – Controle interno — não editar.
    """
    frame_index: int
    callback:    Callable[[], None]
    fired:       bool = field(default=False, repr=False)


class AnimationClip:
    """
    Uma animação: lista de frames + FPS + configurações de loop.

    Parameters
    ----------
    name    : str                  – Nome único do clip (ex: "run", "idle").
    frames  : List[pygame.Surface] – Sequencia de surfaces.
    fps     : float                – Velocidade da animação em frames/segundo.
    loop    : bool                 – Reinicia ao chegar no último frame.
    flip_h  : bool                 – Espelha todos os frames horizontalmente.
    """

    def __init__(
        self,
        name:   str,
        frames: List[pygame.Surface],
        fps:    float = 10.0,
        loop:   bool  = True,
        flip_h: bool  = False,
    ) -> None:
        self.name   = name
        self.fps    = max(fps, 0.01)
        self.loop   = loop

        if flip_h:
            self.frames = [pygame.transform.flip(f, True, False) for f in frames]
        else:
            self.frames = list(frames)

        self._events: List[AnimationEvent] = []

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def add_event(self, frame_index: int, callback: Callable[[], None]) -> "AnimationClip":
        """
        Adiciona um callback que será disparado quando a animação
        atingir o frame `frame_index`. Retorna self para encadeamento.
        """
        self._events.append(AnimationEvent(frame_index, callback))
        return self

    @property
    def events(self) -> List[AnimationEvent]:
        return self._events

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def duration(self) -> float:
        """Duração total do clip em segundos."""
        return self.frame_count / self.fps

    def __repr__(self) -> str:
        return (
            f"<AnimationClip '{self.name}' "
            f"frames={self.frame_count} "
            f"fps={self.fps} loop={self.loop}>"
        )
