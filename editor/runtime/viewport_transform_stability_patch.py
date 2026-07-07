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


def _selected_or_scene_object(viewport: Any) -> Any | None:
    obj = None
    try:
        obj = viewport.selected_object()
    except Exception:
        obj = None
    if obj is not None and hasattr(obj, "transform"):
        return obj
    scene = getattr(viewport, "active_scene", None)
    if scene is None:
        return None
    objects = list(getattr(scene, "editable_objects", []))
    idx = int(getattr(scene, "selected_index", -1))
    if 0 <= idx < len(objects):
        return objects[idx]
    for candidate in objects:
        if getattr(candidate, "name", "") != "EditorCamera" and hasattr(candidate, "transform"):
            return candidate
    return None


def _activate_gizmo_reference(viewport: Any) -> None:
    obj = _selected_or_scene_object(viewport)
    if obj is None:
        return
    try:
        viewport.select_object(obj)
    except Exception:
        pass
    scene = getattr(viewport, "active_scene", None)
    objects = list(getattr(scene, "editable_objects", [])) if scene is not None else []
    if obj in objects and hasattr(scene, "selected_index"):
        scene.selected_index = objects.index(obj)
    try:
        x, y = viewport.world_to_viewport(obj.transform.position)
        viewport._update_hover_cursor(float(x), float(y))
    except Exception:
        pass
    try:
        viewport.update()
    except Exception:
        pass


def _move_axis_at(viewport: Any, x: float, y: float, selected: Any) -> str | None:
    if selected is None or not hasattr(selected, "transform"):
        return None
    try:
        cx, cy = viewport.world_to_viewport(selected.transform.position)
        length = float(getattr(getattr(viewport, "move_gizmo_overlay", None), "axis_length", 72))
    except Exception:
        return None
    near_center = ((float(x) - cx) ** 2 + (float(y) - cy) ** 2) ** 0.5 <= 10.0
    if near_center:
        return None
    near_x = cx <= float(x) <= cx + length + 18 and abs(float(y) - cy) <= 12.0
    near_z = cy - length - 18 <= float(y) <= cy and abs(float(x) - cx) <= 12.0
    if near_x and near_z:
        return "x" if abs(float(y) - cy) <= abs(float(x) - cx) else "z"
    if near_x:
        return "x"
    if near_z:
        return "z"
    return None


def _sync_collider_size(viewport: Any, obj: Any) -> None:
    if obj is None or not hasattr(obj, "transform"):
        return
    scene = getattr(viewport, "active_scene", None)
    if scene is not None and hasattr(scene, "_sync_collider"):
        try:
            scene._sync_collider(obj)
            return
        except Exception:
            pass
    try:
        from engine.physics.collider import BoxCollider, CircleCollider
    except Exception:
        return
    scale = getattr(obj.transform, "scale", [1.0, 1.0, 1.0])
    box = obj.get_component(BoxCollider) if hasattr(obj, "get_component") else None
    if box is not None:
        box.width = max(1, int(abs(float(scale[0]))))
        box.height = max(1, int(abs(float(scale[1]))))
        return
    circle = obj.get_component(CircleCollider) if hasattr(obj, "get_component") else None
    if circle is not None:
        circle.radius = max(1, int(abs(float(scale[0])) / 2.0))


def _emit_transform_changed(viewport: Any, obj: Any) -> None:
    _sync_collider_size(viewport, obj)
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
        from PySide6.QtCore import Qt, QRectF, QPointF
        from PySide6.QtGui import QColor, QPainter, QPen, QBrush
    except Exception:
        return False

    if getattr(Phase1ViewportWidget, "_zennity_transform_stability_patch_applied", False):
        return True

    original_set_tool_manager = Phase1ViewportWidget.set_tool_manager
    original_wheel_event = Phase1ViewportWidget.wheelEvent
    original_mouse_move_event = Phase1ViewportWidget.mouseMoveEvent
    original_mouse_press_event = Phase1ViewportWidget.mousePressEvent
    original_resize_gl = Phase1ViewportWidget.resizeGL
    original_paint_gl = Phase1ViewportWidget.paintGL
    original_update_move_drag = Phase1ViewportWidget._update_move_drag

    def on_tool_changed(self, tool):
        if tool in (EditorTool.MOVE, EditorTool.ROTATE, EditorTool.SCALE):
            _activate_gizmo_reference(self)

    def set_tool_manager(self, tool_manager):
        original_set_tool_manager(self, tool_manager)
        try:
            tool_manager.subscribe(lambda tool, vp=self: on_tool_changed(vp, tool))
        except Exception:
            pass
        try:
            on_tool_changed(self, tool_manager.active_tool)
        except Exception:
            pass

    def wheel_event(self, event):
        original_wheel_event(self, event)
        _sync_camera_to_engine(self)

    def mouse_move_event(self, event):
        was_panning = bool(getattr(self, "_panning", False))
        original_mouse_move_event(self, event)
        if was_panning or bool(getattr(self, "_panning", False)):
            _sync_camera_to_engine(self)

    def mouse_press_event(self, event):
        if self.is_game_view() or self._is_playing() or event.button() != Qt.LeftButton:
            original_mouse_press_event(self, event)
            return
        x, y = float(event.x()), float(event.y())
        if self._active_tool() == EditorTool.MOVE:
            selected = self._selected_transform_object()
            axis = _move_axis_at(self, x, y, selected)
            if selected is not None and axis is not None and self._begin_move_drag(selected, x, y):
                self._move_axis_lock = axis
                event.accept()
                return
        if self._active_tool() == EditorTool.SCALE:
            selected = self._selected_transform_object()
            handle_idx = self._scale_handle_at_viewport_point(x, y, selected)
            if selected is not None and handle_idx is not None and self._begin_scale_drag(selected, x, y, handle_idx):
                event.accept()
                return
            clicked = self._object_at_viewport_point(x, y)
            if clicked is not None:
                self.select_object(clicked)
                scene = getattr(self, "active_scene", None)
                objs = getattr(scene, "editable_objects", []) if scene is not None else []
                if clicked in objs:
                    scene.selected_index = objs.index(clicked)
                self._update_hover_cursor(x, y)
                self.update()
                event.accept()
                return
        original_mouse_press_event(self, event)

    def resize_gl(self, w: int, h: int) -> None:
        original_resize_gl(self, w, h)
        try:
            self.camera.set_viewport_size(max(32, int(w)), max(32, int(h)))
        except Exception:
            pass
        _sync_camera_to_engine(self)

    def paint_gl(self) -> None:
        original_paint_gl(self)
        if self.is_game_view() or self._is_playing():
            return
        selected = self._selected_transform_object()
        if selected is None or not hasattr(selected, "transform"):
            return
        tool = self._active_tool()
        if tool not in (EditorTool.SCALE, EditorTool.MOVE):
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            cx, cy = self.world_to_viewport(selected.transform.position)
            if tool == EditorTool.SCALE:
                painter.setPen(QPen(QColor(80, 160, 255, 190), 2, Qt.SolidLine, Qt.RoundCap))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(QPointF(cx - 42, cy), QPointF(cx + 42, cy))
                painter.drawLine(QPointF(cx, cy - 42), QPointF(cx, cy + 42))
                painter.setBrush(QBrush(QColor(80, 160, 255, 220)))
                for px, py in self._scale_handle_positions(selected):
                    painter.drawRect(QRectF(px - 4, py - 4, 8, 8))
                painter.setPen(QPen(QColor(80, 160, 255), 1))
                painter.drawText(QPointF(cx + 48, cy - 6), "SCALE X")
                painter.drawText(QPointF(cx + 8, cy - 48), "SCALE Z")
            elif tool == EditorTool.MOVE:
                axis = getattr(self, "_move_axis_lock", None)
                if axis in ("x", "z"):
                    color = QColor(230, 70, 70, 120) if axis == "x" else QColor(70, 210, 90, 120)
                    painter.setPen(QPen(color, 5, Qt.SolidLine, Qt.RoundCap))
                    if axis == "x":
                        painter.drawLine(QPointF(cx - 9999, cy), QPointF(cx + 9999, cy))
                    else:
                        painter.drawLine(QPointF(cx, cy - 9999), QPointF(cx, cy + 9999))
        finally:
            painter.end()

    def update_move_drag(self, x: float, y: float) -> None:
        obj = getattr(self, "_move_drag_object", None)
        if obj is None or not hasattr(obj, "transform"):
            original_update_move_drag(self, x, y)
            return
        world = self.viewport_to_world((float(x), float(y)))
        delta = world - getattr(self, "_move_start_world", np.zeros(3, dtype=np.float32))
        axis = getattr(self, "_move_axis_lock", None)
        if axis == "x":
            delta[1] = 0.0
        elif axis == "z":
            delta[0] = 0.0
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
        self._move_axis_lock = _move_axis_at(self, float(x), float(y), obj)
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

    Phase1ViewportWidget.set_tool_manager = set_tool_manager
    Phase1ViewportWidget.wheelEvent = wheel_event
    Phase1ViewportWidget.mouseMoveEvent = mouse_move_event
    Phase1ViewportWidget.mousePressEvent = mouse_press_event
    Phase1ViewportWidget.resizeGL = resize_gl
    Phase1ViewportWidget.paintGL = paint_gl
    Phase1ViewportWidget._begin_move_drag = begin_move_drag
    Phase1ViewportWidget._update_move_drag = update_move_drag
    Phase1ViewportWidget._update_rotate_drag = update_rotate_drag
    Phase1ViewportWidget._update_scale_drag = update_scale_drag
    Phase1ViewportWidget._zennity_transform_stability_patch_applied = True
    return True
