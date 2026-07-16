from __future__ import annotations

from pathlib import Path

from engine.logic.graph_asset import (
    create_logic_node,
    default_logic_graph,
    load_logic_graph,
    normalize_logic_graph,
    node_port_definitions,
    save_logic_graph,
    validate_logic_graph,
)
from engine.logic.runtime import LogicGraphRuntime


def test_logic_graph_round_trip_uses_zlogic_extension(tmp_path):
    graph = default_logic_graph("Player")
    graph["nodes"] = [create_logic_node("event_update"), create_logic_node("move", (240, 0))]
    graph["edges"] = [{
        "from_node": graph["nodes"][0]["id"],
        "to_node": graph["nodes"][1]["id"],
        "from_port": "next",
        "to_port": "in",
        "kind": "flow",
    }]
    saved = save_logic_graph(tmp_path / "player", graph)
    path = tmp_path / "player.zlogic"
    assert path.is_file()
    assert saved == load_logic_graph(path)
    assert saved["format"] == "zennity.logic_graph"


def test_normalization_removes_edges_with_missing_nodes():
    graph = default_logic_graph()
    graph["nodes"] = [{"id": "start", "type": "event_start"}]
    graph["edges"] = [{"from_node": "start", "to_node": "missing"}]
    normalized = normalize_logic_graph(graph)
    assert normalized["edges"] == []


def test_normalization_preserves_only_breakpoints_for_existing_nodes():
    graph = default_logic_graph()
    event = create_logic_node("event_update")
    graph["nodes"] = [event]
    graph["debug"] = {"breakpoints": [event["id"], "missing", event["id"]]}
    normalized = normalize_logic_graph(graph)
    assert normalized["debug"]["breakpoints"] == [event["id"]]


def test_validation_reports_missing_event_and_disconnected_node():
    graph = default_logic_graph()
    graph["nodes"] = [create_logic_node("move"), create_logic_node("jump")]
    issues = validate_logic_graph(graph)
    assert any("Ao iniciar" in issue["message"] for issue in issues)
    assert len([issue for issue in issues if "desconectado" in issue["message"]]) == 2


def test_player_movement_demo_contains_expected_visual_flow():
    root = Path(__file__).resolve().parents[2]
    graph = load_logic_graph(root / "Assets/Logic/PlayerMovement.zlogic")
    node_types = {node["type"] for node in graph["nodes"]}
    assert {"event_update", "input_axis", "if_else", "move", "key_pressed", "is_grounded", "jump"} <= node_types
    assert len(graph["edges"]) == 7
    assert not validate_logic_graph(graph)


def test_player_movement_demo_executes_move_and_jump_nodes():
    root = Path(__file__).resolve().parents[2]
    runtime = LogicGraphRuntime(load_logic_graph(root / "Assets/Logic/PlayerMovement.zlogic"))

    class Animator:
        def __init__(self):
            self.states = []

        def play(self, state):
            self.states.append(state)

    class Game:
        grounded = True

        def __init__(self):
            self.x = 0.0
            self.jumps = []
            self.animator = Animator()
            self._pressed = True

        def axis(self, negative, positive):
            assert (negative, positive) == ("a", "d")
            return 1

        def key_pressed(self, key):
            return self._pressed and key == "space"

        def move(self, amount, _dy=0.0):
            self.x += amount

        def jump(self, force):
            self.jumps.append(force)

    game = Game()
    runtime.update(game, 0.5)
    assert game.x == 110.0
    assert game.jumps == [440.0]


def test_condition_nodes_expose_named_typed_ports():
    ports = node_port_definitions("if_else")
    assert ("condition", "bool") in ports["inputs"]
    assert ports["outputs"] == [("true", "flow"), ("false", "flow")]
    assert ("value", "number") in node_port_definitions("input_axis")["outputs"]


def test_validation_rejects_incompatible_or_unknown_ports():
    graph = default_logic_graph("InvalidPorts")
    event = create_logic_node("event_update")
    move = create_logic_node("move")
    graph["nodes"] = [event, move]
    graph["edges"] = [{
        "from_node": event["id"], "from_port": "missing",
        "to_node": move["id"], "to_port": "value", "kind": "flow",
    }]
    messages = [issue["message"] for issue in validate_logic_graph(graph)]
    assert any("Saída inexistente" in message for message in messages)


def _edge(source, source_port, target, target_port, kind="flow"):
    return {
        "from_node": source["id"], "from_port": source_port,
        "to_node": target["id"], "to_port": target_port, "kind": kind,
    }


def test_runtime_resolves_number_wire_lazily_for_move():
    event = create_logic_node("event_update")
    axis = create_logic_node("input_axis")
    move = create_logic_node("move")
    move["properties"]["speed"] = 50.0
    graph = default_logic_graph("TypedMove")
    graph["nodes"] = [event, axis, move]
    graph["edges"] = [
        _edge(event, "next", move, "in"),
        _edge(axis, "value", move, "value", "number"),
    ]

    class Game:
        def __init__(self): self.x = 0.0
        def axis(self, negative, positive): return -1
        def move(self, amount): self.x += amount

    game = Game()
    LogicGraphRuntime(graph).update(game, 0.5)
    assert game.x == -25.0


def test_runtime_resolves_boolean_nodes_and_branch():
    event = create_logic_node("event_update")
    left = create_logic_node("bool_value")
    right = create_logic_node("bool_value")
    logic_and = create_logic_node("and")
    branch = create_logic_node("if_else")
    jump = create_logic_node("jump")
    graph = default_logic_graph("TypedCondition")
    graph["nodes"] = [event, left, right, logic_and, branch, jump]
    graph["edges"] = [
        _edge(event, "next", branch, "in"),
        _edge(left, "value", logic_and, "a", "bool"),
        _edge(right, "value", logic_and, "b", "bool"),
        _edge(logic_and, "value", branch, "condition", "bool"),
        _edge(branch, "true", jump, "in"),
    ]

    class Game:
        def __init__(self): self.jumps = []
        def jump(self, force): self.jumps.append(force)

    game = Game()
    LogicGraphRuntime(graph).update(game, 0.016)
    assert game.jumps == [420.0]


def test_runtime_connected_value_overrides_property_and_variable_persists():
    event = create_logic_node("event_update")
    number = create_logic_node("number_value")
    number["properties"]["value"] = 3.5
    setter = create_logic_node("set_variable")
    setter["properties"]["name"] = "speed"
    getter = create_logic_node("get_variable")
    getter["properties"]["name"] = "speed"
    move = create_logic_node("move")
    move["properties"]["speed"] = 10.0
    graph = default_logic_graph("Variables")
    graph["nodes"] = [event, number, setter, getter, move]
    graph["edges"] = [
        _edge(event, "next", setter, "in"),
        _edge(number, "value", setter, "value", "number"),
        _edge(setter, "next", move, "in"),
        _edge(getter, "value", move, "value", "any"),
    ]

    class Game:
        def __init__(self): self.x = 0.0
        def move(self, amount): self.x += amount

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.update(game, 1.0)
    assert game.x == 35.0
    assert runtime.variables["speed"] == 3.5


def test_runtime_reports_data_cycles_with_node_name():
    event = create_logic_node("event_update")
    first = create_logic_node("and")
    first["title"] = "Condição circular"
    second = create_logic_node("or")
    branch = create_logic_node("if_else")
    graph = default_logic_graph("Cycle")
    graph["nodes"] = [event, first, second, branch]
    graph["edges"] = [
        _edge(event, "next", branch, "in"),
        _edge(first, "value", second, "a", "bool"),
        _edge(second, "value", first, "a", "bool"),
        _edge(first, "value", branch, "condition", "bool"),
    ]

    try:
        LogicGraphRuntime(graph).update(object(), 0.016)
    except RuntimeError as exc:
        assert "Ciclo de dados" in str(exc)
        assert "Condição circular" in str(exc)
    else:
        raise AssertionError("O ciclo de dados deveria interromper a execução")


def test_runtime_compare_and_text_wires_drive_hud_action():
    event = create_logic_node("event_update")
    number = create_logic_node("number_value")
    number["properties"]["value"] = 8
    compare = create_logic_node("compare_number")
    compare["properties"].update({"operator": ">=", "value": 5})
    text = create_logic_node("text_value")
    text["properties"]["value"] = "Objetivo concluído"
    hud = create_logic_node("set_hud")
    graph = default_logic_graph("TypedHUD")
    graph["nodes"] = [event, number, compare, text, hud]
    graph["edges"] = [
        _edge(event, "next", compare, "in"),
        _edge(number, "value", compare, "value", "number"),
        _edge(compare, "true", hud, "in"),
        _edge(text, "value", hud, "text", "text"),
    ]

    class Game:
        def __init__(self): self.hud = {}
        def set_hud(self, key, value): self.hud[key] = value

    game = Game()
    LogicGraphRuntime(graph).update(game, 0.016)
    assert list(game.hud.values()) == ["Objetivo concluído"]


def test_runtime_debug_snapshot_is_small_and_serializable():
    event = create_logic_node("event_update")
    number = create_logic_node("number_value")
    move = create_logic_node("move")
    graph = default_logic_graph("DebugTrace")
    graph["nodes"] = [event, number, move]
    graph["edges"] = [
        _edge(event, "next", move, "in"),
        _edge(number, "value", move, "value", "number"),
    ]

    class Game:
        def move(self, amount): self.amount = amount

    runtime = LogicGraphRuntime(graph)
    runtime.update(Game(), 0.5)
    snapshot = runtime.debug_snapshot()
    assert snapshot["nodes"] == [event["id"], move["id"], number["id"]]
    assert {edge["id"] for edge in runtime.graph["edges"]} == set(snapshot["edges"])
    assert snapshot["values"][number["id"]]["value"] == 0.0
    assert all(isinstance(key, str) for key in snapshot["values"])


def test_runtime_breakpoint_and_step_keep_exact_flow_continuation():
    event = create_logic_node("event_update")
    setter = create_logic_node("set_variable")
    setter["properties"].update({"name": "frames", "value": 1})
    amount = create_logic_node("number_value")
    amount["properties"]["value"] = 1.0
    move = create_logic_node("move")
    jump = create_logic_node("jump")
    graph = default_logic_graph("BreakpointFlow")
    graph["nodes"] = [event, setter, amount, move, jump]
    graph["edges"] = [
        _edge(event, "next", setter, "in"),
        _edge(setter, "next", move, "in"),
        _edge(amount, "value", move, "value", "number"),
        _edge(move, "next", jump, "in"),
    ]
    graph["debug"]["breakpoints"] = [move["id"]]

    class Game:
        def __init__(self):
            self.x = 0.0
            self.jumps = []

        def move(self, amount):
            self.x += amount

        def jump(self, force):
            self.jumps.append(force)

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.update(game, 0.5)
    assert runtime.debug_paused is True
    assert runtime.pause_node == move["id"]
    assert runtime.variables["frames"] == 1
    assert game.x == 0.0

    runtime.step()
    assert runtime.debug_paused is True
    assert runtime.pause_node == jump["id"]
    assert game.x == 100.0
    assert game.jumps == []

    runtime.step()
    assert runtime.debug_paused is True
    assert runtime.pause_node == ""
    assert game.x == 100.0
    assert game.jumps == [420.0]

    runtime.continue_execution()
    runtime.update(game, 0.5)
    assert runtime.pause_node == move["id"]
    assert game.x == 100.0
