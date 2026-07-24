from __future__ import annotations

from enum import Enum
from typing import Callable


class EditorTool(str, Enum):
    SELECT = "select"
    MOVE = "move"
    ROTATE = "rotate"
    SCALE = "scale"
    RECT = "rect"
    PAN = "pan"
    ZOOM = "zoom"


ToolListener = Callable[[EditorTool], None]


class ToolManager:
    """Fonte unica de verdade para a ferramenta ativa do editor."""

    def __init__(self, initial_tool: EditorTool = EditorTool.SELECT) -> None:
        self._active_tool = initial_tool
        self._listeners: list[ToolListener] = []

    @property
    def active_tool(self) -> EditorTool:
        return self._active_tool

    def set_active_tool(self, tool: EditorTool | str) -> None:
        next_tool = tool if isinstance(tool, EditorTool) else EditorTool(str(tool))
        if next_tool == self._active_tool:
            return
        self._active_tool = next_tool
        self._notify()

    def subscribe(self, callback: ToolListener) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: ToolListener) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self) -> None:
        for callback in list(self._listeners):
            callback(self._active_tool)
