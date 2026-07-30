"""Regression coverage for the real isolated-editor bootstrap."""

from queue import Queue

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from editor.isolated_editor_main import IsolatedEditorWindow
from editor.runtime.tool_manager import EditorTool


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
