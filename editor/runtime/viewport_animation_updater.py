"""Animator state, clip playback and animation-event updates."""
from __future__ import annotations

from typing import Any, Callable


class ViewportAnimationUpdater:
    def __init__(
        self, objects: dict[str, dict[str, Any]], animation_system: Any,
        controllers: dict[str, Any], event_signatures: dict[str, tuple[Any, ...]],
        logic_modules: dict[str, list[tuple[str, Any]]], api_factory: Callable[[str, dict[str, Any]], Any],
        state_hook: Callable[[str, str, str], None], emit: Callable[[dict[str, Any]], None],
    ) -> None:
        self.objects = objects
        self.animation_system = animation_system
        self.controllers = controllers
        self.event_signatures = event_signatures
        self.logic_modules = logic_modules
        self.api_factory = api_factory
        self.state_hook = state_hook
        self.emit = emit

    def update(self, delta_time: float) -> None:
        for object_name, obj in self.objects.items():
            animator = obj.get("animator")
            clips = animator.get("clips") if isinstance(animator, dict) else None
            if not isinstance(clips, dict):
                continue
            controller = self.controllers.get(object_name)
            if controller is not None:
                self._update_controller(object_name, obj, animator, clips, controller, delta_time)
            name = str(obj.get("_current_animation_name", animator.get("active_clip", "")))
            clip = clips.get(name)
            if isinstance(clip, dict):
                self._advance_clip(object_name, obj, animator, name, clip, delta_time)

    def _update_controller(self, object_name, obj, animator, clips, controller, delta_time) -> None:
        previous = controller.current_state
        if object_name not in self.event_signatures:
            self.state_hook(object_name, "on_animation_state_enter", previous)
        clip = clips.get(previous, {})
        count = max(1, int(clip.get("frame_count", 1))) if isinstance(clip, dict) else 1
        fps = max(0.01, float(clip.get("fps", 8.0))) if isinstance(clip, dict) else 8.0
        progress = float(obj.get("_animation_time", 0.0)) * fps / count
        normalized = progress % 1.0 if isinstance(clip, dict) and clip.get("loop", True) else min(1.0, progress)
        controller.update(normalized_time=normalized, delta_time=delta_time)
        animator["parameters"] = dict(controller.parameters)
        animator["active_clip"] = controller.current_state
        obj["_animator_state"] = obj["_current_animation_name"] = controller.current_state
        if controller.current_state != previous:
            self.state_hook(object_name, "on_animation_state_exit", previous)
            self.state_hook(object_name, "on_animation_state_enter", controller.current_state)
            obj["_animation_time"], obj["_animation_frame"], obj["_animation_raw_frame"] = 0.0, 0, -1
        signature = (controller.current_state, tuple(sorted((key, repr(value)) for key, value in controller.parameters.items())))
        if self.event_signatures.get(object_name) != signature:
            self.event_signatures[object_name] = signature
            self.emit({"type": "animator_state", "name": object_name, "state": controller.current_state,
                       "parameters": dict(controller.parameters), "controller_path": str(animator.get("controller_path", ""))})

    def _advance_clip(self, object_name, obj, animator, name, clip, delta_time) -> None:
        count = max(1, int(clip.get("frame_count", 1)))
        fps = max(0.01, float(clip.get("fps", 8.0))) * max(0.0, float(animator.get("speed", 1.0))) * max(0.0, float(clip.get("controller_speed", 1.0)))
        result = self.animation_system.advance(
            float(obj.get("_animation_time", 0.0)), int(obj.get("_animation_raw_frame", -1)),
            delta_time, count, fps, bool(clip.get("loop", True)),
        )
        events_by_frame: dict[int, list[dict[str, Any]]] = {}
        for event in clip.get("events", []):
            if isinstance(event, dict):
                events_by_frame.setdefault(max(0, int(event.get("frame", 0))), []).append(event)
        for frame in result.crossed_frames:
            for event in events_by_frame.get(frame, []):
                api = self.api_factory(object_name, obj)
                api.state["animation_event_payload"] = event.get("payload")
                for path, module in list(self.logic_modules.get(object_name, [])):
                    hook = getattr(module, "on_animation_event", None)
                    if not callable(hook):
                        continue
                    try:
                        hook(api, str(event.get("name", "")))
                    except Exception as exc:
                        self.emit({"type": "runtime_log", "level": "ERROR", "message": f"{object_name}:{path}:on_animation_event: {exc}"})
                self.emit({"type": "animation_event", "name": object_name, "state": name,
                           "event": str(event.get("name", "")), "frame": frame, "payload": event.get("payload")})
        obj["_animation_time"], obj["_animation_frame"], obj["_animation_raw_frame"] = result.elapsed, result.frame, result.raw_frame
