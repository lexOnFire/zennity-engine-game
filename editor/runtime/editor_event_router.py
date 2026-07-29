"""High-frequency Qt event routing for the isolated editor shell."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEvent, Qt


class EditorEventRouter:
    KEY_MAP = {
        Qt.Key_A: "left", Qt.Key_Left: "left",
        Qt.Key_D: "right", Qt.Key_Right: "right",
        Qt.Key_W: "up", Qt.Key_Up: "up",
        Qt.Key_S: "down", Qt.Key_Down: "down",
        Qt.Key_Space: "jump", Qt.Key_R: "restart",
    }
    PREVIEW_EXTENSIONS = {
        ".zanim", ".zanimator", ".zlogic", ".png", ".jpg", ".jpeg", ".bmp", ".webp",
    }
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

    def __init__(self, editor: Any) -> None:
        self.editor = editor

    def handle(self, watched: Any, event: Any) -> bool | None:
        handled = self._runtime_input(event)
        if handled is not None:
            return handled
        editor = self.editor
        if watched is editor.viewport_host and event.type() == QEvent.Resize:
            editor._pending_viewport_size = editor.native_viewport_size()
            editor._viewport_resize_timer.start()
        if watched not in editor._script_drop_targets:
            return None
        if editor._play_session.is_running and event.type() in {QEvent.DragEnter, QEvent.DragMove, QEvent.Drop}:
            event.ignore()
            return True
        if event.type() == QEvent.DragEnter:
            if event.source() is editor.assets_tree:
                path = editor._asset_browser.dragged_path()
                if path is not None and path.suffix.lower() in self.PREVIEW_EXTENSIONS:
                    event.acceptProposedAction()
                    return True
            return None
        if event.type() == QEvent.DragMove:
            if event.source() is editor.assets_tree:
                event.acceptProposedAction()
                return True
            return None
        if event.type() != QEvent.Drop or event.source() is not editor.assets_tree:
            return None
        return self._drop(watched, event)

    def _runtime_input(self, event: Any) -> bool | None:
        editor = self.editor
        key = self.KEY_MAP.get(event.key()) if event.type() in {
            QEvent.ShortcutOverride, QEvent.KeyPress, QEvent.KeyRelease,
        } else None
        if not editor._runtime_playing or key is None:
            return None
        if event.type() == QEvent.ShortcutOverride:
            event.accept()
            return True
        if not event.isAutoRepeat():
            pressed = event.type() == QEvent.KeyPress
            editor._runtime_keys[key] = pressed
            editor._commands.put({"type": "runtime_input", "keys": dict(editor._runtime_keys)})
            editor.statusBar().showMessage(f"Play Input: {key} {'ON' if pressed else 'OFF'}")
        return True

    def _drop(self, watched: Any, event: Any) -> bool | None:
        editor = self.editor
        path = editor._asset_browser.dragged_path()
        if path is None:
            return None
        extension = path.suffix.lower()
        if extension == ".zanim":
            target = self._target_name(watched, event)
            if target in editor._objects_by_name:
                editor._apply_animation_asset_path_to_object(path, target)
                return self._accept(event)
        elif extension == ".zanimator":
            target = self._target_name(watched, event)
            if target in editor._objects_by_name:
                editor._apply_animator_controller_path(path, target)
                return self._accept(event)
        elif watched is editor.viewport_host and extension in self.IMAGE_EXTENSIONS:
            pos = event.position()
            scale = max(1.0, float(editor.viewport_host.devicePixelRatioF()))
            editor._create_sprite_at(path, float(pos.x()) * scale, float(pos.y()) * scale)
            return self._accept(event)
        return None

    def _target_name(self, watched: Any, event: Any) -> str | None:
        editor = self.editor
        if watched not in editor._hierarchy_drop_targets:
            return editor._selected_name
        position = editor.hierarchy_tree.viewport().mapFromGlobal(event.globalPosition().toPoint())
        item = editor.hierarchy_tree.itemAt(position)
        name = editor._hierarchy_item_name(item)
        return name if name in editor._objects_by_name else editor._selected_name

    @staticmethod
    def _accept(event: Any) -> bool:
        event.acceptProposedAction()
        return True
