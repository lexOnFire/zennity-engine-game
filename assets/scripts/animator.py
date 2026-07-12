from __future__ import annotations

from typing import Any, Dict, List

from engine.core.component import Component
from engine.component_registry import ComponentRegistry


SCRIPT_CONFIG = {"fps": 8.0, "frame_count": 4}


def on_update(game, dt):
    """Avança um índice de animação armazenado em game.state."""
    elapsed = float(game.state.get("animation_elapsed", 0.0)) + dt
    frame_time = 1.0 / max(float(SCRIPT_CONFIG["fps"]), 0.01)
    if elapsed >= frame_time:
        elapsed %= frame_time
        count = max(1, int(SCRIPT_CONFIG["frame_count"]))
        game.state["animation_frame"] = (int(game.state.get("animation_frame", 0)) + 1) % count
    game.state["animation_elapsed"] = elapsed


@ComponentRegistry.component
class Animator(Component):
    """Gerencia animações de sprite por estado."""

    def __init__(self, fps: float = 8.0) -> None:
        super().__init__()
        self.fps = float(fps)
        self._states: Dict[str, List] = {}
        self._current = ""
        self._frame_index = 0
        self._elapsed = 0.0

    def add_state(self, name: str, frames: List) -> None:
        self._states[str(name)] = frames

    def set_state(self, name: str) -> None:
        if name == self._current:
            return
        if name not in self._states:
            raise KeyError(f"Estado '{name}' não registrado no Animator.")
        self._current = str(name)
        self._frame_index = 0
        self._elapsed = 0.0

    @property
    def current_frame(self):
        frames = self._states.get(self._current, [])
        return None if not frames else frames[self._frame_index % len(frames)]

    @property
    def current_state(self) -> str:
        return self._current

    def update(self, dt: float) -> None:
        frames = self._states.get(self._current, [])
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
        screen.blit(frame, (int(self.transform.x), int(self.transform.y)))

    def serialize(self) -> Dict[str, Any]:
        data = super().serialize()
        data.update({"fps": self.fps, "current_state": self._current, "frame_index": self._frame_index})
        return data

    def deserialize(self, data: Dict[str, Any]) -> None:
        super().deserialize(data)
        self.fps = float(data.get("fps", 8.0))
        self._current = str(data.get("current_state", ""))
        self._frame_index = int(data.get("frame_index", 0))
