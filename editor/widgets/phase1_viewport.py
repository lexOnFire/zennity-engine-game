from __future__ import annotations

import math
from typing import Any

import numpy as np
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtGui import QMouseEvent

from editor.gizmos.qt_gizmo_overlay import QtMoveGizmoOverlay
from editor.runtime.editor_state import EditorState
from editor.runtime.tool_manager import EditorTool, ToolManager
from editor.widgets.viewport_widget import ViewportWidget


class Phase1ViewportWidget(ViewportWidget):
    """Viewport da Fase 1 com overlay de gizmo Qt seguro.

    Herda toda a lógica funcional da Viewport original e apenas desenha o gizmo
    por cima, sem tocar em eventos de mouse/teclado ou scene.draw.
    """

    object_transform_changed = Signal(object)
    tool_message_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.move_gizmo_overlay = QtMoveGizmoOverlay()
        self.tool_manager: ToolManager | None = None
        self.editor_state: EditorState | None = None
        self._move_drag_object: Any = None
        self._move_start_world = np.zeros(3, dtype=np.float32)
        self._move_start_position = np.zeros(3, dtype=np.float32)

    def set_tool_manager(self, tool_manager: ToolManager) -> None:
        self.tool_manager = tool_manager

    def set_editor_state(self, editor_state: EditorState) -> None:
        self.editor_state = editor_state

    def _active_tool(self) -> EditorTool:
        if self.tool_manager is None:
            return EditorTool.SELECT
        return self.tool_manager.active_tool

    def _is_playing(self) -> bool:
        return bool(getattr(getattr(self, "active_scene", None), "playing", False))

    def _should_draw_gizmo(self, selected: Any) -> bool:
        return selected is not None and not self._is_playing()

    def _snap_size(self) -> float:
        if self.editor_state is None:
            return 1.0
        return max(1.0, float(self.editor_state.snap_size))

    def _snap_enabled(self) -> bool:
        return bool(self.editor_state is not None and self.editor_state.snap_enabled)

    def _apply_snap(self, position: np.ndarray) -> np.ndarray:
        if not self._snap_enabled():
            return position
        snap = self._snap_size()
        snapped = position.copy()
        snapped[0] = round(float(snapped[0]) / snap) * snap
        snapped[1] = round(float(snapped[1]) / snap) * snap
        return snapped

    def _selected_transform_object(self) -> Any:
        selected = self.selected_object() if hasattr(self, "selected_object") else None
        if selected is not None and hasattr(selected, "transform"):
            return selected
        return None

    def _object_at_viewport_point(self, x: float, y: float) -> Any:
        scene = getattr(self, "active_scene", None)
        if scene is None:
            return None
        world = self.viewport_to_world((x, y))
        for obj in reversed(list(getattr(scene, "editable_objects", []))):
            transform = getattr(obj, "transform", None)
            if transform is None:
                continue
            pos = getattr(transform, "position", None)
            scale = getattr(transform, "scale", None)
            if pos is None or scale is None:
                continue
            if getattr(obj, "mesh_type", "") == "Círculo":
                if math.hypot(world[0] - pos[0], world[1] - pos[1]) <= scale[0] / 2:
                    return obj
            elif abs(world[0] - pos[0]) <= scale[0] / 2 and abs(world[1] - pos[1]) <= scale[1] / 2:
                return obj
        return None

    def _begin_move_drag(self, obj: Any, x: float, y: float) -> bool:
        if self._active_tool() != EditorTool.MOVE:
            return False
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        world = self.viewport_to_world((x, y))
        self._move_drag_object = obj
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
        next_position = self._move_start_position + delta
        if not np.allclose(delta[:2], 0.0):
            next_position = self._apply_snap(next_position)
        obj.transform.position[0] = next_position[0]
        obj.transform.position[1] = next_position[1]
        self.object_transform_changed.emit(obj)
        self.update()

    def _end_move_drag(self) -> None:
        self._move_drag_object = None
        self._update_hover_cursor(*self._qt_mouse_pos)

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

    def _update_hover_cursor(self, x: float, y: float) -> None:
        if self._is_playing():
            self.unsetCursor()
            return
        tool = self._active_tool()
        selected = self._selected_transform_object()
        if self._move_drag_object is not None:
            self.setCursor(Qt.ClosedHandCursor)
        elif tool == EditorTool.MOVE and (
            self._gizmo_hit_at_viewport_point(x, y, selected)
            or self._object_at_viewport_point(x, y) is not None
        ):
            self.setCursor(Qt.OpenHandCursor)
        elif tool == EditorTool.SELECT and self._object_at_viewport_point(x, y) is not None:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()

    def _show_unimplemented_tool_message(self, tool: EditorTool) -> None:
        self.tool_message_requested.emit(f"{tool.value.title()} em desenvolvimento")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        tool = self._active_tool()
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        x, y = float(event.x()), float(event.y())

        if tool == EditorTool.SELECT:
            self.select_object(self._object_at_viewport_point(x, y))
            event.accept()
            return

        if tool == EditorTool.MOVE:
            clicked = self._object_at_viewport_point(x, y)
            selected = self._selected_transform_object()
            target = clicked
            if target is None and self._gizmo_hit_at_viewport_point(x, y, selected):
                target = selected
            if target is not None and self._begin_move_drag(target, x, y):
                event.accept()
                return
            event.accept()
            return

        if tool in (EditorTool.ROTATE, EditorTool.SCALE):
            self._show_unimplemented_tool_message(tool)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._active_tool() == EditorTool.MOVE and self._move_drag_object is not None:
            self._update_move_drag(float(event.x()), float(event.y()))
            event.accept()
            return
        self._update_hover_cursor(float(event.x()), float(event.y()))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._move_drag_object is not None:
            self._end_move_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintGL(self) -> None:
        super().paintGL()
        selected = None
        if hasattr(self, "selected_object"):
            selected = self.selected_object()
        elif getattr(self, "viewmodel", None) is not None:
            selected = getattr(self.viewmodel, "selected_object", None)
        if not self._should_draw_gizmo(selected):
            return
        painter = QPainter(self)
        self._draw_selection_outline(painter, selected)
        self.move_gizmo_overlay.draw(painter, selected, self.world_to_viewport)
        painter.end()

    def _draw_selection_outline(self, painter: QPainter, selected: Any) -> None:
        if selected is None or not hasattr(selected, "transform"):
            return
        pos = getattr(selected.transform, "position", None)
        scale = getattr(selected.transform, "scale", None)
        if pos is None or scale is None:
            return
        left_top = self.world_to_viewport((pos[0] - scale[0] / 2, pos[1] - scale[1] / 2, pos[2]))
        right_bottom = self.world_to_viewport((pos[0] + scale[0] / 2, pos[1] + scale[1] / 2, pos[2]))
        rect = QRectF(
            min(left_top[0], right_bottom[0]),
            min(left_top[1], right_bottom[1]),
            abs(right_bottom[0] - left_top[0]),
            abs(right_bottom[1] - left_top[1]),
        ).adjusted(-3.0, -3.0, 3.0, 3.0)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor(80, 160, 255), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawRect(rect)
        painter.restore()
