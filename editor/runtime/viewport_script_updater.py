"""Legacy Python-script updates for the isolated viewport runtime."""
from __future__ import annotations

from typing import Any, Callable


class ViewportScriptUpdater:
    """Execute script instructions and update hooks outside the frame loop."""

    def __init__(
        self,
        objects: dict[str, dict[str, Any]],
        script_instances: dict[str, list[tuple[str, Any]]],
        script_apis: dict[str, Any],
        animator_controllers: dict[str, Any],
        hud_entries: Any,
        normalize_ui: Callable[[Any], dict[str, Any] | None],
        play_audio: Callable[..., None],
        state_hook: Callable[[str, str, str], None],
        emit: Callable[[dict[str, Any]], None],
    ) -> None:
        self.objects = objects
        self.script_instances = script_instances
        self.script_apis = script_apis
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
        for name, instances in list(self.script_instances.items()):
            obj = self.objects.get(name)
            api = self.script_apis.get(name)
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
            self.play_audio(f"script:{name}", str(value))
        elif command == "set_hud" and isinstance(value, dict):
            self.hud_entries.set_entry(dict(value))
        elif command == "remove_hud":
            self.hud_entries.remove_entry(str(value))
        elif command == "set_ui_text" and isinstance(value, dict):
            target = self.objects.get(str(value.get("object", "")))
            ui = self.normalize_ui(target.get("ui")) if target is not None else None
            if target is not None and ui is not None and ui["type"] in {"text", "button"}:
                ui["text"] = str(value.get("text", ""))
                target["ui"] = ui
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
