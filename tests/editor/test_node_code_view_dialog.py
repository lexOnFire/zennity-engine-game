"""Testes para o visualizador de código Read-Only (Code View </>) do Logic Editor."""
from __future__ import annotations

from editor.widgets.logic_graph.dialogs.node_code_view_dialog import (
    NodeCodeViewDialog,
    extract_node_source_info,
)


def test_extract_node_source_info_for_movement_node():
    info = extract_node_source_info("move_by")
    assert info["canonical_id"] == "move_by"
    assert info["definition"] is not None
    assert "class MoveByNode" in info["definition"]["code"]
    assert "movement_nodes.py" in info["definition"]["file"]
    
    assert info["executor"] is not None
    assert "def execute_move_by" in info["executor"]["code"]
    assert "movement_nodes.py" in info["executor"]["file"]
    
    assert info["evaluator"] is None


def test_extract_node_source_info_for_compare_number():
    info = extract_node_source_info("compare_number")
    assert info["definition"] is not None
    assert "class CompareNumberNode" in info["definition"]["code"]
    
    assert info["executor"] is not None
    assert "def execute_compare_number" in info["executor"]["code"]
    
    assert info["evaluator"] is not None
    assert "def evaluate_compare_number" in info["evaluator"]["code"]


def test_extract_node_source_info_for_pure_data_node():
    info = extract_node_source_info("divide_number")
    assert info["definition"] is not None
    assert "class DivideNumberNode" in info["definition"]["code"]
    assert info["evaluator"] is not None
    assert "evaluate_add_number_or_subtract_number_or_multiply_number_or_divide_number" in info["evaluator"]["code"]
    assert info["executor"] is None


def test_node_code_view_dialog_initialization():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    
    node_data = {
        "id": "node_test_1",
        "type": "move_by",
        "title": "Move By",
        "category": "Movement",
        "properties": {"x": 100.0, "y": 0.0},
    }
    dialog = NodeCodeViewDialog(node_data)
    
    assert "Move By (move_by)" in dialog.windowTitle()
    assert dialog.tabs.isTabEnabled(0) is True  # Definition
    assert dialog.tabs.isTabEnabled(1) is True  # Executor
    assert dialog.tabs.isTabEnabled(2) is False # Evaluator (move_by has no evaluator)
    assert "def execute_move_by" in dialog.executor_edit.toPlainText()
    assert dialog.definition_edit.isReadOnly() is True
    assert dialog.executor_edit.isReadOnly() is True
    assert dialog.evaluator_edit.isReadOnly() is True
