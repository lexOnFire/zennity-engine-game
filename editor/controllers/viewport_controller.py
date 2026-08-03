"""Viewport command facade for Phase 1 editor controllers."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from editor.runtime.tool_manager import EditorTool


class ViewportController:
    """Centralizes viewport commands and related status feedback."""

    def __init__(self, host: Any) -> None:
        self.host = host

    def set_tool(self, tool: EditorTool | str) -> None:
        tool_value = tool.value if isinstance(tool, EditorTool) else str(tool)
        self.send({"type": "set_tool", "tool": tool_value})
        self.show_status(f"Ferramenta ativa: {tool_value.title()}")

    def focus_selected(self) -> None:
        self.send({"type": "focus_selected"})
        self.show_status("Foco no objeto selecionado")

    def toggle_grid(self) -> None:
        self.send({"type": "toggle_grid"})
        self.show_status("Grade alternada")

    def set_snap(self, enabled: bool, *, size: float = 16.0, angle: float = 15.0) -> None:
        self.send({
            "type": "set_snap",
            "enabled": bool(enabled),
            "size": float(size),
            "angle": float(angle),
        })
        self.show_status("Snap ativado" if enabled else "Snap desativado")

    def send(self, message: Mapping[str, Any]) -> None:
        self.host._commands.put(dict(message))

    def show_status(self, message: str) -> None:
        status_bar = getattr(self.host, "statusBar", None)
        if callable(status_bar):
            status_bar().showMessage(message)
