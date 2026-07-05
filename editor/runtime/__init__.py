"""Runtime do editor Zennity.

Este pacote centraliza estado e serviços compartilhados do editor.
"""

from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.runtime.editor_context import EditorContext
from editor.runtime.editor_state import EditorState
from editor.runtime.selection_manager import SelectionManager
from editor.runtime.tool_manager import EditorTool, ToolManager

__all__ = [
    "CommandManager",
    "EditorContext",
    "EditorState",
    "EditorTool",
    "FunctionCommand",
    "SelectionManager",
    "ToolManager",
]
