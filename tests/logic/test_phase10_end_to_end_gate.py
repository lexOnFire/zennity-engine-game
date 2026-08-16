"""Gate de integração final End-to-End da Phase 10 (Item 10.7).
Verifica a convivência pacífica dos sistemas construídos nos Itens 10.1 a 10.6.
"""
from __future__ import annotations

import pytest
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.blackboard import BlackboardStore


def test_phase10_runtime_trace_and_value_inspection_integration():
    """Valida a integração harmoniosa de trace de fluxo (10.3) e inspeção de dados (10.4)."""
    graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [
            {"id": "start", "type": "event_start", "properties": {}},
            {"id": "get_hp", "type": "get_variable", "properties": {"name": "hp", "scope": "object"}},
            {"id": "calc_dmg", "type": "subtract_number", "properties": {"b": 20}},
            {"id": "set_hp", "type": "set_variable", "properties": {"name": "hp", "scope": "object"}},
        ],
        "edges": [
            {"id": "e_flow_1", "from_node": "start", "from_port": "next", "to_node": "set_hp", "to_port": "exec", "kind": "flow"},
            {"id": "e_data_1", "from_node": "get_hp", "from_port": "value", "to_node": "calc_dmg", "to_port": "a", "kind": "data"},
            {"id": "e_data_2", "from_node": "calc_dmg", "from_port": "value", "to_node": "set_hp", "to_port": "value", "kind": "data"},
        ],
        "variables": {
            "hp": {"type": "number", "scope": "object", "default": 100},
        },
    }

    store = BlackboardStore()
    store.set("object", "hp", 100, "Player_1")

    runtime = LogicGraphRuntime(graph, store, "Player_1")
    
    class DummyGame:
        pass

    runtime.start(DummyGame())

    # Snapshot do runtime
    snapshot = runtime.debug_snapshot()

    # 1. 10.3 Traces presentes
    assert "start" in snapshot["nodes"]
    assert "set_hp" in snapshot["nodes"]
    assert "e_flow_1" in snapshot["edges"]
    assert snapshot["trace_sequence"] > 0
    assert len(snapshot["trace_events"]) > 0

    # 2. 10.4 Inspecção de Dados e Blackboard presentes
    assert snapshot["values"]["get_hp"]["value"] == 100
    assert snapshot["values"]["calc_dmg"]["value"] == 80.0
    assert snapshot["blackboard"]["object"]["hp"] == 80.0
    assert snapshot["input_values"]["calc_dmg"]["a"] == 100
    assert snapshot["input_values"]["calc_dmg"]["b"] == 20
