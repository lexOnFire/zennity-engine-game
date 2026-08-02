"""Selection and transform-gizmo events for the isolated viewport."""
from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable


try:
    from editor.runtime.viewport_render_order import sort_objects_for_hit_testing
except ModuleNotFoundError:
    from .viewport_render_order import sort_objects_for_hit_testing


@dataclass
class ViewportTransformState:
    dragging: bool
    selected_name: str | None
    drag_start_mouse: tuple[float, float]
    drag_start_object: dict[str, Any] = field(default_factory=dict)
    drag_handle: int = -1
    move_axis: str = ""


class ViewportTransformEventHandler:
    def __init__(
        self,
        pygame: Any,
        objects: dict[str, dict[str, Any]],
        emit: Callable[[dict[str, Any]], None],
        world_to_screen: Callable[[float, float], tuple[float, float]],
    ) -> None:
        self.pygame = pygame
        self.objects = objects
        self.emit = emit
        self.world_to_screen = world_to_screen

    def handle(
        self,
        event: Any,
        state: ViewportTransformState,
        *,
        playing: bool,
        view_mode: str,
        active_tool: str,
        zoom: float,
        snap_enabled: bool,
        snap_size: float,
        snap_angle: float,
    ) -> tuple[bool, ViewportTransformState]:
        pg = self.pygame
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and not playing and view_mode == "scene":
            self._begin(event.pos, state, active_tool, zoom)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if state.dragging and state.selected_name is not None:
                self.emit({"type": "transform_end", "name": state.selected_name})
            state.dragging = False
            state.drag_handle = -1
        elif event.type == pg.MOUSEMOTION and state.dragging and not playing:
            self._drag(event.pos, state, active_tool, zoom, snap_enabled, snap_size, snap_angle)
        else:
            return False, state
        return True, state

    def _begin(self, position: tuple[int, int], state: ViewportTransformState, active_tool: str, zoom: float) -> None:
        state.drag_handle = -1
        state.move_axis = ""
        if active_tool == "move" and state.selected_name in self.objects:
            obj = self.objects[state.selected_name]
            if self._is_locked(obj):
                self._select_body(position, state, active_tool, zoom)
                return
            object_x, object_y = self.world_to_screen(float(obj["x"]), float(obj["y"]))
            angle = math.radians(float(obj.get("rotation", 0.0)))
            direction_x = (math.cos(angle), math.sin(angle))
            direction_y = (-math.sin(angle), math.cos(angle))
            end_x = (object_x + direction_x[0] * 92, object_y + direction_x[1] * 92)
            end_y = (object_x - direction_y[0] * 92, object_y - direction_y[1] * 92)
            if self._near(position, end_x, 15):
                state.move_axis = "x"
                self._start_drag(position, state, obj)
            elif self._near(position, end_y, 15):
                state.move_axis = "y"
                self._start_drag(position, state, obj)
        if not state.dragging and active_tool == "scale" and state.selected_name in self.objects:
            obj = self.objects[state.selected_name]
            if self._is_locked(obj):
                self._select_body(position, state, active_tool, zoom)
                return
            object_x, object_y = self.world_to_screen(float(obj["x"]), float(obj["y"]))
            angle = math.radians(float(obj.get("rotation", 0.0)))
            half_w, half_h = float(obj["w"]) * zoom / 2.0, float(obj["h"]) * zoom / 2.0
            handles = [(-half_w, -half_h), (0.0, -half_h), (half_w, -half_h), (half_w, 0.0),
                       (half_w, half_h), (0.0, half_h), (-half_w, half_h), (-half_w, 0.0)]
            for index, (handle_x, handle_y) in enumerate(handles):
                point = (
                    object_x + handle_x * math.cos(angle) - handle_y * math.sin(angle),
                    object_y + handle_x * math.sin(angle) + handle_y * math.cos(angle),
                )
                if self._near(position, point, 8):
                    state.drag_handle = index
                    self._start_drag(position, state, obj)
                    break
        if not state.dragging:
            self._select_body(position, state, active_tool, zoom)

    def _select_body(self, position: tuple[int, int], state: ViewportTransformState, active_tool: str, zoom: float) -> None:
        hit_candidates: list[tuple[str, dict[str, Any]]] = []
        for name, obj in sort_objects_for_hit_testing(self.objects):
            object_x, object_y = self.world_to_screen(float(obj["x"]), float(obj["y"]))
            angle = math.radians(-float(obj.get("rotation", 0.0)))
            mouse_x, mouse_y = position[0] - object_x, position[1] - object_y
            local_x = mouse_x * math.cos(angle) - mouse_y * math.sin(angle)
            local_y = mouse_x * math.sin(angle) + mouse_y * math.cos(angle)
            if abs(local_x) <= float(obj["w"]) * zoom / 2.0 and abs(local_y) <= float(obj["h"]) * zoom / 2.0:
                hit_candidates.append((name, obj))

        if not hit_candidates:
            return

        chosen_name, chosen_obj = next(
            ((name, obj) for name, obj in hit_candidates if not self._is_locked(obj)),
            hit_candidates[0],
        )

        state.selected_name = chosen_name
        state.drag_start_mouse = (float(position[0]), float(position[1]))
        state.drag_start_object = deepcopy(chosen_obj)
        self.emit({"type": "selected", "name": chosen_name})
        if active_tool != "select" and not self._is_locked(chosen_obj):
            state.dragging = True
            self.emit({"type": "transform_begin", "name": chosen_name})
            if active_tool == "scale":
                state.drag_handle = 8
        else:
            state.dragging = False

    def _start_drag(self, position: tuple[int, int], state: ViewportTransformState, obj: dict[str, Any]) -> None:
        state.dragging = True
        state.drag_start_mouse = (float(position[0]), float(position[1]))
        state.drag_start_object = deepcopy(obj)
        self.emit({"type": "transform_begin", "name": state.selected_name})

    def _drag(
        self, position: tuple[int, int], state: ViewportTransformState, active_tool: str,
        zoom: float, snap_enabled: bool, snap_size: float, snap_angle: float,
    ) -> None:
        if state.selected_name not in self.objects:
            return
        obj = self.objects[state.selected_name]
        if self._is_locked(obj):
            state.dragging = False
            return
        if active_tool == "move":
            self._move(position, obj, state, zoom, snap_enabled, snap_size)
        elif active_tool == "rotate":
            object_x, object_y = self.world_to_screen(float(obj["x"]), float(obj["y"]))
            angle = math.degrees(math.atan2(position[1] - object_y, position[0] - object_x))
            obj["rotation"] = self._snapped(angle, snap_angle, snap_enabled)
        elif active_tool == "scale":
            self._scale(position, obj, state, zoom, snap_enabled, snap_size)
        self.emit({"type": "transform", "name": state.selected_name, **{
            key: obj.get(key, 0.0) for key in ("x", "y", "w", "h", "rotation")
        }})

    def _move(self, position, obj, state, zoom, snap_enabled, snap_size) -> None:
        dx = (float(position[0]) - state.drag_start_mouse[0]) / zoom
        dy = (float(position[1]) - state.drag_start_mouse[1]) / zoom
        angle = float(state.drag_start_object.get("rotation", 0.0))
        radians = math.radians(-angle)
        local_x = dx * math.cos(radians) - dy * math.sin(radians)
        local_y = dx * math.sin(radians) + dy * math.cos(radians)
        if state.move_axis == "x":
            local_y = 0.0
        elif state.move_axis == "y":
            local_x = 0.0
        inverse = math.radians(angle)
        world_x = local_x * math.cos(inverse) - local_y * math.sin(inverse)
        world_y = local_x * math.sin(inverse) + local_y * math.cos(inverse)
        obj["x"] = self._snapped(float(state.drag_start_object["x"]) + world_x, snap_size, snap_enabled)
        obj["y"] = self._snapped(float(state.drag_start_object["y"]) + world_y, snap_size, snap_enabled)

    def _scale(self, position, obj, state, zoom, snap_enabled, snap_size) -> None:
        dx = (float(position[0]) - state.drag_start_mouse[0]) / zoom
        dy = (float(position[1]) - state.drag_start_mouse[1]) / zoom
        angle = float(state.drag_start_object.get("rotation", 0.0))
        radians = math.radians(-angle)
        local_x = dx * math.cos(radians) - dy * math.sin(radians)
        local_y = dx * math.sin(radians) + dy * math.cos(radians)
        original_w, original_h = float(state.drag_start_object["w"]), float(state.drag_start_object["h"])
        original_x, original_y = float(state.drag_start_object["x"]), float(state.drag_start_object["y"])
        horizontal = {-1: (0, 6, 7), 1: (2, 3, 4)}
        vertical = {-1: (0, 1, 2), 1: (4, 5, 6)}
        direction_x = next((direction for direction, handles in horizontal.items() if state.drag_handle in handles), 0)
        direction_y = next((direction for direction, handles in vertical.items() if state.drag_handle in handles), 0)
        modifiers = self.pygame.key.get_mods()
        from_center = bool(modifiers & self.pygame.KMOD_ALT) or state.drag_handle == 8
        proportional = bool(modifiers & self.pygame.KMOD_SHIFT)
        multiplier = 2.0 if from_center else 1.0
        new_w = original_w + direction_x * local_x * multiplier
        new_h = original_h + direction_y * local_y * multiplier
        if state.drag_handle == 8:
            new_w, new_h = original_w + local_x * 2.0, original_h + local_y * 2.0
        if proportional:
            width_ratio = new_w / original_w if original_w else 1.0
            height_ratio = new_h / original_h if original_h else 1.0
            if direction_x and direction_y:
                ratio = width_ratio if abs(width_ratio - 1.0) >= abs(height_ratio - 1.0) else height_ratio
            elif direction_x or state.drag_handle == 8:
                ratio = width_ratio
            else:
                ratio = height_ratio
            ratio = max(1.0 / max(original_w, original_h, 1.0), ratio)
            new_w, new_h = original_w * ratio, original_h * ratio
        final_w = max(1.0, self._snapped(new_w, snap_size, snap_enabled))
        final_h = max(1.0, self._snapped(new_h, snap_size, snap_enabled))
        obj["w"], obj["h"] = final_w, final_h
        if not from_center:
            center_x = direction_x * (final_w - original_w) / 2.0
            center_y = direction_y * (final_h - original_h) / 2.0
            rotation = math.radians(angle)
            obj["x"] = original_x + center_x * math.cos(rotation) - center_y * math.sin(rotation)
            obj["y"] = original_y + center_x * math.sin(rotation) + center_y * math.cos(rotation)

    @staticmethod
    def _near(first, second, tolerance: float) -> bool:
        return abs(first[0] - second[0]) <= tolerance and abs(first[1] - second[1]) <= tolerance

    @staticmethod
    def _snapped(value: float, step: float, enabled: bool) -> float:
        if not enabled or step <= 0.0:
            return value
        return round(value / step) * step

    @staticmethod
    def _is_locked(obj: dict[str, Any]) -> bool:
        return bool(obj.get("editor_locked", False))
