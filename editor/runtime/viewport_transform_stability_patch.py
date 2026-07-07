from __future__ import annotations

from typing import Any

import numpy as np


def _sync_camera_to_engine(viewport: Any) -> None:
    try:
        from engine.graphics.camera2d import Camera2D
    except Exception:
        return
    camera2d = getattr(Camera2D, "main", None)
    camera = getattr(viewport, "camera", None)
    if camera2d is None or camera is None or getattr(camera2d, "transform", None) is None:
        return
    camera2d.zoom = float(getattr(camera, "zoom", 1.0))
    camera2d.transform.position[0] = float(getattr(camera, "position", [0.0, 0.0])[0])
    camera2d.transform.position[1] = float(getattr(camera, "position", [0.0, 0.0])[1])


def _emit_transform_changed(viewport: Any, obj: Any) -> None:
    try:
        viewport.object_transform_changed.emit(obj)
    except Exception:
        pass
    try:
        viewport.update()
    except Exception:
        pass


def apply_viewport_transform_stability_patch() -> bool:
    try:
        from editor.widgets.phase1_viewport import Phase1ViewportWidget
        from editor.runtime.tool_manager import EditorTool
    except Exception:
        return False

    if getattr(Phase1ViewportWidget, "_zennity_transform_stability_patch_applied", False):
        return True

    original_wheel_event = Phase1ViewportWidget.wheelEvent
    original_mouse_move_event = Phase1ViewportWidget.mouseMoveEvent
    original_resize_gl = Phase1ViewportWidget.resizeGL
    original_update_move_drag = Phase1ViewportWidget._update_move_drag

    def wheel_event(self, event):
        original_wheel_event(self, event)
        _sync_camera_to_engine(self)

    def mouse_move_event(self, event):
        was_panning = bool(getattr(self, "_panning", False))
        original_mouse_move_event(self, event)
        if was_panning or bool(getattr(self, "_panning", False)):
            _sync_camera_to_engine(self)

    def resize_gl(self, w: int, h: int) -> None:
        original_resize_gl(self, w, h)
        try:
            self.camera.set_viewport_size(max(32, int(w)), max(32, int(h)))
        except Exception:
            pass
        _sync_camera_to_engine(self)

    def update_move_drag(self, x: float, y: float) -> None:
        obj = getattr(self, "_move_drag_object", None)
        if obj is None or not hasattr(obj, "transform"):
            original_update_move_drag(self, x, y)
            return
        world = self.viewport_to_world((float(x), float(y)))
        delta = world - getattr(self, "_move_start_world", np.zeros(3, dtype=np.float32))
        start_position = getattr(self, "_move_start_position", obj.transform.position).copy()
        next_position = start_position + delta
        next_position = self._apply_snap(next_position)
        obj.transform.position[0] = float(next_position[0])
        obj.transform.position[1] = float(next_position[1])
        _emit_transform_changed(self, obj)

    def begin_move_drag(self, obj: Any, x: float, y: float) -> bool:
        if self._active_tool() != EditorTool.MOVE or self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        self._move_drag_object = obj
        self._move_start_world = self.viewport_to_world((float(x), float(y))).copy()
        self._move_start_position = obj.transform.position.copy()
        self.select_object(obj)
        self._update_hover_cursor(float(x), float(y))
        return True

    def update_rotate_drag(self, x: float, y: float) -> None:
        obj = getattr(self, "_rotate_drag_object", None)
        if obj is None or not hasattr(obj, "transform"):
            return
        cx, cy = self.world_to_viewport(obj.transform.position)
        import math
        current_angle = math.degrees(math.atan2(float(y) - cy, float(x) - cx))
        delta = current_angle - float(getattr(self, "_rotate_start_angle", current_angle))
        new_rz = self._apply_snap_angle(float(getattr(self, "_rotate_start_rz", 0.0)) + delta)
        obj.transform.rz = float(new_rz)
        self._rotate_current_mouse = (float(x), float(y))
        _emit_transform_changed(self, obj)

    def update_scale_drag(self, x: float, y: float) -> None:
        obj = getattr(self, "_scale_drag_object", None)
        handle_idx = getattr(self, "_scale_handle_idx", None)
        if obj is None or handle_idx is None or not hasattr(obj, "transform"):
            return
        world = self.viewport_to_world((float(x), float(y)))
        start_world = getattr(self, "_scale_start_world", world)
        delta = world - start_world
        next_position = getattr(self, "_scale_start_position", obj.transform.position).copy()
        next_scale = getattr(self, "_scale_start_scale", obj.transform.scale).copy()

        affects_left = handle_idx in (0, 6, 7)
        affects_right = handle_idx in (2, 3, 4)
        affects_top = handle_idx in (0, 1, 2)
        affects_bottom = handle_idx in (4, 5, 6)

        if affects_right:
            next_scale[0] += delta[0]
            next_position[0] += delta[0] / 2.0
        elif affects_left:
            next_scale[0] -= delta[0]
            next_position[0] += delta[0] / 2.0
        if affects_bottom:
            next_scale[1] += delta[1]
            next_position[1] += delta[1] / 2.0
        elif affects_top:
            next_scale[1] -= delta[1]
            next_position[1] += delta[1] / 2.0

        if self._snap_enabled():
            snap = self._snap_size()
            next_scale[0] = round(float(next_scale[0]) / snap) * snap
            next_scale[1] = round(float(next_scale[1]) / snap) * snap
        next_scale[0] = max(1.0, abs(float(next_scale[0])))
        next_scale[1] = max(1.0, abs(float(next_scale[1])))

        obj.transform.position[0] = float(next_position[0])
        obj.transform.position[1] = float(next_position[1])
        obj.transform.scale[0] = float(next_scale[0])
        obj.transform.scale[1] = float(next_scale[1])
        _emit_transform_changed(self, obj)

    Phase1ViewportWidget.wheelEvent = wheel_event
    Phase1ViewportWidget.mouseMoveEvent = mouse_move_event
    Phase1ViewportWidget.resizeGL = resize_gl
    Phase1ViewportWidget._begin_move_drag = begin_move_drag
    Phase1ViewportWidget._update_move_drag = update_move_drag
    Phase1ViewportWidget._update_rotate_drag = update_rotate_drag
    Phase1ViewportWidget._update_scale_drag = update_scale_drag
    Phase1ViewportWidget._zennity_transform_stability_patch_applied = True
    return True
