from __future__ import annotations

import math
from typing import Any
import numpy as np

from editor.runtime.tool_manager import EditorTool
from editor.runtime.command_manager import FunctionCommand
from editor.viewport.bounding_box import get_handle_positions, hit_test_handle
from editor.widgets.transform_interaction import emit_transform_changed, move_axis_at


class ViewportGizmoDragMixin:
    """Isola as operações de arrastar (drag) e interagir com gizmos e handles de transformação da viewport."""

    def _gizmo_hit_at_viewport_point(self, x: float, y: float, selected: Any) -> bool:
        if not self._should_draw_gizmo(selected) or not hasattr(selected, "transform"):
            return False
        cx, cy = self.world_to_viewport(selected.transform.position)
        length = float(self.move_gizmo_overlay.axis_length)
        if math.hypot(x - cx, y - cy) <= 10.0:
            return True
        near_x_axis = cx <= x <= cx + length + 16 and abs(y - cy) <= 10.0
        near_y_axis = cy - length - 16 <= y <= cy and abs(x - cx) <= 10.0
        return near_x_axis or near_y_axis

    def _begin_move_drag(self, obj: Any, x: float, y: float) -> bool:
        if self._active_tool() != EditorTool.MOVE:
            return False
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        world = self.viewport_to_world((x, y))
        self._move_drag_object = obj
        self._move_axis_lock = move_axis_at(self, float(x), float(y), obj)
        self._move_start_world = world.copy()
        self._move_start_position = obj.transform.position.copy()
        self.select_object(obj)
        self._update_hover_cursor(x, y)
        return True

    def _update_move_drag(self, x: float, y: float) -> None:
        obj = self._move_drag_object
        if obj is None or not hasattr(obj, "transform"):
            return
        world = self.viewport_to_world((x, y))
        delta = world - self._move_start_world
        if self._move_axis_lock == "x":
            delta[1] = 0.0
        elif self._move_axis_lock == "z":
            delta[0] = 0.0
        next_position = self._move_start_position + delta
        next_position = self._apply_snap(next_position)
        obj.transform.position[0] = next_position[0]
        obj.transform.position[1] = next_position[1]
        emit_transform_changed(self, obj)

    def _end_move_drag(self) -> None:
        obj = self._move_drag_object
        if obj is not None and hasattr(obj, "transform"):
            final_position = obj.transform.position.copy()
            start_position = self._move_start_position.copy()
            moved = not np.allclose(final_position[:2], start_position[:2])
            if moved and self.command_manager is not None:
                def _do(p=final_position, o=obj) -> None:
                    o.transform.position[0] = p[0]
                    o.transform.position[1] = p[1]
                    self.object_transform_changed.emit(o)

                def _undo(p=start_position, o=obj) -> None:
                    o.transform.position[0] = p[0]
                    o.transform.position[1] = p[1]
                    self.object_transform_changed.emit(o)

                self.command_manager.execute(
                    FunctionCommand(
                        description=f"Move {getattr(obj, 'name', 'object')}",
                        do=_do,
                        undo_action=_undo,
                    )
                )
                self.history_changed.emit()
        self._move_drag_object = None
        self._move_axis_lock = None
        self._update_hover_cursor(*self._qt_mouse_pos)

    def _rotate_gizmo_hit_at_viewport_point(self, x: float, y: float, selected: Any) -> bool:
        if not self._should_draw_gizmo(selected):
            return False
        return self.rotate_gizmo_overlay.hit_test(x, y, selected, self.world_to_viewport)

    def _begin_rotate_drag(self, obj: Any, x: float, y: float) -> bool:
        if self._active_tool() != EditorTool.ROTATE:
            return False
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        cx, cy = self.world_to_viewport(obj.transform.position)
        self._rotate_drag_object = obj
        self._rotate_start_rz = float(obj.transform.rz)
        self._rotate_start_angle = math.degrees(math.atan2(y - cy, x - cx))
        self._rotate_center_screen = (cx, cy)
        self._rotate_current_mouse = (x, y)
        self.select_object(obj)
        self._update_hover_cursor(x, y)
        return True

    def _update_rotate_drag(self, x: float, y: float) -> None:
        obj = self._rotate_drag_object
        if obj is None or not hasattr(obj, "transform"):
            return
        cx, cy = self.world_to_viewport(obj.transform.position)
        current_angle = math.degrees(math.atan2(y - cy, x - cx))
        delta = current_angle - self._rotate_start_angle
        new_rz = self._apply_snap_angle(self._rotate_start_rz + delta)
        obj.transform.rz = new_rz
        self._rotate_current_mouse = (x, y)
        emit_transform_changed(self, obj)

    def _end_rotate_drag(self) -> None:
        obj = self._rotate_drag_object
        if obj is not None and hasattr(obj, "transform"):
            final_rz = float(obj.transform.rz)
            start_rz = self._rotate_start_rz
            rotated = not math.isclose(final_rz, start_rz, abs_tol=0.01)
            if rotated and self.command_manager is not None:
                def _do(rz=final_rz, o=obj) -> None:
                    o.transform.rz = rz
                    self.object_transform_changed.emit(o)

                def _undo(rz=start_rz, o=obj) -> None:
                    o.transform.rz = rz
                    self.object_transform_changed.emit(o)

                self.command_manager.execute(
                    FunctionCommand(
                        description=f"Rotate {getattr(obj, 'name', 'object')}",
                        do=_do,
                        undo_action=_undo,
                    )
                )
                self.history_changed.emit()
        self._rotate_drag_object = None
        self._rotate_current_mouse = None
        self._update_hover_cursor(*self._qt_mouse_pos)

    def _scale_handle_positions(self, obj: Any) -> list[tuple[float, float]]:
        if obj is None or not hasattr(obj, "transform"):
            return []
        pos = getattr(obj.transform, "position", None)
        scale = getattr(obj.transform, "scale", None)
        if pos is None or scale is None:
            return []

        p0 = self.world_to_viewport((pos[0] - scale[0] / 2.0, pos[1] - scale[1] / 2.0, pos[2]))
        p1 = self.world_to_viewport((pos[0] + scale[0] / 2.0, pos[1] + scale[1] / 2.0, pos[2]))
        bounds = (
            min(p0[0], p1[0]),
            min(p0[1], p1[1]),
            max(p0[0], p1[0]),
            max(p0[1], p1[1]),
        )
        return get_handle_positions(bounds)

    def _scale_handle_at_viewport_point(self, x: float, y: float, selected: Any) -> int | None:
        if self._active_tool() != EditorTool.SCALE:
            return None
        if not self._should_draw_gizmo(selected):
            return None
        return hit_test_handle((x, y), self._scale_handle_positions(selected), tolerance=8.0)

    def _begin_scale_drag(self, obj: Any, x: float, y: float, handle_idx: int) -> bool:
        if self._active_tool() != EditorTool.SCALE:
            return False
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        self._scale_drag_object = obj
        self._scale_handle_idx = int(handle_idx)
        self._scale_start_world = self.viewport_to_world((x, y)).copy()
        self._scale_start_position = obj.transform.position.copy()
        self._scale_start_scale = obj.transform.scale.copy()
        self.select_object(obj)
        self._update_hover_cursor(x, y)
        return True

    def _update_scale_drag(self, x: float, y: float) -> None:
        obj = self._scale_drag_object
        handle_idx = self._scale_handle_idx
        if obj is None or handle_idx is None or not hasattr(obj, "transform"):
            return

        world = self.viewport_to_world((x, y))
        delta = world - self._scale_start_world
        next_position = self._scale_start_position.copy()
        next_scale = self._scale_start_scale.copy()

        affects_left = handle_idx in (0, 6, 7)
        affects_right = handle_idx in (2, 3, 4)
        affects_top = handle_idx in (0, 1, 2)
        affects_bottom = handle_idx in (4, 5, 6)

        if affects_right:
            next_scale[0] = self._scale_start_scale[0] + delta[0]
            next_position[0] = self._scale_start_position[0] + delta[0] / 2.0
        elif affects_left:
            next_scale[0] = self._scale_start_scale[0] - delta[0]
            next_position[0] = self._scale_start_position[0] + delta[0] / 2.0

        if affects_bottom:
            next_scale[1] = self._scale_start_scale[1] + delta[1]
            next_position[1] = self._scale_start_position[1] + delta[1] / 2.0
        elif affects_top:
            next_scale[1] = self._scale_start_scale[1] - delta[1]
            next_position[1] = self._scale_start_position[1] + delta[1] / 2.0

        if self._snap_enabled():
            snap = self._snap_size()
            next_scale[0] = round(float(next_scale[0]) / snap) * snap
            next_scale[1] = round(float(next_scale[1]) / snap) * snap

        next_scale[0] = max(1.0, float(next_scale[0]))
        next_scale[1] = max(1.0, float(next_scale[1]))

        obj.transform.position[0] = next_position[0]
        obj.transform.position[1] = next_position[1]
        obj.transform.scale[0] = next_scale[0]
        obj.transform.scale[1] = next_scale[1]
        emit_transform_changed(self, obj)

    def _end_scale_drag(self) -> None:
        obj = self._scale_drag_object
        if obj is not None and hasattr(obj, "transform"):
            final_position = obj.transform.position.copy()
            final_scale = obj.transform.scale.copy()
            start_position = self._scale_start_position.copy()
            start_scale = self._scale_start_scale.copy()
            scaled = (
                not np.allclose(final_scale[:2], start_scale[:2])
                or not np.allclose(final_position[:2], start_position[:2])
            )
            if scaled and self.command_manager is not None:
                def _do(p=final_position, s=final_scale, o=obj) -> None:
                    o.transform.position[0] = p[0]
                    o.transform.position[1] = p[1]
                    o.transform.scale[0] = s[0]
                    o.transform.scale[1] = s[1]
                    self.object_transform_changed.emit(o)

                def _undo(p=start_position, s=start_scale, o=obj) -> None:
                    o.transform.position[0] = p[0]
                    o.transform.position[1] = p[1]
                    o.transform.scale[0] = s[0]
                    o.transform.scale[1] = s[1]
                    self.object_transform_changed.emit(o)

                self.command_manager.execute(
                    FunctionCommand(
                        description=f"Scale {getattr(obj, 'name', 'object')}",
                        do=_do,
                        undo_action=_undo,
                    )
                )
                self.history_changed.emit()
        self._scale_drag_object = None
        self._scale_handle_idx = None
        self._update_hover_cursor(*self._qt_mouse_pos)
