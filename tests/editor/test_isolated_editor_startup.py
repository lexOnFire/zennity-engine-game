"""Regression coverage for the real isolated-editor bootstrap."""

import inspect
from queue import Queue

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGraphicsView

from editor.isolated_editor_main import IsolatedEditorWindow, main
from editor.runtime.tool_manager import EditorTool


def test_isolated_editor_keeps_pygame_runtime_out_of_qt_process() -> None:
    source = inspect.getsource(main)

    assert "EngineBootstrap.boot" not in source


def test_isolated_editor_bootstrap_connects_camera_inspector_fields() -> None:
    app = QApplication.instance() or QApplication([])
    window = IsolatedEditorWindow(None, Queue(), Queue())

    try:
        assert window.camera_active_field is not None
        assert window.camera_viewport_w is not None
        assert window.camera_viewport_h is not None
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()


def test_isolated_editor_transform_shortcuts_activate_phase1_tools() -> None:
    app = QApplication.instance() or QApplication([])
    window = IsolatedEditorWindow(None, Queue(), Queue())

    try:
        window.show()
        window.activateWindow()
        window.setFocus()
        app.processEvents()

        for key, expected_tool in (
            (Qt.Key_W, EditorTool.MOVE),
            (Qt.Key_E, EditorTool.ROTATE),
            (Qt.Key_R, EditorTool.SCALE),
            (Qt.Key_Q, EditorTool.SELECT),
        ):
            QTest.keyClick(window, key)
            app.processEvents()
            assert window.editor_context.tools.active_tool == expected_tool
            assert window._tool_actions[expected_tool.value].isChecked()
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()


def test_isolated_editor_disables_scene_delete_while_graph_has_focus() -> None:
    app = QApplication.instance() or QApplication([])
    window = IsolatedEditorWindow(None, Queue(), Queue())
    graph_window = QGraphicsView()
    graph_window.setObjectName("LogicGraphView")

    try:
        window.show()
        graph_window.show()
        graph_window.activateWindow()
        graph_window.setFocus()
        app.processEvents()
        window._tool_controller._sync_edit_shortcut_scope(window, graph_window)

        delete_shortcut = window._tool_controller.shortcut_service.shortcut_for(
            "edit.delete"
        )
        assert delete_shortcut is not None
        assert not delete_shortcut.isEnabled()

        window.activateWindow()
        window.setFocus()
        app.processEvents()
        window._tool_controller._sync_edit_shortcut_scope(graph_window, window)
        assert delete_shortcut.isEnabled()
    finally:
        graph_window.close()
        graph_window.deleteLater()
        window.close()
        window.deleteLater()
        app.processEvents()
