from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Any

import pygame
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent, QPainter
from PySide6.QtWidgets import QWidget


class GameViewportWidget(QWidget):
    """Lightweight Game tab renderer.

    The Scene tab uses the editor's QOpenGLWidget viewport. The Game tab avoids
    creating a second OpenGL/Pygame viewport, which can crash native backends on
    Windows while the Qt event loop is running.
    """

    tool_message_requested = Signal(str)
    history_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GameViewportCanvas")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        pygame.init()
        pygame.font.init()

        self.viewmodel = None
        self.tool_manager = None
        self.editor_state = None
        self.command_manager = None
        self.runtime_manager = None
        self.active_scene: Any | None = None
        self.view_mode = "game"
        self.pg_surface: pygame.Surface | None = None
        self._vp_w = 800
        self._vp_h = 600
        self._last_time = time.time()
        self._qt_mouse_pos: tuple[int, int] = (0, 0)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def set_viewmodel(self, viewmodel) -> None:
        self.viewmodel = viewmodel

    def set_tool_manager(self, tool_manager) -> None:
        self.tool_manager = tool_manager

    def set_editor_state(self, editor_state) -> None:
        self.editor_state = editor_state

    def set_command_manager(self, command_manager) -> None:
        self.command_manager = command_manager

    def set_runtime_manager(self, runtime_manager) -> None:
        self.runtime_manager = runtime_manager

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = "game"

    def is_game_view(self) -> bool:
        return True

    def resizeGL(self, w: int, h: int) -> None:
        self._resize_surface(w, h)

    def resizeEvent(self, event) -> None:
        self._resize_surface(self.width(), self.height())
        super().resizeEvent(event)

    def _resize_surface(self, w: int, h: int) -> None:
        self._vp_w = max(32, int(w))
        self._vp_h = max(32, int(h))
        self.pg_surface = pygame.Surface((self._vp_w, self._vp_h), pygame.SRCALPHA)
        self._apply_qt_shims()

    def _sync_model_from_scene(self) -> None:
        return None

    def _apply_qt_shims(self) -> None:
        target = getattr(self.active_scene, "scene", self.active_scene)
        if target is None:
            return
        if hasattr(target, "_layout"):
            widget = self

            def _game_layout(_w=widget):
                w, h = _w._vp_w, _w._vp_h
                return {
                    "sw": w,
                    "sh": h,
                    "vp_left": 0,
                    "vp_top": 0,
                    "vp_right": w,
                    "vp_bottom": h,
                    "vp_w": w,
                    "vp_h": h,
                    "panel_left_w": 0,
                    "panel_right_x": w,
                    "panel_right_w": 0,
                    "status_y": h,
                }

            target._layout = _game_layout

    def _grid_state_targets(self) -> list[Any]:
        if self.active_scene is None:
            return []
        targets = [self.active_scene]
        inner_scene = getattr(self.active_scene, "scene", None)
        if inner_scene is not None and inner_scene is not self.active_scene:
            targets.append(inner_scene)
        return targets

    def _capture_grid_state(self) -> list[tuple[Any, bool]]:
        states: list[tuple[Any, bool]] = []
        for target in self._grid_state_targets():
            states.append((target, bool(getattr(target, "show_grid", True))))
        return states

    def _set_grid_visible(self, visible: bool) -> None:
        for target in self._grid_state_targets():
            if hasattr(target, "show_grid"):
                target.show_grid = bool(visible)

    def _restore_grid_state(self, states: list[tuple[Any, bool]]) -> None:
        for target, visible in states:
            if hasattr(target, "show_grid"):
                target.show_grid = visible

    def paintEvent(self, event) -> None:
        if self.pg_surface is None:
            self._resize_surface(self.width(), self.height())
        if self.pg_surface is None:
            return
        self.pg_surface.fill((18, 20, 26))
        if self.active_scene is not None:
            grid_state = self._capture_grid_state()
            self._set_grid_visible(False)
            try:
                self.active_scene.draw(self.pg_surface)
            finally:
                self._restore_grid_state(grid_state)

        raw = pygame.image.tostring(self.pg_surface, "RGBA")
        img = QImage(raw, self._vp_w, self._vp_h, self._vp_w * 4, QImage.Format_RGBA8888)
        painter = QPainter(self)
        painter.drawImage(0, 0, img)

        playing = False
        if self.active_scene and bool(getattr(self.active_scene, "playing", False)):
            playing = True
        elif self.runtime_manager and getattr(self.runtime_manager, "is_playing", False):
            playing = True

        if playing:
            from PySide6.QtGui import QPen, QColor, QFont
            import math
            opacity = int(120 + 70 * math.sin(time.time() * 5.0))
            pen = QPen(QColor(0, 173, 181, opacity), 3)
            painter.setPen(pen)
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)

            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.setPen(QColor(0, 173, 181, 220))
            painter.drawText(self.width() - 130, 24, "PLAY MODE ACTIVE")

        painter.end()

    def _tick(self) -> None:
        now = time.time()
        dt = min(now - self._last_time, 0.1)
        self._last_time = now
        runtime_active = (
            self.runtime_manager is not None
            and getattr(self.runtime_manager, "is_playing", False)
            and getattr(self.runtime_manager, "runtime_scene", None) is self.active_scene
        )
        if not runtime_active and not self.isVisible():
            return
        if runtime_active:
            self.runtime_manager.tick(dt)
        elif self.active_scene is not None and bool(getattr(self.active_scene, "playing", False)):
            self.active_scene.update(dt)
        self.update()

    def closeEvent(self, event) -> None:
        self.shutdown()
        super().closeEvent(event)

    def shutdown(self) -> None:
        self._timer.stop()
        self.pg_surface = None

    def _qt_btn_to_pg(self, btn: Qt.MouseButton) -> int:
        if btn == Qt.LeftButton:
            return 1
        if btn == Qt.MiddleButton:
            return 2
        if btn == Qt.RightButton:
            return 3
        return 0

    def _runtime_input_active(self) -> bool:
        return bool(
            self.runtime_manager is not None
            and getattr(self.runtime_manager, "is_playing", False)
            and getattr(self.runtime_manager, "runtime_scene", None) is self.active_scene
        )

    def _forward_runtime_input(self, event_type: str, **payload) -> None:
        if self._runtime_input_active():
            self.runtime_manager.handle_input_event(SimpleNamespace(type=event_type, **payload))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._qt_mouse_pos = (event.x(), event.y())
        self._forward_runtime_input(
            "mouse_down",
            pos=self._qt_mouse_pos,
            button=self._qt_btn_to_pg(event.button()),
        )
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._qt_mouse_pos = (event.x(), event.y())
        self._forward_runtime_input(
            "mouse_up",
            pos=self._qt_mouse_pos,
            button=self._qt_btn_to_pg(event.button()),
        )
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        previous = self._qt_mouse_pos
        self._qt_mouse_pos = (event.x(), event.y())
        self._forward_runtime_input(
            "mouse_move",
            pos=self._qt_mouse_pos,
            rel=(self._qt_mouse_pos[0] - previous[0], self._qt_mouse_pos[1] - previous[1]),
        )
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self._forward_runtime_input("key_down", key=str(int(event.key())))
        event.accept()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        self._forward_runtime_input("key_up", key=str(int(event.key())))
        event.accept()
