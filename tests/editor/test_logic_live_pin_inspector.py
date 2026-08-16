"""Testes para tooltips e inspeção de valores no LogicPortItem (Item 10.4)."""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from editor.widgets.logic_graph_editor import LogicGraphEditor


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_pin_tooltips_update_with_runtime_values_and_clear(qapp, tmp_path):
    graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [
            {
                "id": "calc",
                "type": "add_number",
                "position": [0.0, 0.0],
                "properties": {"a": 10, "b": 20},
            },
        ],
        "edges": [],
    }

    editor = LogicGraphEditor()
    editor.project_root = tmp_path
    editor.show()

    graph_file = tmp_path / "MathTest.zlogic"
    editor.set_graph(graph, graph_file)

    node_item = editor.node_items.get("calc")
    assert node_item is not None

    port_a = node_item.input_ports.get("a")
    port_val = node_item.output_ports.get("value")
    assert port_a is not None
    assert port_val is not None

    # Antes do trace: tooltip padrão
    assert "[Runtime]:" not in port_a.toolTip()
    assert "[Runtime]:" not in port_val.toolTip()

    trace = {
        "graph": str(graph_file),
        "object": "Player",
        "nodes": ["calc"],
        "data_nodes": ["calc"],
        "values": {"calc": {"value": 30.0}},
        "input_values": {"calc": {"a": 10.0, "b": 20.0}},
    }

    editor.apply_runtime_trace(trace)

    # Tooltip reflete valores reais
    assert "[Runtime]: 10.0" in port_a.toolTip()
    assert "[Runtime]: 30.0" in port_val.toolTip()

    # Clear no Stop
    editor.clear_runtime_trace()

    assert "[Runtime]:" not in port_a.toolTip()
    assert "[Runtime]:" not in port_val.toolTip()
