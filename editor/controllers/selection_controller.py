"""Editor selection facade for scene, hierarchy and inspector coordination."""
from __future__ import annotations

from typing import Any


class EditorSelectionController:
    """Centralizes selected-object state updates for Phase 1 controllers."""

    def __init__(self, host: Any) -> None:
        self.host = host

    def select(self, name: str, *, source: str = "Interface", inspect: bool = True) -> bool:
        h = self.host
        in_scene = name in h._objects_by_name
        in_runtime = h._runtime_playing and name in h._runtime_objects_by_name
        if not (in_scene or in_runtime):
            return False
        h._scene_controller.select(name)
        h._selected_name = name
        if inspect:
            h._update_inspector(name)
        h.statusBar().showMessage(f"{source}: {name} selecionado")
        return True

    def select_for_action(self, name: str) -> bool:
        h = self.host
        if name not in h._objects_by_name:
            return False
        h._selected_name = name
        return True

    def selected_scene_object(self) -> tuple[str, dict[str, Any]] | None:
        h = self.host
        name = h._selected_name
        if getattr(h, "_updating_inspector", False) or name not in h._objects_by_name:
            return None
        return str(name), h._objects_by_name[name]

    def publish_scene(self) -> None:
        h = self.host
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def publish_selected_change(self, *, select: bool = False, inspect: bool = False) -> None:
        h = self.host
        self.publish_scene()
        selected = self.selected_scene_object()
        if selected is None:
            return
        name, _obj = selected
        if select:
            h._scene_controller.select(name)
        if inspect:
            h._update_inspector(name)

    def refresh_inspector(self, name: str) -> None:
        self.host._update_inspector(name)
