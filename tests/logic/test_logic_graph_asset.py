from __future__ import annotations

from pathlib import Path

from engine.logic.graph_asset import (
    create_logic_node,
    default_logic_graph,
    load_logic_graph,
    normalize_logic_graph,
    node_port_definitions,
    save_logic_graph,
    subgraph_interface,
    validate_logic_graph,
)
from engine.logic.runtime import LogicGraphRuntime
from engine.logic.blackboard import BlackboardStore, load_blackboard_asset, save_blackboard_asset
from engine.logic.event_bus import LogicEventBus
from engine.logic.recipes import LOGIC_RECIPES, build_logic_recipe, find_logic_recipes


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


def test_logic_graph_enabled_state_can_preserve_detached_assets(tmp_path):
    graph = default_logic_graph("Detached")
    graph["enabled"] = False
    saved = save_logic_graph(tmp_path / "detached", graph)
    assert saved["enabled"] is False
    assert load_logic_graph(tmp_path / "detached.zlogic")["enabled"] is False


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
    graph["debug"] = {
        "breakpoints": [event["id"], "missing", event["id"]],
        "breakpoint_conditions": {event["id"]: "x > 10", "missing": "true"},
        "watches": ["x", "vida", "x"],
    }
    normalized = normalize_logic_graph(graph)
    assert normalized["debug"]["breakpoints"] == [event["id"]]
    assert normalized["debug"]["breakpoint_conditions"] == {event["id"]: "x > 10"}
    assert normalized["debug"]["watches"] == ["x", "vida"]


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


def test_conditional_breakpoint_watches_and_restart_are_beginner_safe():
    event = create_logic_node("event_update")
    amount = create_logic_node("number_value")
    amount["properties"]["value"] = 1.0
    move = create_logic_node("move")
    graph = default_logic_graph("ConditionalDebug")
    graph["nodes"] = [event, amount, move]
    graph["edges"] = [
        _edge(event, "next", move, "in"),
        _edge(amount, "value", move, "value", "number"),
    ]
    graph["debug"] = {
        "breakpoints": [move["id"]],
        "breakpoint_conditions": {move["id"]: "x >= 100 e grounded == verdadeiro"},
        "watches": ["x", "grounded", "x >= 100"],
    }

    class Game:
        grounded = True

        def __init__(self):
            self.x = 0.0

        def move(self, amount):
            self.x += amount

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.update(game, 0.5)
    assert runtime.debug_paused is False
    assert game.x == 100.0

    runtime.update(game, 0.5)
    snapshot = runtime.debug_snapshot()
    assert runtime.debug_paused is True
    assert runtime.pause_node == move["id"]
    assert snapshot["watches"] == {"x": 100.0, "grounded": True, "x >= 100": True}

    game.x = 350.0
    runtime.restart(game)
    assert runtime.debug_paused is True
    assert runtime.pause_node == move["id"]
    assert runtime.debug_snapshot()["watches"]["x"] == 350.0


def test_invalid_breakpoint_condition_pauses_with_clear_error():
    event = create_logic_node("event_update")
    move = create_logic_node("move")
    graph = default_logic_graph("InvalidCondition")
    graph["nodes"] = [event, move]
    graph["edges"] = [_edge(event, "next", move, "in")]
    graph["debug"]["breakpoints"] = [move["id"]]
    graph["debug"]["breakpoint_conditions"] = {move["id"]: "variavel_que_nao_existe > 2"}

    class Game:
        def move(self, amount): pass

    runtime = LogicGraphRuntime(graph)
    runtime.update(Game(), 0.1)
    assert runtime.debug_paused is True
    assert "variável 'variavel_que_nao_existe' não encontrada" in runtime.debug_snapshot()["condition_error"]


def test_blackboard_asset_round_trip_preserves_typed_scopes(tmp_path):
    saved = save_blackboard_asset(tmp_path / "ProjectBlackboard", {"variables": {
        "score": {"type": "number", "scope": "project", "default": 10},
        "tutorial": {"type": "bool", "scope": "project", "default": "verdadeiro"},
    }})
    loaded = load_blackboard_asset(tmp_path / "ProjectBlackboard.zblackboard")
    assert loaded == saved
    assert loaded["variables"]["score"]["default"] == 10.0
    assert loaded["variables"]["tutorial"]["default"] is True


def test_blackboard_shares_scene_and_project_but_isolates_objects():
    store = BlackboardStore(
        {"variables": {"score": {"type": "number", "scope": "scene", "default": 0}}},
        {"variables": {"record": {"type": "number", "scope": "project", "default": 50}}},
    )
    graph = default_logic_graph("Blackboard")
    graph["variables"] = {
        "life": {"type": "number", "scope": "object", "default": 3},
        "score": {"type": "number", "scope": "scene", "default": 0},
        "record": {"type": "number", "scope": "project", "default": 50},
    }
    player = LogicGraphRuntime(graph, store, "Player")
    enemy = LogicGraphRuntime(graph, store, "Enemy")

    store.set("object", "life", 1, "Player")
    store.set("scene", "score", 25, "Player")
    store.set("project", "record", 100, "Enemy")

    assert player.blackboard.get("object", "life", "Player") == 1.0
    assert enemy.blackboard.get("object", "life", "Enemy") == 3.0
    assert enemy.blackboard.get("scene", "score", "Enemy") == 25.0
    assert player.blackboard.get("project", "record", "Player") == 100.0
    assert player.debug_snapshot()["blackboard"]["scene"]["score"] == 25.0


def test_get_and_set_variable_nodes_respect_selected_scope():
    event = create_logic_node("event_update")
    setter = create_logic_node("set_variable")
    setter["properties"].update({"scope": "scene", "name": "score", "value": 7})
    getter = create_logic_node("get_variable")
    getter["properties"].update({"scope": "scene", "name": "score"})
    move = create_logic_node("move")
    graph = default_logic_graph("ScopedNodes")
    graph["variables"] = {"score": {"type": "number", "scope": "scene", "default": 0}}
    graph["nodes"] = [event, setter, getter, move]
    graph["edges"] = [
        _edge(event, "next", setter, "in"),
        _edge(setter, "next", move, "in"),
        _edge(getter, "value", move, "value", "any"),
    ]

    class Game:
        def __init__(self): self.x = 0.0
        def move(self, value): self.x += value

    game = Game()
    runtime = LogicGraphRuntime(graph, BlackboardStore(), "Player")
    runtime.update(game, 1.0)
    assert game.x == 1400.0
    assert runtime.debug_snapshot()["blackboard"]["scene"]["score"] == 7.0


def test_visual_events_communicate_between_graphs_with_payload():
    bus = LogicEventBus()
    store = BlackboardStore({"variables": {
        "score": {"type": "number", "scope": "scene", "default": 0},
    }})
    update = create_logic_node("event_update")
    payload = create_logic_node("number_value")
    payload["properties"]["value"] = 3
    emit = create_logic_node("emit_event")
    emit["properties"]["name"] = "moeda_coletada"
    sender_graph = default_logic_graph("Coin")
    sender_graph["nodes"] = [update, payload, emit]
    sender_graph["edges"] = [
        _edge(update, "next", emit, "in"),
        _edge(payload, "value", emit, "payload", "any"),
    ]

    receive = create_logic_node("event_custom")
    receive["properties"]["name"] = "Moeda_Coletada"
    setter = create_logic_node("set_variable")
    setter["properties"].update({"scope": "scene", "name": "score"})
    receiver_graph = default_logic_graph("HUD")
    receiver_graph["variables"] = {"score": {"type": "number", "scope": "scene", "default": 0}}
    receiver_graph["nodes"] = [receive, setter]
    receiver_graph["edges"] = [
        _edge(receive, "next", setter, "in"),
        _edge(receive, "payload", setter, "value", "any"),
    ]

    class Game: pass

    receiver = LogicGraphRuntime(receiver_graph, store, "HUD", bus)
    sender = LogicGraphRuntime(sender_graph, store, "Coin", bus)
    receiver.start(Game())
    sender.update(Game(), 0.016)
    assert store.get("scene", "score", "HUD") == 0.0
    assert bus.dispatch() == 1
    assert store.get("scene", "score", "HUD") == 3.0
    assert receiver.debug_snapshot()["events"][-1]["name"] == "moeda_coletada"
    assert receiver.debug_snapshot()["values"][receive["id"]]["payload"] == 3.0


def test_visual_event_breakpoint_pauses_before_receiver_node():
    bus = LogicEventBus()
    receive = create_logic_node("event_custom")
    receive["properties"]["name"] = "dano"
    graph = default_logic_graph("Damage")
    graph["nodes"] = [receive]
    graph["debug"]["breakpoints"] = [receive["id"]]

    runtime = LogicGraphRuntime(graph, BlackboardStore(), "Player", bus)
    runtime.start(object())
    bus.emit("dano", 5, "Enemy")
    bus.dispatch()
    assert runtime.debug_paused is True
    assert runtime.pause_node == receive["id"]
    assert runtime.debug_snapshot()["events"][-1]["payload"] == 5


def test_visual_event_bus_stops_recursive_event_storm():
    bus = LogicEventBus()
    receive = create_logic_node("event_custom")
    receive["properties"]["name"] = "loop"
    emit = create_logic_node("emit_event")
    emit["properties"]["name"] = "loop"
    graph = default_logic_graph("LoopGuard")
    graph["nodes"] = [receive, emit]
    graph["edges"] = [_edge(receive, "next", emit, "in")]
    runtime = LogicGraphRuntime(graph, BlackboardStore(), "Looper", bus)
    runtime.start(object())
    bus.emit("loop")
    try:
        bus.dispatch()
    except RuntimeError as exc:
        assert "Limite de eventos excedido" in str(exc)
    else:
        raise AssertionError("Uma cascata recursiva deveria ser interrompida")


def test_subgraph_interface_creates_typed_dynamic_ports():
    start = create_logic_node("subgraph_start")
    entry = create_logic_node("subgraph_input")
    entry["properties"].update({"name": "velocidade", "type": "number", "default": 2})
    result = create_logic_node("subgraph_return")
    result["properties"].update({"name": "movimento", "type": "number"})
    graph = default_logic_graph("CalcularMovimento")
    graph["nodes"] = [start, entry, result]
    graph["edges"] = [
        _edge(start, "next", result, "in"),
        _edge(entry, "value", result, "value", "number"),
    ]
    interface = subgraph_interface(graph)
    assert interface["inputs"] == [{"name": "velocidade", "type": "number", "default": 2}]
    assert interface["outputs"] == [{"name": "movimento", "type": "number"}]

    call = create_logic_node("call_subgraph")
    call["properties"].update(interface)
    assert ("velocidade", "number") in node_port_definitions(call)["inputs"]
    assert ("movimento", "number") in node_port_definitions(call)["outputs"]
    assert not validate_logic_graph(graph)


def test_runtime_executes_reusable_subgraph_with_input_and_output():
    start = create_logic_node("subgraph_start")
    entry = create_logic_node("subgraph_input")
    entry["properties"].update({"name": "valor", "type": "number", "default": 3})
    result = create_logic_node("subgraph_return")
    result["properties"].update({"name": "resultado", "type": "number"})
    reusable = default_logic_graph("Reutilizavel")
    reusable["nodes"] = [start, entry, result]
    reusable["edges"] = [
        _edge(start, "next", result, "in"),
        _edge(entry, "value", result, "value", "number"),
    ]

    update = create_logic_node("event_update")
    call = create_logic_node("call_subgraph")
    call["properties"].update({"path": "Assets/Logic/Reutilizavel.zlogic", **subgraph_interface(reusable)})
    move = create_logic_node("move")
    move["properties"]["speed"] = 10
    parent = default_logic_graph("Player")
    parent["nodes"] = [update, call, move]
    parent["edges"] = [
        _edge(update, "next", call, "in"),
        _edge(call, "next", move, "in"),
        _edge(call, "resultado", move, "value", "number"),
    ]

    class Game:
        def __init__(self): self.x = 0.0
        def move(self, amount): self.x += amount

    game = Game()
    runtime = LogicGraphRuntime(parent, subgraph_loader=lambda _path: reusable)
    runtime.update(game, 0.5)
    assert game.x == 15.0
    assert runtime.debug_snapshot()["values"][call["id"]]["resultado"] == 3.0


def test_runtime_rejects_recursive_subgraph_references():
    start = create_logic_node("subgraph_start")
    recursive_call = create_logic_node("call_subgraph")
    recursive_call["properties"]["path"] = "Assets/Logic/A.zlogic"
    reusable = default_logic_graph("A")
    reusable["nodes"] = [start, recursive_call]
    reusable["edges"] = [_edge(start, "next", recursive_call, "in")]

    update = create_logic_node("event_update")
    parent_call = create_logic_node("call_subgraph")
    parent_call["properties"]["path"] = "Assets/Logic/A.zlogic"
    parent = default_logic_graph("Parent")
    parent["nodes"] = [update, parent_call]
    parent["edges"] = [_edge(update, "next", parent_call, "in")]
    runtime = LogicGraphRuntime(parent, subgraph_loader=lambda _path: reusable)
    try:
        runtime.update(object(), 0.016)
    except RuntimeError as exc:
        assert "Referência circular entre subgrafos" in str(exc)
    else:
        raise AssertionError("Uma referência circular deveria ser rejeitada")


def test_collision_and_trigger_events_receive_other_object():
    collision = create_logic_node("event_collision_enter")
    destroy = create_logic_node("destroy_object")
    graph = default_logic_graph("Collision")
    graph["nodes"] = [collision, destroy]
    graph["edges"] = [
        _edge(collision, "next", destroy, "in"),
        _edge(collision, "other", destroy, "target", "object"),
    ]

    class Game: pass

    class Other:
        active = True
        def destroy(self): self.active = False

    game = Game()
    other = Other()
    runtime = LogicGraphRuntime(graph)
    runtime.trigger_event("event_collision_enter", game, payload=other)
    assert other.active is False
    assert runtime.values[(collision["id"], "other")] is other


def test_repeating_timer_updates_blackboard_after_interval():
    timer = create_logic_node("event_timer")
    timer["properties"].update({"seconds": 1.0, "repeat": True})
    current = create_logic_node("get_variable")
    current["properties"].update({"scope": "object", "name": "ticks"})
    one = create_logic_node("number_value")
    one["properties"]["value"] = 1
    add = create_logic_node("add_number")
    setter = create_logic_node("set_variable")
    setter["properties"].update({"scope": "object", "name": "ticks"})
    graph = default_logic_graph("Timer")
    graph["variables"] = {"ticks": {"type": "number", "scope": "object", "default": 0}}
    graph["nodes"] = [timer, current, one, add, setter]
    graph["edges"] = [
        _edge(timer, "next", setter, "in"),
        _edge(current, "value", add, "a", "number"),
        _edge(one, "value", add, "b", "number"),
        _edge(add, "value", setter, "value", "number"),
    ]

    runtime = LogicGraphRuntime(graph)
    for _ in range(3):
        runtime.update(object(), 0.4)
    assert runtime.blackboard.get("object", "ticks", "Object") == 1.0
    runtime.update(object(), 1.0)
    assert runtime.blackboard.get("object", "ticks", "Object") == 2.0


def test_math_and_text_library_drives_hud_without_python():
    update = create_logic_node("event_update")
    add = create_logic_node("add_number")
    add["properties"].update({"a": 2, "b": 3})
    convert = create_logic_node("to_text")
    join = create_logic_node("join_text")
    join["properties"]["b"] = " pontos"
    hud = create_logic_node("set_hud")
    graph = default_logic_graph("MathText")
    graph["nodes"] = [update, add, convert, join, hud]
    graph["edges"] = [
        _edge(update, "next", hud, "in"),
        _edge(add, "value", convert, "value", "number"),
        _edge(convert, "value", join, "a", "text"),
        _edge(join, "value", hud, "text", "text"),
    ]

    class Game:
        def __init__(self): self.text = ""
        def set_hud(self, _key, text): self.text = text

    game = Game()
    LogicGraphRuntime(graph).update(game, 0.016)
    assert game.text == "5.0 pontos"


def test_gameplay_block_library_exposes_expected_typed_ports():
    assert ("other", "object") in node_port_definitions("event_trigger_enter")["outputs"]
    assert ("degrees", "number") in node_port_definitions("rotate")["inputs"]
    assert node_port_definitions("destroy_object")["outputs"] == []
    assert ("value", "number") in node_port_definitions("clamp_number")["outputs"]
    assert ("value", "text") in node_port_definitions("join_text")["outputs"]


def test_score_library_demo_is_reusable_and_executable():
    root = Path(__file__).resolve().parents[2]
    asset = load_logic_graph(root / "Assets/Logic/CalcularPontuacao.zlogic")
    assert not validate_logic_graph(asset)
    runtime = LogicGraphRuntime(asset, call_stack=("demo",))
    assert runtime.run_subgraph(object(), 0.0, {"pontos_base": 75}) == {"pontuacao_final": 150.0}


def test_beginner_recipe_search_builds_move_x_flow():
    matches = find_logic_recipes("mover sozinho x")
    assert matches[0]["id"] == "move_x_every_frame"
    fragment = build_logic_recipe("move_x_every_frame", (50.0, 80.0))
    assert [node["type"] for node in fragment["nodes"]] == ["event_update", "move_by"]
    assert fragment["nodes"][1]["properties"] == {"x": 120.0, "y": 0.0}
    assert fragment["edges"][0]["kind"] == "flow"
    assert fragment["nodes"][0]["position"] == [50.0, 80.0]


def test_position_nodes_move_per_second_and_read_current_coordinates():
    update = create_logic_node("event_update")
    move = create_logic_node("move_by")
    move["properties"].update({"x": 120.0, "y": -40.0})
    position = create_logic_node("get_position")
    convert = create_logic_node("to_text")
    hud = create_logic_node("set_hud")
    graph = default_logic_graph("AutomaticPosition")
    graph["nodes"] = [update, move, position, convert, hud]
    graph["edges"] = [
        _edge(update, "next", move, "in"),
        _edge(move, "next", hud, "in"),
        _edge(position, "x", convert, "value", "number"),
        _edge(convert, "value", hud, "text", "text"),
    ]

    class Game:
        def __init__(self): self.x, self.y, self.text = 10.0, 20.0, ""
        def move(self, dx, dy=0.0): self.x += dx; self.y += dy
        def set_hud(self, _key, text): self.text = text

    game = Game()
    LogicGraphRuntime(graph).update(game, 0.5)
    assert (game.x, game.y) == (70.0, 0.0)
    assert game.text == "70.0"


def test_unconnected_action_target_means_current_object_without_copying_it():
    update = create_logic_node("event_update")
    position = create_logic_node("set_position")
    position["properties"].update({"x": 25.0, "y": 40.0})
    rotate = create_logic_node("rotate")
    rotate["properties"]["degrees"] = 15.0
    active = create_logic_node("set_active")
    active["properties"]["active"] = False
    graph = default_logic_graph("CurrentObjectTarget")
    graph["nodes"] = [update, position, rotate, active]
    graph["edges"] = [
        _edge(update, "next", position, "in"),
        _edge(position, "next", rotate, "in"),
        _edge(rotate, "next", active, "in"),
    ]

    class Game:
        x, y, rotation, active = 0.0, 0.0, 0.0, True

    game = Game()
    LogicGraphRuntime(graph).update(game, 0.016)
    assert (game.x, game.y, game.rotation, game.active) == (25.0, 40.0, 15.0, False)


def test_recipe_catalog_filters_by_topic_and_keeps_every_recipe_valid():
    action_ids = {recipe["id"] for recipe in find_logic_recipes("", "Ação")}
    assert {"sprite_on_start", "animation_asset_on_start", "sound_on_start"} <= action_ids
    assert "move_x_every_frame" not in action_ids
    assert len(LOGIC_RECIPES) >= 14
    for recipe in LOGIC_RECIPES:
        fragment = build_logic_recipe(str(recipe["id"]))
        graph = default_logic_graph(str(recipe["id"]))
        graph["nodes"] = fragment["nodes"]
        graph["edges"] = fragment["edges"]
        errors = [issue for issue in validate_logic_graph(graph) if issue["level"] == "error"]
        assert not errors, recipe["id"]


def test_visual_asset_actions_call_image_animation_and_sound_apis():
    start = create_logic_node("event_start")
    sprite = create_logic_node("set_sprite")
    sprite["properties"]["path"] = "Assets/Textures/player.png"
    animation = create_logic_node("play_animation_asset")
    animation["properties"]["path"] = "Assets/Animations/walk.zanim"
    sound = create_logic_node("play_sound")
    sound["properties"]["path"] = "Assets/Audio/step.ogg"
    graph = default_logic_graph("VisualAssets")
    graph["nodes"] = [start, sprite, animation, sound]
    graph["edges"] = [
        _edge(start, "next", sprite, "in"),
        _edge(sprite, "next", animation, "in"),
        _edge(animation, "next", sound, "in"),
    ]

    class Game:
        def __init__(self): self.calls = []
        def set_sprite(self, path): self.calls.append(("image", path))
        def play_animation_asset(self, path): self.calls.append(("animation", path))
        def play_sound(self, path): self.calls.append(("audio", path))

    game = Game()
    LogicGraphRuntime(graph).start(game)
    assert game.calls == [
        ("image", "Assets/Textures/player.png"),
        ("animation", "Assets/Animations/walk.zanim"),
        ("audio", "Assets/Audio/step.ogg"),
    ]
