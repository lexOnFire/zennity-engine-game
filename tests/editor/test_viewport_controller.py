from types import SimpleNamespace

from editor.controllers.viewport_controller import ViewportController
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
        super().__init__(_commands=_Commands())
        self.status = _Status()

    def statusBar(self) -> _Status:
        return self.status


def test_viewport_controller_sends_tool_focus_grid_and_snap_commands() -> None:
    host = _Host()
    controller = ViewportController(host)

    controller.set_tool(EditorTool.ROTATE)
    controller.focus_selected()
    controller.toggle_grid()
    controller.set_snap(True, size=32, angle=45)

    assert host._commands.items == [
        {"type": "set_tool", "tool": "rotate"},
        {"type": "focus_selected"},
        {"type": "toggle_grid"},
        {"type": "set_snap", "enabled": True, "size": 32.0, "angle": 45.0},
    ]
    assert host.status.messages == [
        "Ferramenta ativa: Rotate",
        "Foco no objeto selecionado",
        "Grade alternada",
        "Snap ativado",
    ]
