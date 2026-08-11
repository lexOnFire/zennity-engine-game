"""Play-session and debugger commands for the isolated viewport."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from engine.diagnostics import get_logger, report_error

log = get_logger("logic")


@dataclass
class ViewportProcessState:
    running: bool
    screen: Any
    camera_x: float
    camera_y: float
    edit_snapshot: dict[str, dict[str, Any]]
    selected_name: str | None
    playing: bool
    paused: bool
    velocities_y: dict[str, float]
    grounded: dict[str, bool]
    scene_blackboard_config: dict[str, Any]


class ViewportPlayCommandHandler:
    COMMAND_TYPES = frozenset({
        "shutdown", "viewport_size", "scene_snapshot", "logic_debug_command",
        "play", "pause", "stop", "logic_hot_reload",
    })

    def __init__(
        self,
        objects: dict[str, dict[str, Any]],
        logic_runtimes: dict[str, list[tuple[str, Any]]],
        logic_apis: dict[str, Any],
        emit: Callable[[dict[str, Any]], None],
        resize: Callable[[int, int], Any],
        zoom: Callable[[], float],
        pause_audio: Callable[[bool], None],
        stop_audio: Callable[[], None],
        reset_physics: Callable[[], None],
        clear_hud: Callable[[], None],
        start_logic: Callable[[dict[str, Any]], None],
        start_audio: Callable[[], None],
        stop_logic: Callable[[], None],
    ) -> None:
        self.objects = objects
        self.logic_runtimes = logic_runtimes
        self.logic_apis = logic_apis
        self.emit = emit
        self.resize = resize
        self.zoom = zoom
        self.pause_audio = pause_audio
        self.stop_audio = stop_audio
        self.reset_physics = reset_physics
        self.clear_hud = clear_hud
        self.start_logic = start_logic
        self.start_audio = start_audio
        self.stop_logic = stop_logic

    def handle(self, command: dict[str, Any], state: ViewportProcessState) -> ViewportProcessState | None:
        command_type = str(command.get("type", ""))
        if command_type not in self.COMMAND_TYPES:
            return None
        if command_type == "shutdown":
            state.running = False
        elif command_type == "viewport_size":
            width = max(32, int(command.get("w", 32)))
            height = max(32, int(command.get("h", 32)))
            state.screen = self.resize(width, height)
            zoom = self.zoom()
            state.camera_x = -float(width) / 2.0 / zoom
            state.camera_y = -float(height) / 2.0 / zoom
        elif command_type == "scene_snapshot":
            new_objects = command.get("objects", [])
            if not state.playing:
                self.objects.clear()
                self.objects.update({item["name"]: dict(item) for item in new_objects})
                state.edit_snapshot = deepcopy(self.objects)
                state.selected_name = None
                state.playing = False
                state.paused = False
                state.velocities_y = {}
                state.grounded = {}
            else:
                self.stop_audio()
                self.stop_logic()
                self.objects.clear()
                self.objects.update({item["name"]: dict(item) for item in new_objects})
                state.edit_snapshot = deepcopy(self.objects)
                state.selected_name = None
                state.velocities_y = {}
                state.grounded = {}
                self.reset_physics()
                self.clear_hud()
                self.start_logic(state.scene_blackboard_config)
                self.start_audio()
        elif command_type == "logic_debug_command":
            self._handle_logic_debug(command, state)
        elif command_type == "play":
            self._play(command, state)
        elif command_type == "pause":
            if state.playing:
                state.paused = not state.paused
                self.pause_audio(state.paused)
                self.emit({"type": "play_state", "state": "pause" if state.paused else "play"})
        elif command_type == "stop":
            self.stop_audio()
            if state.playing:
                self.stop_logic()
                self.objects.clear()
                self.objects.update(deepcopy(state.edit_snapshot))
                state.playing = False
                state.paused = False
                state.velocities_y = {}
                state.grounded = {}
                self.reset_physics()
                self.clear_hud()
                self.emit({"type": "play_state", "state": "edit"})
                self.emit({"type": "scene_snapshot", "objects": list(self.objects.values())})
        elif command_type == "logic_hot_reload":
            self._handle_logic_hot_reload(command, state)
        return state

    def _play(self, command: dict[str, Any], state: ViewportProcessState) -> None:
        if not state.playing:
            incoming_blackboard = command.get("scene_blackboard", {})
            if isinstance(incoming_blackboard, dict):
                state.scene_blackboard_config = deepcopy(incoming_blackboard)
            incoming_audio = command.get("audio_sources", {})
            if isinstance(incoming_audio, dict):
                for object_name, audio_config in incoming_audio.items():
                    if object_name in self.objects and isinstance(audio_config, dict):
                        self.objects[object_name]["audio"] = dict(audio_config)
            state.edit_snapshot = deepcopy(self.objects)
            state.playing = True
            state.paused = False
            state.velocities_y = {}
            state.grounded = {}
            self.reset_physics()
            self.clear_hud()
            self.start_logic(state.scene_blackboard_config)
            self.start_audio()
            self.emit({"type": "play_state", "state": "play"})
        elif state.paused:
            state.paused = False
            self.pause_audio(False)
            self.emit({"type": "play_state", "state": "play"})

    def _handle_logic_debug(self, command: dict[str, Any], state: ViewportProcessState) -> None:
        requested_graph = Path(str(command.get("graph", ""))).as_posix().casefold()
        requested_name = Path(requested_graph).name.casefold()
        action = str(command.get("command", "sync")).lower()
        breakpoints = command.get("breakpoints", [])
        conditions = command.get("breakpoint_conditions", {})
        watches = command.get("watches", [])
        variables = command.get("variables", {})
        matched: list[tuple[str, str, Any]] = []
        for object_name, runtimes in self.logic_runtimes.items():
            for graph_path, runtime in runtimes:
                current = Path(str(graph_path)).as_posix().casefold()
                if current == requested_graph or Path(current).name.casefold() == requested_name:
                    runtime.configure_breakpoints(
                        breakpoints if isinstance(breakpoints, list) else [],
                        conditions if isinstance(conditions, dict) else {},
                        watches if isinstance(watches, list) else [],
                    )
                    if isinstance(variables, dict):
                        runtime.configure_variables(variables)
                    matched.append((object_name, graph_path, runtime))
        if action == "continue" and matched:
            for _object_name, _graph_path, runtime in matched:
                runtime.continue_execution()
            state.paused = False
            self.pause_audio(False)
            self.emit({"type": "play_state", "state": "play"})
        elif action == "step" and matched:
            for object_name, graph_path, runtime in matched:
                try:
                    runtime.step()
                    self._emit_trace(object_name, graph_path, runtime)
                except Exception as exc:
                    report_error(log, f"single-step Logic Graph {object_name}:{graph_path}", exc)
                    self._emit_trace(object_name, graph_path, runtime, exc)
                    self.emit({"type": "runtime_log", "level": "ERROR", "message": f"{object_name}:{graph_path}: {exc}"})
            state.paused = True
            self.pause_audio(True)
        elif action == "restart" and matched:
            any_paused = False
            for object_name, graph_path, runtime in matched:
                api = self.logic_apis.get(object_name)
                if api is None:
                    continue
                try:
                    runtime.restart(api)
                    any_paused = any_paused or runtime.debug_paused
                    self._emit_trace(object_name, graph_path, runtime)
                except Exception as exc:
                    report_error(log, f"restart Logic Graph {object_name}:{graph_path}", exc)
                    self._emit_trace(object_name, graph_path, runtime, exc)
            state.paused = any_paused
            self.pause_audio(state.paused)
            self.emit({"type": "play_state", "state": "pause" if state.paused else "play"})

    def _handle_logic_hot_reload(self, command: dict[str, Any], state: ViewportProcessState) -> None:
        import json
        if not state.playing:
            return
        path = command.get("path", "")
        content = command.get("content", "")
        if not path or not content:
            return
        try:
            graph_data = json.loads(content)
            requested_graph = Path(str(path)).as_posix().casefold()
            for object_name, runtimes in self.logic_runtimes.items():
                for graph_path, runtime in runtimes:
                    current = Path(str(graph_path)).as_posix().casefold()
                    if current == requested_graph:
                        runtime.hot_reload(graph_data)
        except Exception as exc:
            report_error(log, f"hot-reload Logic Graph {path}", exc)
            self.emit({
                "type": "runtime_log", "level": "ERROR",
                "message": f"Logic Hot Reload failed: {exc}",
            })

    def _emit_trace(self, object_name: str, graph_path: str, runtime: Any, error: Exception | None = None) -> None:
        event = {"type": "logic_trace", "object": object_name, "graph": graph_path, **runtime.debug_snapshot()}
        if error is not None:
            event["error"] = str(error)
        self.emit(event)
