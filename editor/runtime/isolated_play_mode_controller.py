"""Play Mode command orchestration for the isolated editor shell."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from editor.runtime.play_session import EditorPlaySession


@dataclass(frozen=True, slots=True)
class PlayCommandPlan:
    commands: tuple[dict[str, Any], ...]
    starting: bool = False
    resuming: bool = False
    play_snapshot: tuple[dict[str, Any], ...] = ()
    audio_sources: dict[str, dict[str, Any]] | None = None


class IsolatedPlayModeController:
    """Builds deterministic IPC plans without depending on Qt widgets."""

    BLOCKED_WHILE_RUNNING = {
        "new_scene",
        "load_scene",
        "reset_from_interface",
        "move_selected",
    }

    def __init__(self, session: EditorPlaySession | None = None) -> None:
        self.session = session or EditorPlaySession()

    def blocks(self, command_type: str) -> bool:
        return self.session.is_running and command_type in self.BLOCKED_WHILE_RUNNING

    def plan(
        self,
        message: dict[str, Any],
        *,
        scene_objects: list[dict[str, Any]],
        selected_name: str | None,
        scene_blackboard: dict[str, Any] | None = None,
    ) -> PlayCommandPlan:
        command = deepcopy(message)
        command_type = str(command.get("type", ""))
        if command_type == "play":
            resuming = self.session.state == "pause"
            snapshot = self.session.begin(scene_objects, selected_name)
            if resuming:
                return PlayCommandPlan((command,), resuming=True)
            audio_sources = {
                str(obj["name"]): deepcopy(obj["audio"])
                for obj in snapshot
                if isinstance(obj.get("audio"), dict)
            }
            command["audio_sources"] = deepcopy(audio_sources)
            command["scene_blackboard"] = deepcopy(scene_blackboard or {})
            return PlayCommandPlan(
                commands=(
                    {"type": "scene_snapshot", "objects": deepcopy(snapshot)},
                    command,
                    {"type": "start_play_audio", "audio_sources": deepcopy(audio_sources)},
                ),
                starting=True,
                play_snapshot=tuple(deepcopy(snapshot)),
                audio_sources=audio_sources,
            )
        if command_type == "stop":
            return PlayCommandPlan((command, {"type": "stop_all_audio"}))
        return PlayCommandPlan((command,))
