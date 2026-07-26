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

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pygame

from engine.core import Component
from engine.time import Time
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

    component_type = "Animator"
    unique = True

    def __init__(self, default_clip: Optional[str] = None, speed: float = 1.0) -> None:
        super().__init__()
        self._clips:       Dict[str, AnimationClip]   = {}
        self._transitions: List[Tuple[str, str, Callable[[], bool]]] = []
        self._current:     Optional[AnimationClip]    = None
        self._default:     Optional[str]              = default_clip

        self._frame_index: int   = 0
        self._timer:       float = 0.0
        self._finished:    bool  = False   # True quando clip não-loop chega ao fim
        self._clip_time:    float = 0.0
        self._playing:      bool  = False
        self._paused:       bool  = False
        self._runtime_animation_managed: bool = False
        self.speed:         float = float(speed)

        # Callback: chamado quando um clip não-loop termina
        self.on_finish: Optional[Callable[[str], None]] = None

    # ------------------------------------------------------------------
    # Ciclo de vida do Component
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._default and self._default in self._clips:
            self.play(self._default)

    def on_runtime_start(self) -> None:
        self._runtime_animation_managed = True
        if self._current is None and self._default and self._default in self._clips:
            self.play(self._default)

    def on_runtime_update(self, delta_time: float) -> None:
        self._advance(Time.delta_time)

    def on_runtime_stop(self) -> None:
        self._runtime_animation_managed = False

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
        self._clip_time   = 0.0
        self._finished    = False
        self._playing     = True
        self._paused      = False

        # Reseta eventos do clip
        for ev in self._current.events:
            ev.fired = False

        self._push_frame()
        self._apply_keyframe_sample()

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        if self._current is not None:
            self._paused = False
            self._playing = True

    def stop(self) -> None:
        self._playing = False
        self._paused = False
        self._finished = False
        self._clip_time = 0.0
        self._timer = 0.0
        self._frame_index = 0
        self._current = None

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self._runtime_animation_managed:
            return
        self._advance(dt)

    def _advance(self, dt: float) -> None:
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
        if self._current is None or self._finished or not self._playing or self._paused:
            return

        dt = max(0.0, float(dt)) * max(0.0, float(self.speed))
        self._advance_keyframes(dt)
        if self._current is None or self._current.frame_count <= 0:
            return

        frame_duration = 1.0 / self._current.fps
        self._timer   += dt

        while self._timer >= frame_duration:
            self._timer -= frame_duration
            self._advance_frame()
            if self._finished:
                break

    def _advance_keyframes(self, dt: float) -> None:
        clip = self._current
        if clip is None or not getattr(clip, "keyframes", None):
            return
        duration = max(float(clip.duration), 0.0)
        if duration <= 0.0:
            self._clip_time = 0.0
            self._apply_keyframe_sample()
            return

        self._clip_time += dt
        if self._clip_time >= duration:
            if clip.loop:
                self._clip_time = self._clip_time % duration
            else:
                self._clip_time = duration
                self._finished = True
                self._playing = False
                if self.on_finish:
                    self.on_finish(clip.name)
        self._apply_keyframe_sample()

    def _advance_frame(self) -> None:
        clip = self._current
        if clip is None:
            return

        next_index = self._frame_index + 1

        if next_index >= clip.frame_count:
            if clip.loop:
                next_index = 0
                self._frame_index = next_index
                self._push_frame()
                self._fire_events()
                # Reseta eventos APÓS disparar os do frame 0,
                # para que o próximo loop possa dispará-los novamente
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
        if self._current.frame_count <= 0:
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

    def _apply_keyframe_sample(self) -> None:
        if self._current is None or self.game_object is None:
            return
        sample = self._current.sample(self._clip_time)
        if not sample:
            return
        for property_name, value in sample.items():
            self._apply_animated_property(str(property_name), value)

    def _apply_animated_property(self, property_name: str, value: Any) -> None:
        if self.game_object is None:
            return
        transform = self.game_object.transform
        normalized = property_name.lower().replace("transform.", "")
        if normalized in {"position", "rotation", "scale"}:
            current = np.array(getattr(transform, normalized), dtype=np.float32)
            next_value = self._vector_value(value, current)
            setattr(transform, normalized, next_value)
            return
        if normalized in {"x", "position.x"}:
            transform.position[0] = float(value)
        elif normalized in {"y", "position.y"}:
            transform.position[1] = float(value)
        elif normalized in {"z", "position.z"}:
            transform.position[2] = float(value)
        elif normalized in {"rz", "rotation.z", "rotation.rz"}:
            transform.rotation[2] = float(value)

    def _vector_value(self, value: Any, current: np.ndarray) -> np.ndarray:
        if isinstance(value, np.ndarray):
            values = value.astype(np.float32)
        elif isinstance(value, (list, tuple)):
            values = np.array(value, dtype=np.float32)
        else:
            values = np.array([float(value)], dtype=np.float32)
        result = current.copy()
        count = min(len(result), len(values))
        result[:count] = values[:count]
        return result

    def serialize_properties(self) -> dict[str, Any]:
        return {
            "default_clip": self._default,
            "current_clip_name": self.current_clip,
            "speed": float(self.speed),
            "playing": bool(self._playing),
            "paused": bool(self._paused),
            "clip_time": float(self._clip_time),
            "clips": [clip.serialize() for clip in self._clips.values()],
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        self._default = data.get("default_clip")
        self.speed = float(data.get("speed", 1.0))
        self._playing = bool(data.get("playing", False))
        self._paused = bool(data.get("paused", False))
        self._clip_time = float(data.get("clip_time", 0.0))
        self._clips.clear()
        for clip_data in data.get("clips", []):
            if isinstance(clip_data, dict):
                clip = AnimationClip.deserialize(clip_data)
                self._clips[clip.name] = clip
        current_name = data.get("current_clip_name") or data.get("current_clip")
        if isinstance(current_name, dict):
            current_name = current_name.get("name")
        elif hasattr(current_name, "name"):
            current_name = current_name.name
        self._current = self._clips.get(current_name) if current_name else None

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

    @property
    def is_any_playing(self) -> bool:
        return self._current is not None and self._playing and not self._paused and not self._finished

    @property
    def current_time(self) -> float:
        return self._clip_time

    def is_playing(self, name: str) -> bool:
        return self._current is not None and self._current.name == name and self._playing and not self._paused

    # ------------------------------------------------------------------
    # Draw (delega ao SpriteRenderer — Animator não desenha sozinho)
    # ------------------------------------------------------------------

    def draw(self, screen) -> None:
        pass   # SpriteRenderer cuida do draw

    def __repr__(self) -> str:
        clip = self._current.name if self._current else "None"
        return f"<Animator clip='{clip}' frame={self._frame_index}>"
