import pytest
from engine.logic.graph_asset import normalize_logic_graph
from engine.logic.node_definitions.catalogue import resolve_node_id, definitions_view
from engine.logic.runtime import LogicGraphRuntime
from engine.logic.blackboard import BlackboardStore
from engine.logic.event_bus import LogicEventBus


class MockGame:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def move_y(self, dy: float) -> None:
        self.y += dy


class MockGameFallbackMove:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def move(self, dx: float, dy: float = 0.0) -> None:
        self.x += dx
        self.y += dy


def test_catalogue_contains_move_y():
    defs = definitions_view()
    definition = defs.get("move_y")
    assert definition is not None
    assert definition["id"] == "move_y"
    assert definition["category"] == "Movement"
    assert definition["inputs"] == [("in", "flow"), ("value", "number")]
    assert definition["outputs"] == [("next", "flow")]


def test_alias_move_dot_y_resolves_to_move_y():
    assert resolve_node_id("move.y") == "move_y"


def test_execute_move_y_updates_y_position():
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph",
        "nodes": [
            {
                "id": "node_update",
                "type": "event_update",
            },
            {
                "id": "node_axis",
                "type": "input_axis",
                "properties": {
                    "negative": "S",
                    "positive": "W",
                }
            },
            {
                "id": "node_move_y",
                "type": "move_y",
                "properties": {
                    "speed": 100.0
                }
            }
        ],
        "edges": [
            {
                "id": "e_flow",
                "from_node": "node_update",
                "from_port": "next",
                "to_node": "node_axis",
                "to_port": "in",
                "kind": "flow"
            },
            {
                "id": "e_axis_move",
                "from_node": "node_axis",
                "from_port": "next",
                "to_node": "node_move_y",
                "to_port": "in",
                "kind": "flow"
            },
            {
                "id": "e_axis_val",
                "from_node": "node_axis",
                "from_port": "value",
                "to_node": "node_move_y",
                "to_port": "value",
                "kind": "data"
            }
        ]
    })

    class GameWithAxis(MockGame):
        def axis(self, neg, pos):
            return 1.0

    game = GameWithAxis(x=10.0, y=20.0)
    store = BlackboardStore()
    bus = LogicEventBus()
    runtime = LogicGraphRuntime(graph, store, "Player", bus)
    runtime.start(game)

    runtime.update(game, 0.5)  # 1.0 * 100.0 * 0.5 = 50.0
    assert game.y == 70.0
    assert game.x == 10.0


def test_execute_move_dot_y_alias_runtime():
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph",
        "nodes": [
            {
                "id": "node_update",
                "type": "event_update",
            },
            {
                "id": "node_axis",
                "type": "input_axis",
                "properties": {
                    "negative": "S",
                    "positive": "W",
                }
            },
            {
                "id": "node_move_y",
                "type": "move.y",  # using dotted alias
                "properties": {
                    "speed": 200.0
                }
            }
        ],
        "edges": [
            {
                "id": "e_flow",
                "from_node": "node_update",
                "from_port": "next",
                "to_node": "node_axis",
                "to_port": "in",
                "kind": "flow"
            },
            {
                "id": "e_axis_move",
                "from_node": "node_axis",
                "from_port": "next",
                "to_node": "node_move_y",
                "to_port": "in",
                "kind": "flow"
            },
            {
                "id": "e_axis_val",
                "from_node": "node_axis",
                "from_port": "value",
                "to_node": "node_move_y",
                "to_port": "value",
                "kind": "data"
            }
        ]
    })

    class GameWithAxisFallback(MockGameFallbackMove):
        def axis(self, neg, pos):
            return -0.5

    game = GameWithAxisFallback(x=0.0, y=0.0)
    store = BlackboardStore()
    bus = LogicEventBus()
    runtime = LogicGraphRuntime(graph, store, "Player", bus)
    runtime.start(game)

    runtime.update(game, 0.1)  # -0.5 * 200.0 * 0.1 = -10.0
    assert game.y == -10.0
    assert game.x == 0.0
