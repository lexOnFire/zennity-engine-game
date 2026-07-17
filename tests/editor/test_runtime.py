from __future__ import annotations

from editor.runtime import CommandManager, EditorContext, EditorTool, FunctionCommand
from editor.runtime.selection_manager import SelectionManager
from editor.runtime.tool_manager import ToolManager


def test_selection_manager_notifies_only_on_change() -> None:
    manager = SelectionManager()
    calls = []
    selected = object()

    manager.subscribe(calls.append)
    manager.set_selected(selected)
    manager.set_selected(selected)
    manager.clear()

    assert calls == [selected, None]


def test_tool_manager_tracks_active_tool() -> None:
    manager = ToolManager()
    calls = []

    manager.subscribe(calls.append)
    manager.set_active_tool("move")

    assert manager.active_tool == EditorTool.MOVE
    assert calls == [EditorTool.MOVE]


def test_command_manager_executes_undo_and_redo() -> None:
    values = []
    manager = CommandManager()
    command = FunctionCommand(
        "append value",
        do=lambda: values.append("done"),
        undo_action=lambda: values.pop(),
    )

    manager.execute(command)
    assert values == ["done"]
    assert manager.can_undo is True

    manager.undo()
    assert values == []
    assert manager.can_redo is True

    manager.redo()
    assert values == ["done"]


def test_editor_context_resets_scene_state() -> None:
    context = EditorContext()
    selected = object()
    context.selection.set_selected(selected)
    context.state.is_playing = True

    context.reset_scene_state()

    assert context.selection.selected is None
    assert context.state.is_playing is False
