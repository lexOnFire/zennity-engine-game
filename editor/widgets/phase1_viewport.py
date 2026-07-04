from __future__ import annotations

import math
from typing import Any

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtGui import QMouseEvent

from editor.gizmos.qt_gizmo_overlay import QtMoveGizmoOverlay
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
        self._move_drag_object: Any = None
        self._move_drag_offset = np.zeros(3, dtype=np.float32)

    def set_tool_manager(self, tool_manager: ToolManager) -> None:
        self.tool_manager = tool_manager

    def _active_tool(self) -> EditorTool:
        if self.tool_manager is None:
            return EditorTool.SELECT
        return self.tool_manager.active_tool

    def _is_playing(self) -> bool:
        return bool(getattr(getattr(self, "active_scene", None), "playing", False))

    def _should_draw_gizmo(self, selected: Any) -> bool:
        return selected is not None and not self._is_playing()

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
        if self._is_playing():
            return False
        if obj is None or not hasattr(obj, "transform"):
            return False
        world = self.viewport_to_world((x, y))
        self._move_drag_object = obj
        self._move_drag_offset = (obj.transform.position - world).copy()
        self.select_object(obj)
        return True

    def _update_move_drag(self, x: float, y: float) -> None:
        obj = self._move_drag_object
        if obj is None or not hasattr(obj, "transform"):
            return
        world = self.viewport_to_world((x, y))
        obj.transform.position[0] = world[0] + self._move_drag_offset[0]
        obj.transform.position[1] = world[1] + self._move_drag_offset[1]
        self.object_transform_changed.emit(obj)
        self.update()

    def _end_move_drag(self) -> None:
        self._move_drag_object = None

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
            target = clicked or selected
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
        self.move_gizmo_overlay.draw(painter, selected, self.world_to_viewport)
        painter.end()
