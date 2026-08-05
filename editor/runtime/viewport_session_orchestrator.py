"""Logic, behavior and lifecycle orchestration for isolated Play Mode."""
from __future__ import annotations

import time
from copy import deepcopy
from typing import Any, Callable


class ViewportSessionOrchestrator:
    def __init__(
        self, objects: dict[str, dict[str, Any]], logic_runtimes: dict[str, list[tuple[str, Any]]],
        behavior_runners: dict[str, Any], logic_modules: dict[str, Any], logic_apis: dict[str, Any],
        animator_controllers: dict[str, Any], logic_event_bus: Callable[[], Any], runtime_world: Any,
        hud_entries: Any, emit: Callable[[dict[str, Any]], None], play_audio: Callable[..., None],
        pause_audio: Callable[[bool], None], state_hook: Callable[[str, str, str], None],
    ) -> None:
        self.objects = objects
        self.logic_runtimes = logic_runtimes
        self.behavior_runners = behavior_runners
        self.logic_modules = logic_modules
        self.logic_apis = logic_apis
        self.animator_controllers = animator_controllers
        self.logic_event_bus = logic_event_bus
        self.runtime_world = runtime_world
        self.hud_entries = hud_entries
        self.emit = emit
        self.play_audio = play_audio
        self.pause_audio = pause_audio
        self.state_hook = state_hook

    def update_logic(
        self, input_state: dict[str, bool], delta_time: float, last_trace: float,
        velocities_y: dict[str, float], grounded: dict[str, bool], restart_requested: bool,
    ) -> tuple[float, bool, bool]:
        now = time.monotonic()
        trace_due = now - last_trace >= 0.10
        pause_requested = False
        event_bus = self.logic_event_bus()
        for name, runtimes in list(self.logic_runtimes.items()):
            obj, api = self.objects.get(name), self.logic_apis.get(name)
            if obj is None or api is None or not obj.get("active", True):
                continue
            api.begin_frame(input_state)
            for graph_path, runtime in list(runtimes):
                try:
                    runtime.update(api, delta_time)
                    if event_bus.dispatch():
                        pause_requested = self._emit_event_traces() or pause_requested
                    if runtime.debug_paused or trace_due:
                        pause_requested = pause_requested or runtime.debug_paused
                        self._emit_trace(name, graph_path, runtime)
                except Exception as exc:
                    self._emit_trace(name, graph_path, runtime, exc)
                    runtimes.remove((graph_path, runtime))
                    self.emit({"type": "runtime_log", "level": "ERROR", "message": f"{name}:{graph_path}: {exc}"})
            restart_requested = self._apply_logic_instructions(name, obj) or restart_requested
            self._apply_jump(name, obj, velocities_y, grounded)
        if trace_due:
            last_trace = now
        if pause_requested:
            self.pause_audio(True)
            self.emit({"type": "play_state", "state": "pause"})
        return last_trace, pause_requested, restart_requested

    def update_behaviors(self, input_state: dict[str, bool], delta_time: float, last_trace: float = 0.0) -> tuple[float, bool]:
        import time
        now = time.monotonic()
        trace_due = now - last_trace >= 0.10
        pause_requested = False
        for name, runner in list(self.behavior_runners.items()):
            obj, api = self.objects.get(name), self.logic_apis.get(name)
            if obj is None or api is None or not obj.get("active", True):
                continue
            if name not in self.logic_modules:
                api.begin_frame(input_state)
            previous = runner.current_state
            try:
                changed = runner.update(api, delta_time)
                obj["_behavior_state"] = runner.current_state
                behavior = obj.get("behavior")
                if isinstance(behavior, dict):
                    behavior["parameters"] = dict(runner.parameters)
                if changed:
                    self.emit({"type": "runtime_log", "level": "INFO", "message": f"{name}: Behavior {previous} → {runner.current_state}"})
                if trace_due:
                    graph_path = getattr(runner, "_active_path", getattr(runner, "graph_path", "Behavior Tree"))
                    self._emit_trace(name, str(graph_path), runner)
            except Exception as exc:
                self.behavior_runners.pop(name, None)
                self.emit({"type": "runtime_log", "level": "ERROR", "message": f"{name}: Behavior Controller: {exc}"})
        if trace_due:
            last_trace = now
        return last_trace, pause_requested

    def finish_frame(self, delta_time: float, velocities_y: dict[str, float], grounded: dict[str, bool]) -> None:
        for api in self.logic_apis.values():
            api.end_frame()
        for destroyed_name in self.runtime_world.update_lifecycle(delta_time):
            velocities_y.pop(destroyed_name, None)
            grounded.pop(destroyed_name, None)

    def restart(
        self, edit_snapshot: dict[str, dict[str, Any]], velocities_y: dict[str, float],
        grounded: dict[str, bool], active_contacts: dict[Any, Any],
        stop_audio: Callable[[], None], stop_logic: Callable[[], None],
        reset_physics: Callable[[], None], start_logic: Callable[[], None], start_audio: Callable[[], None],
    ) -> None:
        stop_audio()
        stop_logic()
        self.objects.clear()
        self.objects.update(deepcopy(edit_snapshot))
        velocities_y.clear(); grounded.clear(); active_contacts.clear(); self.hud_entries.clear()
        reset_physics(); start_logic(); start_audio()

    def _apply_logic_instructions(self, name: str, obj: dict[str, Any]) -> bool:
        restart = False
        for instruction in obj.pop("logic_events", []):
            if not isinstance(instruction, dict):
                continue
            command, value = instruction.get("command"), instruction.get("value")
            if command == "animator_play" and value:
                controller = self.animator_controllers.get(name)
                if controller is not None and controller.play(str(value)):
                    obj["_animator_state"] = obj["_current_animation_name"] = controller.current_state
                    obj["_animation_time"], obj["_animation_frame"], obj["_animation_raw_frame"] = 0.0, 0, -1
            elif command == "play_sound" and value:
                self.play_audio(f"logic:{name}", str(value))
            elif command == "set_hud" and isinstance(value, dict):
                self.hud_entries.set_entry(dict(value))
            elif command == "remove_hud":
                self.hud_entries.remove_entry(str(value))
            elif command == "set_ui_text" and isinstance(value, dict):
                target = self.objects.get(str(value.get("object", "")))
                ui = target.get("ui") if isinstance(target, dict) else None
                if isinstance(ui, dict) and ui.get("type") in {"text", "button"}:
                    ui["text"] = str(value.get("text", ""))
            elif command == "set_ui_progress" and isinstance(value, dict):
                target = self.objects.get(str(value.get("object", "")))
                ui = target.get("ui") if isinstance(target, dict) else None
                if isinstance(ui, dict) and ui.get("type") == "progress_bar":
                    ui["value"] = float(value.get("value", 0.0))
                    ui["max_value"] = max(0.0001, float(value.get("max_value", 100.0)))
            elif command == "restart_scene":
                restart = True
            elif command:
                # UI buttons and other runtime producers use their command name
                # as a first-class custom event for Visual Logic graphs.
                self.logic_event_bus().emit(str(command), value, name)
        return restart

    @staticmethod
    def _apply_jump(name, obj, velocities_y, grounded) -> None:
        if obj.pop("_jump_requested", False) and grounded.get(name, False):
            velocities_y[name] = -float(obj.pop("_jump_force", 420.0))
            grounded[name] = False
            obj["_grounded"] = False

    def _emit_event_traces(self) -> bool:
        paused = False
        for name, runtimes in self.logic_runtimes.items():
            for path, runtime in runtimes:
                if runtime.consume_event_trace():
                    paused = paused or runtime.debug_paused
                    self._emit_trace(name, path, runtime)
        return paused

    def _emit_trace(self, name: str, path: str, runtime: Any, error: Exception | None = None) -> None:
        event = {"type": "logic_trace", "object": name, "graph": path, **runtime.debug_snapshot()}
        if error is not None:
            event["error"] = str(error)
        self.emit(event)
