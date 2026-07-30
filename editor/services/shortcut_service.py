"""Centralized keyboard shortcut registration for the editor shell."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut


@dataclass(frozen=True)
class ShortcutBinding:
    """A shortcut and the command it should trigger."""

    command_id: str
    sequence: str
    description: str = ""


class ShortcutService:
    """Owns application-wide shortcuts so controllers do not duplicate them."""

    STANDARD_BINDINGS = (
        ShortcutBinding("tool.select", "Q", "Select"),
        ShortcutBinding("tool.move", "W", "Move"),
        ShortcutBinding("tool.rotate", "E", "Rotate"),
        ShortcutBinding("tool.scale", "R", "Scale"),
        ShortcutBinding("edit.duplicate", "Ctrl+D", "Duplicate"),
        ShortcutBinding("edit.undo", "Ctrl+Z", "Undo"),
        ShortcutBinding("edit.redo", "Ctrl+Y", "Redo"),
        ShortcutBinding("edit.delete", "Delete", "Delete"),
        ShortcutBinding("viewport.focus_selected", "F", "Focus selected"),
        ShortcutBinding("viewport.toggle_grid", "G", "Toggle grid"),
    )

    def __init__(self, host: Any) -> None:
        self.host = host
        self._shortcuts: list[QShortcut] = []
        self._shortcuts_by_command: dict[str, QShortcut] = {}

    @property
    def shortcuts(self) -> tuple[QShortcut, ...]:
        return tuple(self._shortcuts)

    def shortcut_for(self, command_id: str) -> QShortcut | None:
        return self._shortcuts_by_command.get(command_id)

    def bind_action(self, action: QAction, sequence: str) -> None:
        action.setShortcut(QKeySequence(sequence))
        action.setShortcutContext(Qt.ApplicationShortcut)

    def register(
        self,
        bindings: Iterable[ShortcutBinding],
        handlers: dict[str, Callable[[], None]],
    ) -> None:
        for binding in bindings:
            handler = handlers.get(binding.command_id)
            if handler is None:
                continue
            shortcut = QShortcut(QKeySequence(binding.sequence), self.host)
            shortcut.setContext(Qt.ApplicationShortcut)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)
            self._shortcuts_by_command[binding.command_id] = shortcut
