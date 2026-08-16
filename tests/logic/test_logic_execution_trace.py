"""Testes unitários para modelo de execution trace do LogicGraphRuntime (Item 10.3)."""
from __future__ import annotations

import pytest
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.blackboard import BlackboardStore


def _build_test_graph() -> dict:
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
                "id": "set_var_node",
                "type": "set_variable",
                "properties": {"name": "test_var", "scope": "object", "value": 10},
            },
            {
                "id": "get_var_node",
                "type": "get_variable",
                "properties": {"name": "test_var", "scope": "object"},
            },
            {
                "id": "compare_node",
                "type": "compare_number",
                "properties": {"operator": ">", "value": 5},
            },
            {
                "id": "true_action",
                "type": "log_message",
                "properties": {"message": "Success"},
            },
            {
                "id": "false_action",
                "type": "log_message",
                "properties": {"message": "Failed"},
            },
        ],
        "edges": [
            {
                "id": "edge_start_to_set",
                "from_node": "start_node",
                "from_port": "next",
                "to_node": "set_var_node",
                "to_port": "exec",
                "kind": "flow",
            },
            {
                "id": "edge_set_to_compare",
                "from_node": "set_var_node",
                "from_port": "next",
                "to_node": "compare_node",
                "to_port": "exec",
                "kind": "flow",
            },
            {
                "id": "edge_get_to_compare",
                "from_node": "get_var_node",
                "from_port": "value",
                "to_node": "compare_node",
                "to_port": "value",
                "kind": "data",
            },
            {
                "id": "edge_compare_true",
                "from_node": "compare_node",
                "from_port": "true",
                "to_node": "true_action",
                "to_port": "exec",
                "kind": "flow",
            },
            {
                "id": "edge_compare_false",
                "from_node": "compare_node",
                "from_port": "false",
                "to_node": "false_action",
                "to_port": "exec",
                "kind": "flow",
            },
        ],
    }


class DummyGame:
    def __init__(self):
        self.logs = []

    def log(self, msg):
        self.logs.append(msg)


def test_runtime_captures_node_and_flow_traces():
    graph = _build_test_graph()
    store = BlackboardStore()
    runtime = LogicGraphRuntime(graph, store, "TestObject")
    game = DummyGame()

    runtime.start(game)

    snapshot = runtime.debug_snapshot()
    assert "start_node" in snapshot["nodes"]
    assert "set_var_node" in snapshot["nodes"]
    assert "compare_node" in snapshot["nodes"]
    assert "true_action" in snapshot["nodes"]
    assert "false_action" not in snapshot["nodes"]

    # Flow edges traversed
    assert "edge_start_to_set" in snapshot["edges"]
    assert "edge_set_to_compare" in snapshot["edges"]
    assert "edge_compare_true" in snapshot["edges"]
    assert "edge_compare_false" not in snapshot["edges"]


def test_trace_sequence_and_incremental_query():
    graph = _build_test_graph()
    store = BlackboardStore()
    runtime = LogicGraphRuntime(graph, store, "TestObject")
    game = DummyGame()

    runtime.start(game)

    events = runtime.trace_events_since(0)
    assert len(events) >= 4
    
    # Sequences are monotonically increasing
    sequences = [e["sequence"] for e in events]
    assert sequences == sorted(sequences)

    # Incremental query since last sequence
    last_seq = sequences[-1]
    assert runtime.trace_events_since(last_seq) == []


def test_trace_buffer_is_bounded_and_prevents_memory_leak():
    graph = _build_test_graph()
    store = BlackboardStore()
    runtime = LogicGraphRuntime(graph, store, "TestObject")
    game = DummyGame()

    for _ in range(1000):
        runtime._record_trace("test_event", payload="stress")

    assert len(runtime._trace_events) == 512
    assert runtime._trace_sequence == 1000
