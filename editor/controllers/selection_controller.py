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
