"""Regression coverage for the real isolated-editor bootstrap."""

from queue import Queue

from PySide6.QtWidgets import QApplication

from editor.isolated_editor_main import IsolatedEditorWindow


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
