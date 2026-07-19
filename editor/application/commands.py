"""Command infrastructure for deterministic editor mutations.

The module is intentionally independent from Qt and Pygame so commands can be
unit-tested and later reused by alternative editor frontends.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .scene_manager import SceneManager


class EditorCommand(Protocol):
    """A reversible editor mutation."""

    def execute(self) -> None: ...

    def undo(self) -> None: ...


@dataclass(slots=True)
class CommandHistory:
    """Owns undo/redo stacks and is the only coordinator for command replay."""

    undo_stack: list[EditorCommand] = field(default_factory=list)
    redo_stack: list[EditorCommand] = field(default_factory=list)

    def execute(self, command: EditorCommand) -> None:
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()

    def undo(self) -> bool:
        if not self.undo_stack:
            return False
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            return False
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        return True

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()


@dataclass(slots=True)
class RenameObjectCommand:
    scene: SceneManager
    old_name: str
    new_name: str

    def execute(self) -> None:
        self.scene.rename(self.old_name, self.new_name)

    def undo(self) -> None:
        self.scene.rename(self.new_name, self.old_name)


@dataclass(slots=True)
class AddObjectCommand:
    scene: SceneManager
    object_data: dict

    def execute(self) -> None:
        self.scene.add(self.object_data)

    def undo(self) -> None:
        self.scene.remove(str(self.object_data["name"]))


@dataclass(slots=True)
class RemoveObjectCommand:
    scene: SceneManager
    object_name: str
    _removed: dict | None = None

    def execute(self) -> None:
        self._removed = self.scene.remove(self.object_name)

    def undo(self) -> None:
        if self._removed is None:
            raise RuntimeError("cannot undo a command that was not executed")
        self.scene.add(self._removed)
