"""Scene and selection IPC boundary for the isolated editor."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


class SceneSelectionController:
    """Publishes detached scene state so async queue serialization is race-free."""

    def __init__(self, commands: Any) -> None:
        self._commands = commands

    def publish_snapshot(self, objects: list[dict[str, Any]]) -> bool:
        return self._commands.put(
            {"type": "scene_snapshot", "objects": deepcopy(list(objects))}
        )

    def select(self, object_name: str | None) -> bool:
        return self._commands.put(
            {"type": "select_object", "name": object_name}
        )
