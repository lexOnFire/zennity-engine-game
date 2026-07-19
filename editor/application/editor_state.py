"""Qt/Pygame-independent state for one editor session."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SceneObject = dict[str, Any]


@dataclass(slots=True)
class EditorState:
    """Mutable state owned by one editor session.

    Keeping this object free from UI dependencies makes state transitions
    independently testable and prevents the main window from becoming the
    permanent owner of every subsystem.
    """

    scene_document: dict[str, Any] | None = None
    current_scene_path: Path | None = None
    selected_name: str | None = None
    runtime_playing: bool = False
    snap_enabled: bool = False
    updating_inspector: bool = False
    runtime_objects_by_name: dict[str, SceneObject] = field(default_factory=dict)

    def select(self, object_name: str | None) -> None:
        self.selected_name = None if object_name is None else str(object_name)

    def clear_selection(self) -> None:
        self.selected_name = None

    def begin_play_mode(self) -> None:
        self.runtime_playing = True
        self.runtime_objects_by_name.clear()

    def end_play_mode(self) -> None:
        self.runtime_playing = False
        self.runtime_objects_by_name.clear()

    def set_scene_path(self, path: str | Path | None) -> None:
        self.current_scene_path = None if path is None else Path(path)
