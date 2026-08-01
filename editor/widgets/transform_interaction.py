from __future__ import annotations

import time
from typing import Any

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPen

from editor.runtime.tool_manager import EditorTool


def event_position(event: Any) -> tuple[float, float]:
    """Return precise Qt 6 coordinates with compatibility for synthetic events."""
    if hasattr(event, "position"):
        point = event.position()
    elif hasattr(event, "pos"):
        point = event.pos()
    else:
        return float(event.x()), float(event.y())
    return float(point.x()), float(point.y())


def sync_camera_to_engine(viewport: Any) -> None:
    from engine.graphics.camera2d import Camera2D

    camera2d = Camera2D.main
    camera = getattr(viewport, "camera", None)
    if camera2d is None or camera is None or getattr(camera2d, "transform", None) is None:
        return
    camera2d.zoom = float(camera.zoom)
    camera2d.transform.position[0] = float(camera.position[0])
    camera2d.transform.position[1] = float(camera.position[1])


def activate_gizmo_reference(viewport: Any, tool: EditorTool) -> None:
    if tool not in (EditorTool.MOVE, EditorTool.ROTATE, EditorTool.SCALE):
        return
    obj = viewport._selected_transform_object()
    scene = getattr(viewport, "active_scene", None)
    objects = list(getattr(scene, "editable_objects", [])) if scene is not None else []
    if obj is None:
        index = int(getattr(scene, "selected_index", -1)) if scene is not None else -1
        obj = objects[index] if 0 <= index < len(objects) else next(
            (candidate for candidate in objects if getattr(candidate, "name", "") != "EditorCamera"),
            None,
        )
    if obj is None or not hasattr(obj, "transform"):
        return
    viewport.select_object(obj)
    if obj in objects and hasattr(scene, "selected_index"):
        scene.selected_index = objects.index(obj)
    x, y = viewport.world_to_viewport(obj.transform.position)
    viewport._update_hover_cursor(float(x), float(y))
    viewport.update()


def move_axis_at(viewport: Any, x: float, y: float, selected: Any) -> str | None:
    if selected is None or not hasattr(selected, "transform"):
        return None
    cx, cy = viewport.world_to_viewport(selected.transform.position)
    length = float(viewport.move_gizmo_overlay.axis_length)
    if ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 <= 10.0:
        return None
    near_x = cx <= x <= cx + length + 18 and abs(y - cy) <= 12.0
    near_z = cy - length - 18 <= y <= cy and abs(x - cx) <= 12.0
    if near_x and near_z:
        return "x" if abs(y - cy) <= abs(x - cx) else "z"
    if near_x:
        return "x"
    if near_z:
        return "z"
    return None


def sync_collider_size(viewport: Any, obj: Any) -> None:
    scene = getattr(viewport, "active_scene", None)
    if scene is not None and callable(getattr(scene, "_sync_collider", None)):
        scene._sync_collider(obj)
        return
    from engine.physics.collider import BoxCollider, CircleCollider

    scale = obj.transform.scale
    box = obj.get_component(BoxCollider)
    if box is not None:
        box.width = max(1, int(abs(float(scale[0]))))
        box.height = max(1, int(abs(float(scale[1]))))
        return
    circle = obj.get_component(CircleCollider)
    if circle is not None:
        circle.radius = max(1, int(abs(float(scale[0])) / 2.0))


def request_editor_frame(viewport: Any, target_fps: float = 60.0) -> None:
    now = time.monotonic()
    interval = 1.0 / max(1.0, float(target_fps))
    elapsed = now - float(getattr(viewport, "_last_drag_repaint", 0.0))
    if elapsed >= interval:
        viewport._last_drag_repaint = now
        viewport.update()
        return
    if bool(getattr(viewport, "_drag_repaint_pending", False)):
        return
    viewport._drag_repaint_pending = True

    def paint_latest() -> None:
        viewport._drag_repaint_pending = False
        viewport._last_drag_repaint = time.monotonic()
        if not viewport._is_playing():
            viewport.update()

    QTimer.singleShot(max(1, int((interval - elapsed) * 1000.0)), paint_latest)


def emit_transform_changed(viewport: Any, obj: Any) -> None:
    sync_collider_size(viewport, obj)
    viewport.object_transform_changed.emit(obj)
    request_editor_frame(viewport)


def draw_transform_overlay(viewport: Any) -> None:
    if viewport.is_game_view() or viewport._is_playing():
        return
    selected = viewport._selected_transform_object()
    if selected is None or not hasattr(selected, "transform"):
        return
    tool = viewport._active_tool()
    if tool not in (EditorTool.SCALE, EditorTool.MOVE):
        return
    painter = QPainter(viewport)
    try:
        painter.setRenderHint(QPainter.Antialiasing, True)
        cx, cy = viewport.world_to_viewport(selected.transform.position)
        if tool == EditorTool.SCALE:
            painter.setPen(QPen(QColor(80, 160, 255, 190), 2, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(QPointF(cx - 42, cy), QPointF(cx + 42, cy))
            painter.drawLine(QPointF(cx, cy - 42), QPointF(cx, cy + 42))
            painter.setBrush(QBrush(QColor(80, 160, 255, 220)))
            for px, py in viewport._scale_handle_positions(selected):
                painter.drawRect(QRectF(px - 4, py - 4, 8, 8))
        else:
            axis = getattr(viewport, "_move_axis_lock", None)
            if axis in ("x", "z"):
                color = QColor(230, 70, 70, 120) if axis == "x" else QColor(70, 210, 90, 120)
                painter.setPen(QPen(color, 5, Qt.SolidLine, Qt.RoundCap))
                if axis == "x":
                    painter.drawLine(QPointF(cx - 9999, cy), QPointF(cx + 9999, cy))
                else:
                    painter.drawLine(QPointF(cx, cy - 9999), QPointF(cx, cy + 9999))
    finally:
        painter.end()
