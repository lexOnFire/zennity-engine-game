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
        logic_workspace = getattr(h, "_logic_workspace_controller", None)
        if logic_workspace is not None:
            logic_workspace.selection_changed(name)
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

    def selected_scene_name(self) -> str | None:
        selected = self.selected_scene_object()
        return selected[0] if selected is not None else None

    def scene_object(self, name: str | None) -> dict[str, Any] | None:
        if not name:
            return None
        obj = self.host._objects_by_name.get(str(name))
        return obj if isinstance(obj, dict) else None

    def has_scene_object(self, name: str | None) -> bool:
        return self.scene_object(name) is not None

    def publish_scene(self) -> None:
        h = self.host
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def scene_objects(self) -> list[dict[str, Any]]:
        return self.host._scene_snapshot

    def append_scene_object(self, obj: dict[str, Any]) -> None:
        self.host._scene_snapshot.append(obj)
        name = obj.get("name")
        if name:
            self.host._objects_by_name[str(name)] = obj

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
