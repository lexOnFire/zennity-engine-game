from __future__ import annotations

from editor.runtime.command_manager import CommandManager
from editor.runtime.editor_state import EditorState
from editor.runtime.selection_manager import SelectionManager
from editor.runtime.tool_manager import ToolManager


from pathlib import Path


class EditorContext:
    """Container explicito dos servicos de runtime do editor."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.state = EditorState()
        self.selection = SelectionManager()
        self.tools = ToolManager()
        self.commands = CommandManager()

    def reset_scene_state(self) -> None:
        self.selection.clear()
        self.commands.clear()
        self.state.is_playing = False
