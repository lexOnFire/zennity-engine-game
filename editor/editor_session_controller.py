"""Lifecycle infrastructure for the isolated editor window."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget

from editor.runtime.editor_event_router import EditorEventRouter


class EditorSessionController:
    """Own timers, event filters and viewport-process teardown."""

    def __init__(self, editor: Any) -> None:
        self.editor = editor
        self._configured = False
        self._closed = False
        self._filter_targets: set[Any] = set()

    def configure(self) -> None:
        if self._configured:
            return
        editor = self.editor
        editor._pending_viewport_size = None
        editor._last_viewport_size_sent = None
        editor._viewport_resize_timer = self._timer(
            editor._flush_viewport_resize, interval=24, single_shot=True,
        )

        editor.assets_tree.setDragEnabled(True)
        editor.viewport_host.setAcceptDrops(True)
        editor._hierarchy_drop_targets = {
            editor.hierarchy_tree, editor.hierarchy_tree.viewport(),
        }
        editor._inspector_drop_targets = {
            editor.inspector_panel, *editor.inspector_panel.findChildren(QWidget),
        }
        editor._scene_drop_targets = {
            editor.viewport_tabs, editor.viewport_tabs.tabBar(), editor.viewport_host,
        }
        editor._script_drop_targets = (
            editor._hierarchy_drop_targets
            | editor._inspector_drop_targets
            | editor._scene_drop_targets
        )
        editor._event_router = EditorEventRouter(editor)
        self._filter_targets = set(editor._script_drop_targets)
        for target in self._filter_targets:
            target.setAcceptDrops(True)
            target.installEventFilter(editor)
        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(editor)

        editor._event_timer = self._timer(editor._read_viewport_events, interval=33)
        editor._animator_preview_timer = self._timer(
            editor._tick_animation_preview, interval=125,
        )
        self._configured = True

    def _timer(self, callback: Any, *, interval: int, single_shot: bool = False) -> QTimer:
        timer = QTimer(self.editor)
        timer.setSingleShot(single_shot)
        timer.setInterval(interval)
        timer.timeout.connect(callback)
        if not single_shot:
            timer.start()
        return timer

    def attach_viewport_process(self, process: Any) -> None:
        self.editor._viewport_controller.attach(process)
        self.editor._viewport_process = process
        self._closed = False

    def native_viewport_size(self) -> tuple[int, int]:
        host = self.editor.viewport_host
        scale = max(1.0, float(host.devicePixelRatioF()))
        return max(32, round(host.width() * scale)), max(32, round(host.height() * scale))

    def handle_event(self, watched: Any, event: Any) -> bool | None:
        return self.editor._event_router.handle(watched, event)

    def flush_viewport_resize(self) -> None:
        editor = self.editor
        size = editor._pending_viewport_size
        editor._pending_viewport_size = None
        if size is None or size == editor._last_viewport_size_sent:
            return
        editor._last_viewport_size_sent = size
        editor._commands.put({"type": "viewport_size", "w": size[0], "h": size[1]})

    def shutdown(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._configured:
            for timer_name in (
                "_viewport_resize_timer", "_event_timer", "_animator_preview_timer",
            ):
                timer = getattr(self.editor, timer_name, None)
                if timer is not None:
                    timer.stop()
            for target in self._filter_targets:
                target.removeEventFilter(self.editor)
            application = QApplication.instance()
            if application is not None:
                application.removeEventFilter(self.editor)
        for controller_name in (
            "_inspector_controller",
            "_hierarchy_controller",
            "_asset_browser",
            "_console_controller",
        ):
            controller = getattr(self.editor, controller_name, None)
            disconnect = getattr(controller, "disconnect", None)
            if callable(disconnect):
                disconnect()
        self.editor._viewport_controller.shutdown()
