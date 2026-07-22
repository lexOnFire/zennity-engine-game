"""Deterministic parity contracts for the registry-based Logic Graph runtime."""

from __future__ import annotations

from copy import deepcopy

from engine.logic.graph_asset import create_logic_node, default_logic_graph
from engine.logic.runtime import LogicGraphRuntime


def _node(node_type: str, node_id: str, **properties):
    node = create_logic_node(node_type)
    node["id"] = node_id
    node["properties"].update(properties)
    return node


def _edge(source: str, port: str, target: str, order: int) -> dict:
    return {
        "id": f"edge-{order}-{source}-{port}-{target}",
        "from_node": source,
        "from_port": port,
        "to_node": target,
        "to_port": "in",
        "kind": "flow",
        "order": order,
    }


class DeterministicGame:
    active = True
    grounded = True
    rotation = 0.0

    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.log: list[tuple[float, float]] = []

    def move(self, dx: float, dy: float = 0.0) -> None:
        self.x += dx
        self.y += dy
        self.log.append((self.x, self.y))

    def key(self, _key: str) -> bool:
        return False

    def key_pressed(self, _key: str) -> bool:
        return False


def _sequence_graph() -> dict:
    graph = default_logic_graph("DeterministicSequence")
    graph["nodes"] = [
        _node("event_update", "event"),
        _node("sequence", "sequence", outputs=3),
        _node("move_by", "first", x=1.0, y=0.0),
        _node("move_by", "second", x=2.0, y=0.0),
        _node("move_by", "third", x=4.0, y=0.0),
    ]
    graph["edges"] = [
        _edge("event", "next", "sequence", 0),
        _edge("sequence", "then_0", "first", 1),
        _edge("sequence", "then_1", "second", 2),
        _edge("sequence", "then_2", "third", 3),
    ]
    return graph


def _run_signature(graph: dict, deltas: tuple[float, ...]):
    game = DeterministicGame()
    runtime = LogicGraphRuntime(deepcopy(graph))
    frames = []
    for delta in deltas:
        runtime.update(game, delta)
        frames.append((
            tuple(runtime.executed_nodes),
            tuple(runtime.executed_edges),
            tuple(game.log),
            game.x,
            game.y,
        ))
    return frames


def test_registry_runtime_repeats_identical_order_and_effects() -> None:
    graph = _sequence_graph()
    first = _run_signature(graph, (0.25, 0.5, 0.125))
    second = _run_signature(graph, (0.25, 0.5, 0.125))
    assert first == second
    assert first[0][0] == ("event", "sequence", "first", "second", "third")
    assert first[0][3] == 1.75


def test_once_state_is_deterministic_across_independent_runtimes() -> None:
    graph = default_logic_graph("OnceParity")
    graph["nodes"] = [
        _node("event_update", "event"),
        _node("once", "once"),
        _node("move_by", "move", x=10.0, y=0.0),
    ]
    graph["edges"] = [
        _edge("event", "next", "once", 0),
        _edge("once", "next", "move", 1),
    ]
    signatures = [_run_signature(graph, (0.1, 0.1, 0.1)) for _ in range(3)]
    assert signatures[0] == signatures[1] == signatures[2]
    assert signatures[0][-1][3] == 1.0


def test_input_graph_is_not_mutated_by_runtime_execution() -> None:
    graph = _sequence_graph()
    original = deepcopy(graph)
    _run_signature(graph, (0.25, 0.5))
    assert graph == original
