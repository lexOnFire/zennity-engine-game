"""Logic event updates for the isolated viewport runtime."""
from __future__ import annotations

from typing import Any, Callable

from engine.diagnostics import get_logger, report_error

log = get_logger("logic")


class ViewportLogicEventUpdater:
    """Executes logic events and update hooks outside the frame loop."""

    def __init__(
        self,
        objects: dict[str, dict[str, Any]],
        logic_modules: dict[str, list[tuple[str, Any]]],
        logic_apis: dict[str, Any],
        animator_controllers: dict[str, Any],
        hud_entries: Any,
        normalize_ui: Callable[[Any], dict[str, Any] | None],
        play_audio: Callable[..., None],
        state_hook: Callable[[str, str, str], None],
        emit: Callable[[dict[str, Any]], None],
    ) -> None:
        self.objects = objects
        self.logic_modules = logic_modules
        self.logic_apis = logic_apis
        self.animator_controllers = animator_controllers
        self.hud_entries = hud_entries
        self.normalize_ui = normalize_ui
        self.play_audio = play_audio
        self.state_hook = state_hook
        self.emit = emit

    def update(
        self,
        input_state: dict[str, bool],
        delta_time: float,
        velocities_y: dict[str, float],
        grounded: dict[str, bool],
    ) -> bool:
        restart_requested = False
        for name, instances in list(self.logic_modules.items()):
            obj = self.objects.get(name)
            api = self.logic_apis.get(name)
            if obj is None or api is None:
                continue
            instructions = obj.pop("logic_events", [])
            api.begin_frame(input_state)
            for path, module in list(instances):
                try:
                    restart_requested = self._update_module(
                        name, obj, api, module, instructions, input_state, delta_time,
                    ) or restart_requested
                except Exception as exc:
                    # The module is detached from the running scene, so this is a
                    # gameplay-visible failure and must never be silent.
                    report_error(log, f"update logic module {name}:{path} (module detached)", exc)
                    instances.remove((path, module))
                    self.emit({
                        "type": "runtime_log", "level": "ERROR",
                        "message": f"{name}:{path}: {exc}",
                    })
            self._apply_jump(name, obj, velocities_y, grounded)
        return restart_requested

    def _update_module(
        self, name: str, obj: dict[str, Any], api: Any, module: Any,
        instructions: list[Any], input_state: dict[str, bool], delta_time: float,
    ) -> bool:
        restart_requested = False
        simple_hook = getattr(module, "on_instruction", None)
        legacy_hook = getattr(module, "isolated_on_instruction", None)
        for instruction in instructions:
            if not isinstance(instruction, dict):
                continue
            restart_requested = self._apply_instruction(name, obj, instruction) or restart_requested
            if callable(simple_hook):
                simple_hook(api, instruction)
            elif callable(legacy_hook):
                legacy_hook(obj, instruction)
        if module._zennity_update_mode == "simple":
            module._zennity_update_hook(api, delta_time)
        elif module._zennity_update_mode == "legacy":
            module._zennity_update_hook(obj, delta_time)
        else:
            module._zennity_update_hook(obj, input_state, delta_time)
        return restart_requested

    def _apply_instruction(self, name: str, obj: dict[str, Any], instruction: dict[str, Any]) -> bool:
        command, value = instruction.get("command"), instruction.get("value")
        if command == "play_animation" and value:
            self._set_animation(obj, str(value))
        elif command == "animator_play" and value:
            controller = self.animator_controllers.get(name)
            previous = controller.current_state if controller is not None else ""
            if controller is not None and controller.play(str(value)):
                self.state_hook(name, "on_animation_state_exit", previous)
                self.state_hook(name, "on_animation_state_enter", controller.current_state)
                obj["_animator_state"] = controller.current_state
                self._set_animation(obj, controller.current_state)
        elif command in {"animator_set_bool", "animator_set_float"} and isinstance(value, dict):
            controller = self.animator_controllers.get(name)
            if controller is not None:
                parameter = str(value.get("name", ""))
                if command == "animator_set_bool":
                    controller.set_bool(parameter, bool(value.get("value")))
                else:
                    controller.set_float(parameter, float(value.get("value", 0.0)))
        elif command == "animator_trigger" and value:
            controller = self.animator_controllers.get(name)
            if controller is not None:
                controller.trigger(str(value))
        elif command == "stop_animation":
            obj["_current_animation_name"] = "Nenhum"
        elif command == "play_sound" and value:
            self.play_audio(f"logic:{name}", str(value))
        elif command == "set_hud" and isinstance(value, dict):
            self.hud_entries.set_entry(dict(value))
        elif command == "remove_hud":
            self.hud_entries.remove_entry(str(value))
        elif command == "set_ui_text" and isinstance(value, dict):
            obj_name = str(value.get("object", "")).strip()
            text_val = str(value.get("text", ""))
            target = self.objects.get(obj_name)
            ui = self.normalize_ui(target.get("ui")) if target is not None else None
            if target is not None and ui is not None and ui["type"] in {"text", "button"}:
                ui["text"] = text_val
                target["ui"] = ui
            for scene_obj in self.objects.values():
                if isinstance(scene_obj, dict):
                    c_ui = scene_obj.get("ui")
                    if isinstance(c_ui, dict) and c_ui.get("type") == "canvas":
                        overrides = c_ui.setdefault("_widget_overrides", {})
                        overrides.setdefault(obj_name, {})["text"] = text_val
        elif command == "set_ui_progress" and isinstance(value, dict):
            obj_name = str(value.get("object", "")).strip()
            val_num = float(value.get("value", 0.0))
            max_num = max(0.0001, float(value.get("max_value", 100.0)))
            target = self.objects.get(obj_name)
            ui = self.normalize_ui(target.get("ui")) if target is not None else None
            if target is not None and ui is not None and str(ui.get("type", "")).lower() in {"progress_bar", "uiprogressbar"}:
                ui["value"] = val_num
                ui["max_value"] = max_num
                target["ui"] = ui
            for scene_obj in self.objects.values():
                if isinstance(scene_obj, dict):
                    c_ui = scene_obj.get("ui")
                    if isinstance(c_ui, dict) and str(c_ui.get("type", "")).lower() in {"canvas", "uicanvas"}:
                        overrides = c_ui.setdefault("_widget_overrides", {})
                        for key_alias in {obj_name, f"ui_{obj_name}", obj_name.removeprefix("ui_")}:
                            w_override = overrides.setdefault(key_alias, {})
                            w_override["value"] = val_num
                            w_override["max_value"] = max_num
                            if val_num <= 0:
                                w_override["visible"] = False
        elif command == "set_ui_visible" and isinstance(value, dict):
            obj_name = str(value.get("object", "")).strip()
            visible_bool = bool(value.get("visible", True))
            target = self.objects.get(obj_name)
            ui = self.normalize_ui(target.get("ui")) if target is not None else None
            if target is not None and ui is not None:
                ui["visible"] = visible_bool
                target["ui"] = ui
            for scene_obj in self.objects.values():
                if isinstance(scene_obj, dict):
                    c_ui = scene_obj.get("ui")
                    if isinstance(c_ui, dict) and c_ui.get("type") == "canvas":
                        overrides = c_ui.setdefault("_widget_overrides", {})
                        overrides.setdefault(obj_name, {})["visible"] = visible_bool
        return command == "restart_scene"

    @staticmethod
    def _set_animation(obj: dict[str, Any], name: str) -> None:
        obj["_current_animation_name"] = name
        obj["_animation_time"], obj["_animation_frame"], obj["_animation_raw_frame"] = 0.0, 0, -1
        animator = obj.get("animator")
        if isinstance(animator, dict):
            animator["active_clip"] = name

    @staticmethod
    def _apply_jump(name: str, obj: dict[str, Any], velocities_y: dict[str, float], grounded: dict[str, bool]) -> None:
        if obj.pop("_jump_requested", False) and grounded.get(name, False):
            velocities_y[name] = -float(obj.pop("_jump_force", 420.0))
            grounded[name] = False
            obj["_grounded"] = False
