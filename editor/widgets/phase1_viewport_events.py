"""Mixin de manipulação de eventos de mouse para Phase1ViewportWidget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent

from editor.runtime.tool_manager import EditorTool
from editor.widgets.viewport_gizmo_helpers import (
    event_position,
    move_axis_at,
    request_editor_frame,
    sync_camera_to_engine,
)


class Phase1ViewportEventsMixin:
    """Isola o tratamento de mousePress, mouseMove e mouseRelease do viewport."""

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.is_game_view() or self._is_playing():
            super().mousePressEvent(event)
            return

        tool = self._active_tool()
        x, y = event_position(event)

        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_last_mouse = (x, y)
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        if tool == EditorTool.SELECT:
            self.select_object(self._object_at_viewport_point(x, y))
            event.accept()
            return

        if tool == EditorTool.MOVE:
            selected = self._selected_transform_object()
            axis = move_axis_at(self, x, y, selected)
            target = selected if axis is not None else self._object_at_viewport_point(x, y)
            if target is not None and self._begin_move_drag(target, x, y):
                self._move_axis_lock = axis
                event.accept()
                return
            event.accept()
            return

        if tool == EditorTool.ROTATE:
            clicked = self._object_at_viewport_point(x, y)
            selected = self._selected_transform_object()
            target = clicked
            if target is None and self._rotate_gizmo_hit_at_viewport_point(x, y, selected):
                target = selected
            if target is not None and self._begin_rotate_drag(target, x, y):
                event.accept()
                return
            event.accept()
            return

        if tool == EditorTool.SCALE:
            selected = self._selected_transform_object()
            handle_idx = self._scale_handle_at_viewport_point(x, y, selected)
            if selected is not None and handle_idx is not None and self._begin_scale_drag(selected, x, y, handle_idx):
                event.accept()
                return
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.is_game_view() or self._is_playing():
            super().mouseMoveEvent(event)
            return

        x, y = event_position(event)

        if self._panning:
            dx = x - self._pan_last_mouse[0]
            dy = y - self._pan_last_mouse[1]
            self.camera.pan(dx, dy)
            self._pan_last_mouse = (x, y)
            sync_camera_to_engine(self)
            request_editor_frame(self)
            event.accept()
            return

        if self._active_tool() == EditorTool.MOVE and self._move_drag_object is not None:
            self._update_move_drag(x, y)
            event.accept()
            return

        if self._rotate_drag_object is not None:
            self._update_rotate_drag(x, y)
            event.accept()
            return

        if self._scale_drag_object is not None:
            self._update_scale_drag(x, y)
            event.accept()
            return

        self._update_hover_cursor(x, y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.is_game_view() or self._is_playing():
            super().mouseReleaseEvent(event)
            return

        if event.button() == Qt.MiddleButton and self._panning:
            self._panning = False
            self._update_hover_cursor(float(event.x()), float(event.y()))
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            if self._move_drag_object is not None:
                self._end_move_drag()
                event.accept()
                return
            if self._rotate_drag_object is not None:
                self._end_rotate_drag()
                event.accept()
                return
            if self._scale_drag_object is not None:
                self._end_scale_drag()
                event.accept()
                return

        super().mouseReleaseEvent(event)
