"""Fachada do Play Mode usada pelo editor, independente da UI."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from editor.runtime.play_session import EditorPlaySession


@dataclass(frozen=True, slots=True)
class PlayModeResult:
    objects: list[dict[str, Any]]
    selected_name: str | None


class PlayModeController:
    def __init__(self, viewport: Any, session: EditorPlaySession | None = None) -> None:
        self.viewport = viewport
        self.session = session or EditorPlaySession()

    @property
    def state(self) -> str:
        return self.session.state

    @property
    def is_running(self) -> bool:
        return self.session.is_running

    def play(self, objects: list[dict[str, Any]], selected_name: str | None, **runtime_data: Any) -> PlayModeResult:
        result = self.begin(objects, selected_name)
        self.viewport.send("play", objects=result.objects, **runtime_data)
        return result

    def begin(self, objects: list[dict[str, Any]], selected_name: str | None) -> PlayModeResult:
        snapshot = self.session.begin(objects, selected_name)
        return PlayModeResult(snapshot, selected_name)

    def set_runtime_state(self, state: str) -> None:
        self.session.set_runtime_state(state)

    def pause(self) -> None:
        if not self.is_running:
            return
        next_state = "play" if self.state == "pause" else "pause"
        self.session.set_runtime_state(next_state)
        self.viewport.send("pause", paused=next_state == "pause")

    def stop(self) -> PlayModeResult:
        result = self.finish()
        self.viewport.send("stop")
        return result

    def finish(self) -> PlayModeResult:
        objects, selected = self.session.finish()
        return PlayModeResult(objects, selected)

    def accept_runtime_snapshot(self, objects: list[dict[str, Any]]) -> PlayModeResult:
        restored, selected = self.session.consume_scene_snapshot(objects)
        return PlayModeResult(restored, selected)
