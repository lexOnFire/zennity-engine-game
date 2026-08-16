"""Testes para captura de valores em tempo de execução e inspeção de dados (Item 10.4)."""
from __future__ import annotations

import pytest
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.blackboard import BlackboardStore


def _build_math_graph() -> dict:
    return {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [
            {
                "id": "start_node",
                "type": "event_start",
                "properties": {},
            },
            {
                "id": "set_health",
                "type": "set_variable",
                "properties": {"name": "health", "scope": "object", "value": 100},
            },
            {
                "id": "get_health",
                "type": "get_variable",
                "properties": {"name": "health", "scope": "object"},
            },
            {
                "id": "subtract_dmg",
                "type": "subtract_number",
                "properties": {"b": 25},
            },
            {
                "id": "compare_hp",
                "type": "compare_number",
                "properties": {"operator": ">", "value": 50},
            },
        ],
        "edges": [
            {
                "id": "e_start_compare",
                "from_node": "start_node",
                "from_port": "next",
                "to_node": "compare_hp",
                "to_port": "exec",
                "kind": "flow",
            },
            {
                "id": "e_get_sub",
                "from_node": "get_health",
                "from_port": "value",
                "to_node": "subtract_dmg",
                "to_port": "a",
                "kind": "data",
            },
            {
                "id": "e_sub_compare",
                "from_node": "subtract_dmg",
                "from_port": "value",
                "to_node": "compare_hp",
                "to_port": "value",
                "kind": "data",
            },
        ],
    }


class DummyGame:
    pass


def test_runtime_captures_input_and_output_data_values():
    graph = _build_math_graph()
    store = BlackboardStore()
    store.set("object", "health", 100, "Enemy_1")
    runtime = LogicGraphRuntime(graph, store, "Enemy_1")
    game = DummyGame()

    runtime.start(game)

    snapshot = runtime.debug_snapshot()
    
    # Outputs capturados
    outputs = snapshot["values"]
    assert outputs["get_health"]["value"] == 100
    assert outputs["subtract_dmg"]["value"] == 75.0
    assert outputs["compare_hp"]["value"] is True

    # Inputs capturados
    inputs = snapshot["input_values"]
    assert inputs["subtract_dmg"]["a"] == 100
    assert inputs["subtract_dmg"]["b"] == 25
    assert inputs["compare_hp"]["value"] == 75.0


def test_falsy_values_and_none_distinct_from_not_evaluated():
    graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [
            {"id": "start", "type": "event_start", "properties": {}},
            {"id": "set_zero", "type": "set_variable", "properties": {"name": "count", "scope": "object", "value": 0}},
            {"id": "set_false", "type": "set_variable", "properties": {"name": "flag", "scope": "object", "value": False}},
            {"id": "set_empty", "type": "set_variable", "properties": {"name": "text", "scope": "object", "value": ""}},
            {"id": "get_zero", "type": "get_variable", "properties": {"name": "count", "scope": "object"}},
            {"id": "unreached_node", "type": "add_number", "properties": {"a": 1, "b": 2}},
        ],
        "edges": [
            {"id": "e1", "from_node": "start", "from_port": "next", "to_node": "set_zero", "to_port": "exec", "kind": "flow"},
            {"id": "e2", "from_node": "set_zero", "from_port": "next", "to_node": "set_false", "to_port": "exec", "kind": "flow"},
            {"id": "e3", "from_node": "set_false", "from_port": "next", "to_node": "set_empty", "to_port": "exec", "kind": "flow"},
        ],
    }
    store = BlackboardStore()
    runtime = LogicGraphRuntime(graph, store, "Player")
    runtime.start(DummyGame())

    snapshot = runtime.debug_snapshot()
    variables = snapshot["blackboard"]["object"]
    
    assert variables["count"] == 0
    assert variables["flag"] is False
    assert variables["text"] == ""

    # Unreached node não tem valor
    assert "unreached_node" not in snapshot["values"]


def test_runtime_instance_isolation_between_two_objects():
    graph = _build_math_graph()
    store = BlackboardStore()
    
    runtime_enemy_1 = LogicGraphRuntime(graph, store, "Enemy_1")
    runtime_enemy_2 = LogicGraphRuntime(graph, store, "Enemy_2")
    
    store.set("object", "health", 100, "Enemy_1")
    store.set("object", "health", 40, "Enemy_2")

    game = DummyGame()
    runtime_enemy_1.start(game)
    runtime_enemy_2.start(game)

    snap1 = runtime_enemy_1.debug_snapshot()
    snap2 = runtime_enemy_2.debug_snapshot()

    assert snap1["blackboard"]["object"]["health"] == 100
    assert snap2["blackboard"]["object"]["health"] == 40
    assert snap1["values"]["compare_hp"]["value"] is True  # 100 - 25 = 75 > 50 -> True
    assert snap2["values"]["compare_hp"]["value"] is False # 40 - 25 = 15 > 50 -> False
