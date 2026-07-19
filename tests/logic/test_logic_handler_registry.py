import pytest

from engine.logic.handlers import LogicNodeHandlerRegistry, default_logic_handlers
from engine.logic.graph_asset import create_logic_node, default_logic_graph
from engine.logic.runtime import LogicGraphRuntime


def test_registry_rejects_accidental_replacement():
    registry = LogicNodeHandlerRegistry()
    registry.register("custom", lambda runtime, node, game, dt: ["next"])
    with pytest.raises(ValueError):
        registry.register("custom", lambda runtime, node, game, dt: [])


def test_default_handlers_are_discoverable():
    assert {"input_axis", "if_else", "move", "key_pressed"}.issubset(default_logic_handlers().node_types)


def test_custom_handler_executes_without_editing_runtime_dispatcher():
    graph = default_logic_graph("Custom")
    start = create_logic_node("event_start", (0, 100))
    graph["nodes"].append(start)
    custom = create_logic_node("custom_test", (300, 100))
    custom["type"] = "custom_test"
    graph["nodes"].append(custom)
    graph["edges"].append({"id": "edge", "from_node": start["id"], "from_port": "next", "to_node": custom["id"], "to_port": "in", "order": 0})
    registry = default_logic_handlers()
    calls = []
    registry.register("custom_test", lambda runtime, node, game, dt: calls.append(node["id"]) or [])
    runtime = LogicGraphRuntime(graph, handlers=registry)
    runtime.start(object())
    assert calls == [custom["id"]]
