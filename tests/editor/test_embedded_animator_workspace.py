from pathlib import Path

from PySide6.QtWidgets import QApplication, QWidget

from editor.widgets.animator_dialog import AnimatorControllerEditorDialog


def test_embedded_animator_uses_official_controller_format(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    parent = QWidget()
    editor = AnimatorControllerEditorDialog(tmp_path, parent=parent, embedded=True)
    try:
        assert editor.embedded
        assert not editor.isWindow()
        assert editor.editor_tabs.tabText(3) == "Ajuda"
        assert "Animator Graph" in editor.help_browser.toPlainText()
        editor.name_field.setText("Player")
        editor.save()
        path = tmp_path / "Assets" / "Animations" / "Player.zanimator"
        assert path.is_file()
        assert editor.current_path == path.resolve()
        assert editor.load_document(path)
        assert editor.data["format"] == "zennity.animator_controller"
    finally:
        editor.deleteLater()
        parent.deleteLater()
        app.processEvents()
