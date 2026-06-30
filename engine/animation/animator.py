from __future__ import annotations
"""
engine/animation/animator.py
────────────────────────────

Animator — componente que gerencia clips de animação e atualiza
automaticamente o SpriteRenderer do mesmo GameObject.

Máquina de estados leve:
  - Cada estado é um AnimationClip nomeado.
  - Transições automáticas via `add_transition(from, to, condition_fn)`.
  - Transição manual via `play(name)`.
"""

from typing import Callable, Dict, List, Optional, Tuple
import pygame

from engine.component import Component
from .clip import AnimationClip


class Animator(Component):
    """
    Gerencia e toca animações, atualizando o SpriteRenderer do GameObject.

    Uso básico
    ----------
        anim = player.add_component(Animator())
        anim.add_clip(AnimationClip("idle", sheet.get_range(0, 4),  fps=6))
        anim.add_clip(AnimationClip("run",  sheet.get_range(4, 10), fps=12))
        anim.add_clip(AnimationClip("jump", sheet.get_range(10,13), fps=8, loop=False))
        anim.play("idle")

    Transições automáticas
    -----------------------
        anim.add_transition("idle", "run",  lambda: abs(rb.velocity[0]) > 10)
        anim.add_transition("run",  "idle", lambda: abs(rb.velocity[0]) < 10)
        anim.add_transition("*",    "jump", lambda: not rb.grounded)  # de qualquer estado
        anim.add_transition("jump", "idle", lambda: rb.grounded)
    """

    def __init__(self, default_clip: Optional[str] = None) -> None:
        super().__init__()
        self._clips:       Dict[str, AnimationClip]   = {}
        self._transitions: List[Tuple[str, str, Callable[[], bool]]] = []
        self._current:     Optional[AnimationClip]    = None
        self._default:     Optional[str]              = default_clip

        self._frame_index: int   = 0
        self._timer:       float = 0.0
        self._finished:    bool  = False   # True quando clip não-loop chega ao fim

        # Callback: chamado quando um clip não-loop termina
        self.on_finish: Optional[Callable[[str], None]] = None

    # ------------------------------------------------------------------
    # Ciclo de vida do Component
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._default and self._default in self._clips:
            self.play(self._default)

    # ------------------------------------------------------------------
    # API de clips
    # ------------------------------------------------------------------

    def add_clip(self, clip: AnimationClip) -> "Animator":
        """Registra um clip. Retorna self para encadeamento."""
        self._clips[clip.name] = clip
        return self

    def add_transition(
        self,
        from_state: str,
        to_state:   str,
        condition:  Callable[[], bool],
    ) -> "Animator":
        """
        Adiciona uma transição automática.

        Use "*" em `from_state` para criar uma transição global
        (qualquer estado → to_state quando condition() for True).
        Retorna self para encadeamento.
        """
        self._transitions.append((from_state, to_state, condition))
        return self

    def play(self, name: str, force: bool = False) -> None:
        """
        Troca para o clip `name`.
        Se o clip já está tocando e `force=False`, não reinicia.
        """
        if name not in self._clips:
            return
        if not force and self._current and self._current.name == name:
            return

        self._current     = self._clips[name]
        self._frame_index = 0
        self._timer       = 0.0
        self._finished    = False

        # Reseta eventos do clip
        for ev in self._current.events:
            ev.fired = False

        self._push_frame()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        # 1. Verifica transições automáticas (antes de avançar o frame)
        if self._current:
            for from_state, to_state, condition in self._transitions:
                if from_state == "*" or from_state == self._current.name:
                    if to_state != self._current.name:
                        try:
                            if condition():
                                self.play(to_state)
                                break
                        except Exception:
                            pass

        # 2. Avança o timer
        if self._current is None or self._finished:
            return

        frame_duration = 1.0 / self._current.fps
        self._timer   += dt

        while self._timer >= frame_duration:
            self._timer -= frame_duration
            self._advance_frame()
            if self._finished:
                break

    def _advance_frame(self) -> None:
        clip = self._current
        if clip is None:
            return

        next_index = self._frame_index + 1

        if next_index >= clip.frame_count:
            if clip.loop:
                next_index = 0
                # Reseta eventos para o próximo loop
                for ev in clip.events:
                    ev.fired = False
            else:
                self._finished = True
                if self.on_finish:
                    self.on_finish(clip.name)
                return

        self._frame_index = next_index
        self._push_frame()
        self._fire_events()

    def _push_frame(self) -> None:
        """Atualiza a imagem do SpriteRenderer com o frame atual."""
        if self._current is None:
            return
        frame = self._current.frames[self._frame_index]

        # Importa aqui para evitar import circular
        from engine.graphics.renderer2d import SpriteRenderer
        sr = self.game_object.get_component(SpriteRenderer) if self.game_object else None
        if sr:
            sr.image = frame

    def _fire_events(self) -> None:
        if self._current is None:
            return
        for ev in self._current.events:
            if not ev.fired and ev.frame_index == self._frame_index:
                ev.callback()
                ev.fired = True

    # ------------------------------------------------------------------
    # Consultas de estado
    # ------------------------------------------------------------------

    @property
    def current_clip(self) -> Optional[str]:
        """Nome do clip atual, ou None."""
        return self._current.name if self._current else None

    @property
    def current_frame(self) -> int:
        return self._frame_index

    @property
    def is_finished(self) -> bool:
        """True se o clip atual (não-loop) chegou ao fim."""
        return self._finished

    def is_playing(self, name: str) -> bool:
        return self._current is not None and self._current.name == name

    # ------------------------------------------------------------------
    # Draw (delega ao SpriteRenderer — Animator não desenha sozinho)
    # ------------------------------------------------------------------

    def draw(self, screen) -> None:
        pass   # SpriteRenderer cuida do draw

    def __repr__(self) -> str:
        clip = self._current.name if self._current else "None"
        return f"<Animator clip='{clip}' frame={self._frame_index}>"
