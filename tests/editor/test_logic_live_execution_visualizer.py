"""Testes para o visualizador de execução ao vivo no LogicGraphEditor (Item 10.3)."""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from editor.widgets.logic_graph_editor import LogicGraphEditor
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.blackboard import BlackboardStore


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _build_test_graph() -> dict:
    return {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [
            {
                "id": "node_1",
                "type": "event_start",
                "position": [0.0, 0.0],
                "properties": {},
            },
            {
                "id": "node_2",
                "type": "log_message",
                "position": [200.0, 0.0],
                "properties": {"message": "Hello"},
            },
        ],
        "edges": [
            {
                "id": "edge_1_2",
                "from_node": "node_1",
                "from_port": "next",
                "to_node": "node_2",
                "to_port": "in",
                "kind": "flow",
            },
        ],
    }


def test_editor_applies_runtime_trace_and_clears_on_stop(qapp, tmp_path):
    graph = _build_test_graph()
    editor = LogicGraphEditor()
    editor.project_root = tmp_path
    editor.show()

    graph_file = tmp_path / "TestLogic.zlogic"
    editor.set_graph(graph, graph_file)

    # Verifica items
    node_1_item = editor.node_items.get("node_1")
    node_2_item = editor.node_items.get("node_2")
    assert node_1_item is not None
    assert node_2_item is not None

    trace = {
        "graph": str(graph_file),
        "object": "TestPlayer",
        "nodes": ["node_1", "node_2"],
        "edges": ["edge_1_2"],
        "values": {"node_2": {"message": "Hello"}},
    }

    editor.apply_runtime_trace(trace)

    assert node_1_item._runtime_display[0] is True
    assert node_2_item._runtime_display[0] is True
    assert editor.edge_items[0]._runtime_active is True

    # Clear on Stop
    editor.clear_runtime_trace()

    assert node_1_item._runtime_display[0] is False
    assert node_2_item._runtime_display[0] is False
    assert editor.edge_items[0]._runtime_active is False
