"""
assets/scripts/animator.py
───────────────────────────────────────────────────────────────
Animador de sprites baseado em estados (idle / run / jump / etc).

Cada estado é uma lista de surface paths ou pygame.Surface carregadas.
O animator avança os frames automaticamente com base em fps.

Uso:
    anim = Animator(fps=8)
    anim.add_state("idle",  [surf_idle_1, surf_idle_2])
    anim.add_state("run",   [surf_run_1, surf_run_2, surf_run_3, surf_run_4])
    anim.set_state("idle")
    go.add_component(anim)
"""
from __future__ import annotations

from typing import Any, Dict, List

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


@ComponentRegistry.component
class Animator(Component):
    """Gerencia animações de sprite por estado."""

    def __init__(self, fps: float = 8.0) -> None:
        super().__init__()
        self.fps: float = fps
        self._states: Dict[str, List] = {}   # nome → lista de surfaces
        self._current: str = ""
        self._frame_index: int = 0
        self._elapsed: float = 0.0

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    def add_state(self, name: str, frames: List) -> None:
        """Registra uma lista de frames (pygame.Surface) para um estado."""
        self._states[name] = frames

    def set_state(self, name: str) -> None:
        """Troca para o estado *name* se for diferente do atual."""
        if name == self._current:
            return
        if name not in self._states:
            raise KeyError(f"Estado '{name}' não registrado no Animator.")
        self._current = name
        self._frame_index = 0
        self._elapsed = 0.0

    @property
    def current_frame(self):
        """Surface do frame atual, ou None se não houver estado."""
        if not self._current or self._current not in self._states:
            return None
        frames = self._states[self._current]
        if not frames:
            return None
        return frames[self._frame_index % len(frames)]

    @property
    def current_state(self) -> str:
        return self._current

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        pass

    def update(self, dt: float) -> None:
        if not self._current or self._current not in self._states:
            return
        frames = self._states[self._current]
        if not frames:
            return

        self._elapsed += dt
        frame_duration = 1.0 / max(self.fps, 0.01)
        while self._elapsed >= frame_duration:
            self._elapsed -= frame_duration
            self._frame_index = (self._frame_index + 1) % len(frames)

    def draw(self, screen) -> None:
        frame = self.current_frame
        if frame is None:
            return
        pos = (int(self.transform.x), int(self.transform.y))
        screen.blit(frame, pos)

    # ------------------------------------------------------------------ #
    # Serialização (salva apenas config — surfaces não são serializadas)
    # ------------------------------------------------------------------ #

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data["fps"] = self.fps
        data["current_state"] = self._current
        data["frame_index"] = self._frame_index
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.fps = float(data.get("fps", 8.0))
        self._current = data.get("current_state", "")
        self._frame_index = int(data.get("frame_index", 0))
