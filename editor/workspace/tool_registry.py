"""Tool Registry — registra ferramentas internas do editor.

Cada ferramenta possui: dock, toolbar, atalhos, comandos e menu.
A ferramenta ativa controla viewport, atalhos e gizmos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolDefinition:
    """Definição completa de uma ferramenta do editor.

    Uma ferramenta não é apenas uma dock: ela possui dock,
    toolbar associada, atalhos, comandos e entrada de menu.

    Atributos:
        id        — identificador único da ferramenta
        label     — nome exibido na UI
        dock      — QDockWidget associado (opcional)
        toolbar   — QToolBar específico da ferramenta (opcional)
        shortcuts — lista de atalhos de teclado
        commands  — lista de action IDs disponíveis quando a ferramenta está ativa
        menu      — categoria de menu onde a ferramenta aparece
        icon      — nome do ícone
        category  — categoria de agrupamento ("Editor", "Produção", "Debug", etc.)
    """
    id: str
    label: str
    dock: Any = None
    toolbar: Any = None
    shortcuts: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    menu: str = "Janela"
    icon: str = ""
    category: str = "Editor"


class ToolRegistry:
    """Registro central de todas as ferramentas do editor."""

    _instance: ToolRegistry | None = None

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._active_tool_id: str | None = None

    @classmethod
    def instance(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.id] = tool

    def get(self, tool_id: str) -> ToolDefinition | None:
        return self._tools.get(tool_id)

    def activate(self, tool_id: str) -> ToolDefinition | None:
        tool = self._tools.get(tool_id)
        if tool is None:
            return None
        self._active_tool_id = tool_id

        if tool.dock:
            try:
                tool.dock.show()
                tool.dock.raise_()
            except Exception:
                pass

        try:
            from editor.core.event_bus import EventBus
            EventBus.emit("Workspace.panel_opened", tool_id=tool_id, label=tool.label)
        except Exception:
            pass

        return tool

    @property
    def active_tool(self) -> ToolDefinition | None:
        if self._active_tool_id:
            return self._tools.get(self._active_tool_id)
        return None

    def all_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def by_category(self, category: str) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.category == category]
