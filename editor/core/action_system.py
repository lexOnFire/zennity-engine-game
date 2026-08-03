"""Editor Action System — uma ação reutilizada em menu, toolbar, atalho e palette.

Em vez de cada botão chamar uma função diretamente, tudo passa por
EditorAction → CommandManager → undo/redo.

Uso:
    registry = ActionRegistry.instance()
    registry.register(EditorAction(
        id="scene.new",
        label="Nova Cena",
        shortcut="Ctrl+N",
        handler=editor.new_scene,
    ))

    # Em qualquer menu, toolbar ou palette:
    action = registry.get("scene.new")
    action.trigger()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class EditorAction:
    """Definição de uma ação do editor.

    Uma mesma instância pode ser adicionada ao menu, toolbar, context menu
    e command palette sem duplicar código.
    """
    id: str
    label: str
    handler: Callable[..., Any]
    shortcut: str = ""
    icon: str = ""
    tooltip: str = ""
    category: str = "Geral"
    checkable: bool = False
    checked: bool = False
    enabled: bool = True
    tags: list[str] = field(default_factory=list)

    def trigger(self, *args: Any, **kwargs: Any) -> Any:
        """Executa o handler da ação."""
        if not self.enabled:
            return None
        return self.handler(*args, **kwargs)

    def to_qaction(self, parent: Any = None) -> Any:
        """Cria um QAction compatível com PySide6 a partir desta EditorAction."""
        try:
            from PySide6.QtGui import QAction, QKeySequence
            act = QAction(self.label, parent)
            if self.shortcut:
                act.setShortcut(QKeySequence(self.shortcut))
            if self.tooltip:
                act.setStatusTip(self.tooltip)
            if self.checkable:
                act.setCheckable(True)
                act.setChecked(self.checked)
            act.triggered.connect(self.trigger)
            return act
        except ImportError:
            return None


class ActionRegistry:
    """Registro central de todas as ações do editor."""

    _instance: ActionRegistry | None = None

    def __init__(self) -> None:
        self._actions: dict[str, EditorAction] = {}

    @classmethod
    def instance(cls) -> ActionRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, action: EditorAction) -> None:
        self._actions[action.id] = action

    def get(self, action_id: str) -> EditorAction | None:
        return self._actions.get(action_id)

    def trigger(self, action_id: str, *args: Any, **kwargs: Any) -> Any:
        action = self.get(action_id)
        if action:
            return action.trigger(*args, **kwargs)
        return None

    def all_actions(self) -> list[EditorAction]:
        return list(self._actions.values())

    def by_category(self, category: str) -> list[EditorAction]:
        return [a for a in self._actions.values() if a.category == category]

    def search(self, query: str) -> list[EditorAction]:
        q = query.lower()
        return [
            a for a in self._actions.values()
            if q in a.label.lower() or any(q in t for t in a.tags)
        ]
