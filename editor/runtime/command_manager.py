from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


class Command(Protocol):
    """Contrato para acoes reversiveis do editor."""

    description: str

    def execute(self) -> None:
        ...

    def undo(self) -> None:
        ...


@dataclass
class FunctionCommand:
    """Comando simples para encapsular pares execute/undo."""

    description: str
    do: Callable[[], None]
    undo_action: Callable[[], None]

    def execute(self) -> None:
        self.do()

    def undo(self) -> None:
        self.undo_action()


class CommandManager:
    """Gerencia undo/redo usando Command Pattern."""

    def __init__(self, limit: int = 100) -> None:
        self.limit = limit
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def execute(self, command: Command) -> None:
        command.execute()
        self._undo_stack.append(command)
        if len(self._undo_stack) > self.limit:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)

    def redo(self) -> None:
        if not self._redo_stack:
            return
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()
