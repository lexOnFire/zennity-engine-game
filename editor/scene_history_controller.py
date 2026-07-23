"""Undo/redo transaction and scene restoration coordination."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


class SceneHistoryController:
    """Bridges the bounded delta history with editor scene presentation."""

    def __init__(self, host: Any) -> None:
        self.host = host

    def record(self, before: list[dict] | None = None) -> None:
        h = self.host
        if before is None:
            h._scene_history.begin(h._scene_snapshot)
        else:
            h._scene_history.commit(before, h._scene_snapshot)
        self.sync_actions()

    def restore(self, snapshot: list[dict]) -> None:
        h = self.host
        h._scene_snapshot = deepcopy(snapshot)
        h._objects_by_name = {item["name"]: item for item in h._scene_snapshot}
        if h._selected_name not in h._objects_by_name:
            h._selected_name = None
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        if h._selected_name is not None:
            h._scene_controller.select(h._selected_name)
            h._update_inspector(h._selected_name)
        else:
            h._clear_inspector_view()
        self.sync_actions()

    def undo(self) -> bool:
        restored = self.host._scene_history.undo(self.host._scene_snapshot)
        if restored is None:
            self.sync_actions()
            return False
        self.restore(restored)
        return True

    def redo(self) -> bool:
        restored = self.host._scene_history.redo(self.host._scene_snapshot)
        if restored is None:
            self.sync_actions()
            return False
        self.restore(restored)
        return True

    def sync_actions(self) -> None:
        """Keep Edit menu actions aligned with the actual history state."""
        actions = getattr(self.host, "toolbar_actions", {})
        undo_action = actions.get("Desfazer")
        redo_action = actions.get("Refazer")
        editing_locked = bool(getattr(self.host, "_runtime_playing", False))
        if undo_action is not None:
            undo_action.setEnabled(not editing_locked and self.host._scene_history.can_undo)
        if redo_action is not None:
            redo_action.setEnabled(not editing_locked and self.host._scene_history.can_redo)
