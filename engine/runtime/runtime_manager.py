from __future__ import annotations

from enum import Enum
from typing import Any

from engine.runtime.runtime_scene import RuntimeScene


class RuntimeState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"


class RuntimeManager:
    """Owns the lifecycle of the isolated Play Mode world."""

    def __init__(self) -> None:
        self.state = RuntimeState.STOPPED
        self.runtime_scene: RuntimeScene | None = None

    @property
    def is_playing(self) -> bool:
        return self.state == RuntimeState.PLAYING

    def start_play(self, editor_scene: Any) -> RuntimeScene:
        if self.runtime_scene is not None:
            return self.runtime_scene
        self.runtime_scene = RuntimeScene(editor_scene)
        self.state = RuntimeState.PLAYING
        return self.runtime_scene

    def stop_play(self) -> None:
        if self.runtime_scene is not None:
            self.runtime_scene.destroy()
        self.runtime_scene = None
        self.state = RuntimeState.STOPPED
