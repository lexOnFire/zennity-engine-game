"""Configuration and audio commands for the isolated viewport."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ViewportControlSettings:
    active_tool: str
    view_mode: str
    snap_enabled: bool
    snap_size: float
    snap_angle: float


class ViewportControlCommandHandler:
    COMMAND_TYPES = frozenset({"set_tool", "set_view_mode", "set_snap", "runtime_input"})

    def __init__(self, forwarded_input: dict[str, bool]) -> None:
        self.forwarded_input = forwarded_input

    def handle(
        self,
        command: dict[str, Any],
        settings: ViewportControlSettings,
    ) -> ViewportControlSettings | None:
        command_type = str(command.get("type", ""))
        if command_type not in self.COMMAND_TYPES:
            return None
        values = {
            "active_tool": settings.active_tool,
            "view_mode": settings.view_mode,
            "snap_enabled": settings.snap_enabled,
            "snap_size": settings.snap_size,
            "snap_angle": settings.snap_angle,
        }
        if command_type == "set_tool":
            tool = str(command.get("tool", "select")).lower()
            if tool in {"select", "move", "rotate", "scale"}:
                values["active_tool"] = tool
        elif command_type == "set_view_mode":
            mode = str(command.get("mode", "scene")).lower()
            if mode in {"scene", "game"}:
                values["view_mode"] = mode
        elif command_type == "set_snap":
            values["snap_enabled"] = bool(command.get("enabled", False))
            values["snap_size"] = max(0.01, float(command.get("size", 16.0)))
            values["snap_angle"] = max(0.01, float(command.get("angle", 15.0)))
        elif isinstance(command.get("keys"), dict):
            for key in self.forwarded_input:
                self.forwarded_input[key] = bool(command["keys"].get(key, False))
        return ViewportControlSettings(**values)


class ViewportAudioCommandHandler:
    COMMAND_TYPES = frozenset({
        "start_play_audio", "stop_all_audio", "preview_audio", "stop_audio_preview",
    })

    def __init__(
        self,
        objects: dict[str, dict[str, Any]],
        channels: dict[str, Any],
        sounds: dict[str, Any],
        emit: Callable[[dict[str, Any]], None],
        start_sources: Callable[[], None],
        stop_sources: Callable[[], None],
        play_file: Callable[[str, str, float, bool], None],
    ) -> None:
        self.objects = objects
        self.channels = channels
        self.sounds = sounds
        self.emit = emit
        self.start_sources = start_sources
        self.stop_sources = stop_sources
        self.play_file = play_file

    def handle(self, command: dict[str, Any]) -> bool:
        command_type = str(command.get("type", ""))
        if command_type not in self.COMMAND_TYPES:
            return False
        if command_type == "start_play_audio":
            incoming = command.get("audio_sources", {})
            if isinstance(incoming, dict):
                for object_name, config in incoming.items():
                    if object_name in self.objects and isinstance(config, dict):
                        self.objects[object_name]["audio"] = dict(config)
            self.emit({"type": "script_log", "level": "INFO", "message": "Comando dedicado de áudio recebido pelo Play Mode"})
            self.start_sources()
        elif command_type == "stop_all_audio":
            self.stop_sources()
            self.emit({"type": "script_log", "level": "INFO", "message": "Todos os áudios foram interrompidos"})
        elif command_type == "preview_audio":
            self.play_file(
                "__preview__", str(command.get("path", "")),
                float(command.get("volume", 1.0)), bool(command.get("loop", False)),
            )
        else:
            channel = self.channels.pop("__preview__", None)
            if channel is not None:
                channel.stop()
            self.sounds.pop("__preview__", None)
            self.emit({"type": "script_log", "level": "INFO", "message": "Prévia de áudio interrompida"})
        return True

