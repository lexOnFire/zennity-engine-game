from __future__ import annotations

from enum import Enum
from typing import Any

from engine.input import Input
from engine.runtime.input_manager import InputManager
from engine.runtime.runtime_scene import RuntimeScene


class RuntimeState(str, Enum):
    STOPPED = "stopped"
    PLAYING = "playing"


class RuntimeManager:
    """Owns the lifecycle of the isolated Play Mode world."""

    def __init__(self) -> None:
        self.state = RuntimeState.STOPPED
        self.runtime_scene: RuntimeScene | None = None
        self.input = InputManager()

    @property
    def is_playing(self) -> bool:
        return self.state == RuntimeState.PLAYING

    def start_play(self, editor_scene: Any) -> RuntimeScene:
        if self.runtime_scene is not None:
            return self.runtime_scene
        self.input.start()
        Input.bind_manager(self.input)
        self.runtime_scene = RuntimeScene(editor_scene)
        self.runtime_scene.start_runtime()
        self.state = RuntimeState.PLAYING
        return self.runtime_scene

    def tick(self, delta_time: float) -> None:
        if self.state != RuntimeState.PLAYING or self.runtime_scene is None:
            return
        self.input.update()
        self.runtime_scene.update(float(delta_time))

    def stop_play(self) -> None:
        if self.runtime_scene is not None:
            self.runtime_scene.stop_runtime()
            self.runtime_scene.destroy()
        self.runtime_scene = None
        Input.unbind_manager(self.input)
        self.input.stop()
        self.state = RuntimeState.STOPPED

    def handle_input_event(self, event: Any) -> None:
        if self.state != RuntimeState.PLAYING:
            return
        self.input.handle_event(event)
