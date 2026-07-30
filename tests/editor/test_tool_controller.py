from types import SimpleNamespace

from PySide6.QtWidgets import QApplication, QGraphicsView, QMainWindow, QWidget

from editor.controllers.tool_controller import ToolController
from editor.runtime.editor_context import EditorContext
from editor.runtime.tool_manager import EditorTool


class _ViewportCommands:
    def __init__(self) -> None:
        self.calls = []

    def set_tool(self, tool: EditorTool | str) -> None:
        tool_value = tool.value if isinstance(tool, EditorTool) else str(tool)
        self.calls.append(("set_tool", tool_value))

    def focus_selected(self) -> None:
        self.calls.append(("focus_selected",))

    def toggle_grid(self) -> None:
        self.calls.append(("toggle_grid",))


class _Host(SimpleNamespace):
    def __init__(self) -> None:
        super().__init__(
            editor_context=EditorContext(),
            _viewport_commands=_ViewportCommands(),
            _tool_actions={},
            _selected_name=None,
        )


def test_tool_controller_activates_tool_manager_and_viewport_controller() -> None:
    host = _Host()
    controller = ToolController(host)

    controller.activate_tool(EditorTool.MOVE)

    assert host.editor_context.tools.active_tool == EditorTool.MOVE
    assert host._viewport_commands.calls == [("set_tool", "move")]


def test_tool_controller_focus_and_grid_are_viewport_controller_calls() -> None:
    host = _Host()
    controller = ToolController(host)

    controller.focus_selected()
    controller.toggle_grid()

    assert host._viewport_commands.calls == [("focus_selected",), ("toggle_grid",)]


def test_scene_shortcuts_are_blocked_for_graph_canvas_and_external_window() -> None:
    app = QApplication.instance() or QApplication([])
    host = QMainWindow()
    controller = ToolController(host)
    central = QWidget(host)
    host.setCentralWidget(central)
    graph = QGraphicsView(central)
    graph.setObjectName("LogicGraphView")
    regular = QWidget(central)
    external = QGraphicsView()

    try:
        assert not controller._scene_shortcuts_allowed(graph)
        assert controller._scene_shortcuts_allowed(regular)
        assert not controller._scene_shortcuts_allowed(external)
    finally:
        external.deleteLater()
        host.deleteLater()
        app.processEvents()
