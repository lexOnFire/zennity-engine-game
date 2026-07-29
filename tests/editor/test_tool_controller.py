from types import SimpleNamespace

from editor.controllers.tool_controller import ToolController
from editor.runtime.editor_context import EditorContext
from editor.runtime.tool_manager import EditorTool


class _Commands:
    def __init__(self) -> None:
        self.items = []

    def put(self, item: dict) -> None:
        self.items.append(item)


class _Status:
    def __init__(self) -> None:
        self.messages = []

    def showMessage(self, message: str) -> None:
        self.messages.append(message)


class _Host(SimpleNamespace):
    def __init__(self) -> None:
        super().__init__(
            editor_context=EditorContext(),
            _commands=_Commands(),
            _tool_actions={},
            _selected_name=None,
        )
        self.status = _Status()

    def statusBar(self) -> _Status:
        return self.status


def test_tool_controller_activates_tool_manager_and_viewport_command() -> None:
    host = _Host()
    controller = ToolController(host)

    controller.activate_tool(EditorTool.MOVE)

    assert host.editor_context.tools.active_tool == EditorTool.MOVE
    assert host._commands.items == [{"type": "set_tool", "tool": "move"}]
    assert host.status.messages[-1] == "Ferramenta ativa: Move"


def test_tool_controller_focus_and_grid_are_viewport_commands() -> None:
    host = _Host()
    controller = ToolController(host)

    controller.focus_selected()
    controller.toggle_grid()

    assert host._commands.items == [{"type": "focus_selected"}, {"type": "toggle_grid"}]
