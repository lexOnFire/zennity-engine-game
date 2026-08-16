"""Testes para o editor de código e validação no CustomScriptEditorDialog (Item 10.6)."""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication
from unittest.mock import patch

from editor.widgets.logic_graph.dialogs.custom_script_editor_dialog import CustomScriptEditorDialog
from editor.widgets.logic_graph.code_editor import CodeEditorWidget, PythonSyntaxHighlighter


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_code_editor_widget_line_numbers_and_highlight(qapp):
    editor = CodeEditorWidget()
    editor.setPlainText("a = ctx.get_input('a')\nctx.set_output('res', a * 2)\n# comentario")

    # Verifica contagem de linhas e área
    assert editor.blockCount() == 3
    assert editor.line_number_area_width() > 0
    assert editor.highlighter is not None


def test_custom_script_editor_validation_feedback_and_errors(qapp):
    node = {
        "id": "node_custom",
        "type": "custom_script",
        "properties": {
            "execution_model": "pure_data",
            "inputs": [{"name": "a", "type": "number", "default": 10.0}],
            "outputs": [{"name": "result", "type": "number"}],
            "script": "a = ctx.get_input('a')\nctx.set_output('result', a + 5)",
        },
    }

    dialog = CustomScriptEditorDialog(node)
    
    # 1. Script Válido
    with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
        assert dialog._validate_only() is True
        assert "✓" in dialog.status_label.text()
        mock_warn.assert_not_called()

    # 2. Syntax Error
    dialog.script_edit.setPlainText("a = \nctx.set_output('result', a)")
    with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
        assert dialog._validate_only() is False
        assert "✕" in dialog.status_label.text()
        mock_warn.assert_called_once()

    # 3. Security Error
    dialog.script_edit.setPlainText("import os\nctx.set_output('result', 1)")
    with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
        assert dialog._validate_only() is False
        assert "✕" in dialog.status_label.text()

    # 4. Unknown Port Reference
    dialog.script_edit.setPlainText("ctx.set_output('unknown_port', 42)")
    with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
        assert dialog._validate_only() is False
        assert "✕" in dialog.status_label.text()


def test_500_lines_code_editor_responsiveness(qapp):
    editor = CodeEditorWidget()
    lines = [f"val_{i} = ctx.get_input('in_{i % 5}') # line {i}" for i in range(500)]
    content = "\n".join(lines)
    
    editor.setPlainText(content)
    assert editor.blockCount() == 500
    assert editor.line_number_area_width() > 0
