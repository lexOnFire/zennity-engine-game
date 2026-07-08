from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass
class BatchCommand:
    """Agrupa varios comandos em um unico step de undo/redo.

    Util para operacoes que alteram multiplas propriedades ao mesmo tempo
    (ex: mover um objeto altera x e y em conjunto).
    """

    description: str
    commands: list[Command] = field(default_factory=list)

    def execute(self) -> None:
        for cmd in self.commands:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self.commands):
            cmd.undo()


class CommandManager:
    """Gerencia undo/redo usando Command Pattern.

    Callbacks de refresh:
        on_after_execute(cmd)  -- chamado apos todo execute/redo
        on_after_undo(cmd)     -- chamado apos todo undo
        on_after_redo(cmd)     -- chamado apos todo redo (alem de on_after_execute)

    A UI pode se inscrever nesses callbacks para sincronizar Inspector,
    Viewport e estado dos botoes de undo/redo sem patches dispersos.
    """

    def __init__(self, limit: int = 100) -> None:
        self.limit = limit
        self._undo_stack: list[Command] = []
        self._redo_stack: list[Command] = []
        self.on_after_execute: list[Callable[[Command], None]] = []
        self.on_after_undo: list[Callable[[Command], None]] = []
        self.on_after_redo: list[Callable[[Command], None]] = []

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    @property
    def undo_description(self) -> str:
        return self._undo_stack[-1].description if self._undo_stack else ""

    @property
    def redo_description(self) -> str:
        return self._redo_stack[-1].description if self._redo_stack else ""

    # ------------------------------------------------------------------
    # Operacoes principais
    # ------------------------------------------------------------------

    def execute(self, command: Command) -> None:
        """Executa um comando e empurra para o stack de undo.

        O redo stack e limpo porque a linha do tempo mudou.
        """
        command.execute()
        self._undo_stack.append(command)
        if len(self._undo_stack) > self.limit:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._fire(self.on_after_execute, command)

    def undo(self) -> str:
        """Desfaz o ultimo comando. Retorna a descricao ou string vazia."""
        if not self._undo_stack:
            return ""
        command = self._undo_stack.pop()
        command.undo()
        self._redo_stack.append(command)
        self._fire(self.on_after_undo, command)
        self._fire(self.on_after_execute, command)
        return command.description

    def redo(self) -> str:
        """Refaz o ultimo comando desfeito. Retorna a descricao ou string vazia."""
        if not self._redo_stack:
            return ""
        command = self._redo_stack.pop()
        command.execute()
        self._undo_stack.append(command)
        self._fire(self.on_after_redo, command)
        self._fire(self.on_after_execute, command)
        return command.description

    def clear(self) -> None:
        self._undo_stack.clear()
        self._redo_stack.clear()

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _fire(listeners: list[Callable], arg: Command) -> None:
        for cb in list(listeners):
            try:
                cb(arg)
            except Exception:
                pass
