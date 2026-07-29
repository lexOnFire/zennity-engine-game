from __future__ import annotations

from pathlib import Path

from engine.logic.graph_asset import (
    consolidate_logic_events,
    create_logic_node,
    default_logic_graph,
    load_logic_graph,
    merge_logic_fragment,
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
from engine.logic.code_preview import node_code_preview


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


def test_node_editor_layout_is_persistent_and_safely_clamped(tmp_path):
    graph = default_logic_graph("Layout")
    node = create_logic_node("move")
    node["editor"] = {"collapsed": True, "width": 9999, "height": 640}
    graph["nodes"] = [node]

    saved = save_logic_graph(tmp_path / "layout.zlogic", graph)
    restored = load_logic_graph(tmp_path / "layout.zlogic")

    assert saved["nodes"][0]["editor"] == {
        "collapsed": True,
        "width": 520.0,
        "height": 640.0,
    }
    assert restored["nodes"][0]["editor"] == saved["nodes"][0]["editor"]


def test_old_nodes_receive_default_editor_layout():
    graph = default_logic_graph("LegacyLayout")
    graph["nodes"] = [{
        "id": "legacy", "type": "event_start", "title": "Ao iniciar",
        "category": "Eventos", "position": [0, 0], "properties": {},
    }]

    editor_state = normalize_logic_graph(graph)["nodes"][0]["editor"]

    assert editor_state == {"collapsed": False, "width": 210.0, "height": 0.0}


def test_graph_annotations_are_persistent_and_clamped(tmp_path):
    graph = default_logic_graph("Organized")
    graph["editor"] = {
        "groups": [{"id": "g", "title": "Movimento", "position": [10, 20], "size": [10, 9999]}],
        "comments": [{"id": "c", "text": "Explicação", "position": [30, 40], "width": 9999}],
    }
    saved = save_logic_graph(tmp_path / "organized.zlogic", graph)
    assert saved["editor"]["groups"][0]["size"] == [240.0, 1200.0]
    assert saved["editor"]["comments"][0]["width"] == 720.0


def test_validation_reports_unreachable_flow_and_execution_cycle():
    event = create_logic_node("event_start")
    first = create_logic_node("log_message")
    second = create_logic_node("log_message")
    detached = create_logic_node("log_message")
    graph = default_logic_graph("Unsafe")
    graph["nodes"] = [event, first, second, detached]
    graph["edges"] = [
        _edge(event, "next", first, "in"),
        _edge(first, "next", second, "in"),
        _edge(second, "next", first, "in"),
    ]
    issues = validate_logic_graph(graph)
    messages = [issue["message"] for issue in issues]
    assert any("Execution cycle detected" in message for message in messages)
    assert any("Disconnected node" in message for message in messages)


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


def test_consolidate_duplicate_frame_events_preserves_every_branch():
    first_event = create_logic_node("event_update")
    duplicate_event = create_logic_node("event_update")
    move_x = create_logic_node("move_by")
    move_y = create_logic_node("move_by")
    graph = default_logic_graph("FanOut")
    graph["nodes"] = [first_event, duplicate_event, move_x, move_y]
    graph["edges"] = [
        _edge(first_event, "next", move_x, "in"),
        _edge(duplicate_event, "next", move_y, "in"),
    ]
    graph["debug"]["breakpoints"] = [duplicate_event["id"]]

    consolidated, removed = consolidate_logic_events(graph)

    events = [node for node in consolidated["nodes"] if node["type"] == "event_update"]
    outgoing = [edge for edge in consolidated["edges"] if edge["from_node"] == events[0]["id"]]
    assert removed == 1
    assert len(events) == 1
    assert len(outgoing) == 2
    assert consolidated["debug"]["breakpoints"] == [events[0]["id"]]


def test_recipe_merge_reuses_frame_event_and_executes_parallel_actions():
    base = build_logic_recipe("move_x_every_frame")
    graph = default_logic_graph("ParallelRecipes")
    graph["nodes"], graph["edges"] = base["nodes"], base["edges"]

    merged, reused = merge_logic_fragment(graph, build_logic_recipe("patrol_y_between_limits"))
    events = [node for node in merged["nodes"] if node["type"] == "event_update"]
    outgoing = [edge for edge in merged["edges"] if edge["from_node"] == events[0]["id"]]

    class Game:
        def __init__(self): self.x, self.y = 0.0, 0.0
        def move(self, dx, dy=0.0): self.x += dx; self.y += dy

    game = Game()
    LogicGraphRuntime(merged).update(game, 0.5)
    assert reused == 1
    assert len(events) == 1
    assert len(outgoing) == 2
    assert (game.x, game.y) == (60.0, 50.0)
    assert not any("Duplicate event" in issue["message"] for issue in validate_logic_graph(merged))


def test_validation_explains_duplicate_frame_event():
    graph = default_logic_graph("DuplicateEvent")
    graph["nodes"] = [create_logic_node("event_update"), create_logic_node("event_update")]
    assert any("Duplicate event" in issue["message"] for issue in validate_logic_graph(graph))


def test_validation_reports_missing_event_and_disconnected_node():
    graph = default_logic_graph()
    graph["nodes"] = [create_logic_node("move"), create_logic_node("jump")]
    issues = validate_logic_graph(graph)
    assert any("Add On Start, On Update" in issue["message"] for issue in issues)
    assert len([issue for issue in issues if "Disconnected node" in issue["message"]]) == 2


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
    assert any("Non-existent output port" in message for message in messages)


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
    assert "variable 'variavel_que_nao_existe' not found" in runtime.debug_snapshot()["condition_error"]


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
    matches = find_logic_recipes("Move Automatically on X Axis")
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
    action_ids = {recipe["id"] for recipe in find_logic_recipes("", "Action")}
    assert {"sprite_on_start", "animation_asset_on_start", "sound_on_start"} <= action_ids
    assert "move_x_every_frame" not in action_ids
    assert len(LOGIC_RECIPES) >= 22
    for recipe in LOGIC_RECIPES:
        fragment = build_logic_recipe(str(recipe["id"]))
        graph = default_logic_graph(str(recipe["id"]))
        graph["nodes"] = fragment["nodes"]
        graph["edges"] = fragment["edges"]
        errors = [issue for issue in validate_logic_graph(graph) if issue["level"] == "error"]
        assert not errors, recipe["id"]


def test_code_editing_recipes_are_searchable_and_build_editable_graphs():
    recipe_ids = {recipe["id"] for recipe in find_logic_recipes("code edit")}
    expected = {
        "code_edit_spin_on_update",
        "code_edit_diagonal_move",
        "code_edit_key_teleport",
        "code_edit_timer_spawn",
        "code_edit_tunable_jump",
        "code_edit_patrol_bounds",
        "code_edit_scroll_speeds",
        "code_edit_number_driven_move",
    }
    assert expected <= recipe_ids
    fragment = build_logic_recipe("code_edit_diagonal_move", (10.0, 20.0))
    node_types = [node["type"] for node in fragment["nodes"]]
    move = next(node for node in fragment["nodes"] if node["type"] == "move_by")
    assert node_types == ["event_update", "move_by"]
    assert move["properties"] == {"x": 120.0, "y": -60.0}
    assert "target.x += 120.0 * dt" in node_code_preview(move)


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


def test_scrolling_background_action_configures_and_stops_target():
    start = create_logic_node("event_start")
    scroll = create_logic_node("start_texture_scroll")
    scroll["properties"].update({
        "path": "Assets/Textures/road.png", "speed_x": 0.0,
        "speed_y": 160.0, "repeat_x": False, "repeat_y": True,
        "parallax": 0.5, "send_to_background": True,
    })
    stop = create_logic_node("stop_texture_scroll")
    stop["properties"]["reset"] = True
    graph = default_logic_graph("ScrollingRoad")
    graph["nodes"] = [start, scroll, stop]
    graph["edges"] = [_edge(start, "next", scroll, "in"), _edge(scroll, "next", stop, "in")]

    class Game:
        def __init__(self): self.calls = []
        def start_texture_scroll(self, x, y, **options): self.calls.append(("start", x, y, options))
        def stop_texture_scroll(self, reset=False): self.calls.append(("stop", reset))

    game = Game()
    LogicGraphRuntime(graph).start(game)

    assert game.calls == [
        ("start", 0.0, 160.0, {
            "repeat_x": False, "repeat_y": True, "parallax": 0.5,
            "image_path": "Assets/Textures/road.png",
            "send_to_background": True,
        }),
        ("stop", True),
    ]


def test_created_event_uses_new_object_as_implicit_target():
    start = create_logic_node("event_start")
    create = create_logic_node("create_object")
    create["properties"].update({"name": "Projectile", "inherit_source": False})
    created_event = create_logic_node("event_object_created")
    position = create_logic_node("set_position")
    position["properties"].update({"x": 90.0, "y": 40.0})
    graph = default_logic_graph("SpawnEvents")
    graph["nodes"] = [start, create, created_event, position]
    graph["edges"] = [
        _edge(start, "next", create, "in"),
        _edge(created_event, "next", position, "in"),
    ]

    class Created:
        active = True
        x = y = 0.0

    class Game:
        x = y = 0.0
        def __init__(self): self.created = Created()
        def create_object(self, **_values): return self.created

    game = Game()
    LogicGraphRuntime(graph).start(game)

    assert (game.created.x, game.created.y) == (90.0, 40.0)


def test_spawn_limit_uses_dedicated_flow_without_creating_object():
    start = create_logic_node("event_start")
    create = create_logic_node("create_object")
    create["properties"].update({"inherit_source": False, "max_instances": 3})
    blocked = create_logic_node("log_message")
    blocked["properties"]["text"] = "limite"
    graph = default_logic_graph("SpawnLimit")
    graph["nodes"] = [start, create, blocked]
    graph["edges"] = [
        _edge(start, "next", create, "in"),
        _edge(create, "limit_reached", blocked, "in"),
    ]

    class Game:
        x = y = 0.0
        def __init__(self): self.logs = []
        def can_spawn(self, _group, maximum): return maximum < 3
        def create_object(self, **_values): raise AssertionError("não deve criar")
        def log(self, text): self.logs.append(text)

    game = Game()
    LogicGraphRuntime(graph).start(game)

    assert game.logs == ["limite"]


def test_same_motion_block_keeps_multiple_spawned_targets_moving():
    key = create_logic_node("event_key_pressed")
    key["properties"]["key"] = "D"
    create = create_logic_node("create_object")
    create["properties"]["name"] = "Shot"
    motion = create_logic_node("start_continuous_motion")
    motion["properties"].update({"x": 10.0, "y": 0.0})
    graph = default_logic_graph("MultiShot")
    graph["nodes"] = [key, create, motion]
    graph["edges"] = [
        _edge(key, "next", create, "in"),
        _edge(create, "next", motion, "in"),
    ]

    class Created:
        active = True
        def __init__(self):
            self.x = self.y = 0.0
        def move(self, dx, dy=0.0):
            self.x += dx
            self.y += dy

    class Game:
        active = True
        x = y = 0.0
        def __init__(self):
            self.presses = iter((True, True, False))
            self.created = []
        def key_pressed(self, _key): return next(self.presses)
        def clone_object(self, _source, _name):
            created = Created()
            self.created.append(created)
            return created
        def move(self, _dx, _dy=0.0): pass

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.update(game, 0.1)
    runtime.update(game, 0.1)
    runtime.update(game, 0.1)

    assert len(game.created) == 2
    assert game.created[0].x == 3.0
    assert game.created[1].x == 2.0


def test_named_permanent_movements_can_run_together_in_global_and_local_space():
    start = create_logic_node("event_start")
    horizontal = create_logic_node("start_continuous_motion")
    horizontal["properties"].update({"movement": "Horizontal", "x": 10.0, "y": 0.0})
    vertical = create_logic_node("start_continuous_motion")
    vertical["properties"].update({"movement": "Vertical", "x": 0.0, "y": 20.0})
    graph = default_logic_graph("TwoMotions")
    graph["nodes"] = [start, horizontal, vertical]
    graph["edges"] = [
        _edge(start, "next", horizontal, "in"),
        _edge(start, "next", vertical, "in"),
    ]

    class Game:
        active = True
        rotation = 0.0

        def __init__(self):
            self.x = self.y = 0.0

        def move(self, dx, dy=0.0):
            self.x += dx
            self.y += dy

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.start(game)
    runtime.update(game, 1.0)

    assert (game.x, game.y) == (10.0, 20.0)
    assert {state["name"] for state in runtime._persistent_motion.values()} == {"Horizontal", "Vertical"}

    local_graph = default_logic_graph("LocalMotion")
    local_start = create_logic_node("event_start")
    local_motion = create_logic_node("start_continuous_motion")
    local_motion["properties"].update({"movement": "Frente", "x": 10.0, "y": 0.0, "space": "local"})
    local_graph["nodes"] = [local_start, local_motion]
    local_graph["edges"] = [_edge(local_start, "next", local_motion, "in")]
    local_game = Game()
    local_game.rotation = 90.0
    local_runtime = LogicGraphRuntime(local_graph)
    local_runtime.start(local_game)
    local_runtime.update(local_game, 1.0)
    assert abs(local_game.x) < 1e-6
    assert local_game.y == 10.0


def test_permanent_motion_can_accelerate_change_pause_resume_query_and_stop():
    start = create_logic_node("event_start")
    motion = create_logic_node("start_continuous_motion")
    motion["properties"].update({
        "movement": "Corrida", "x": 20.0, "y": 0.0,
        "acceleration": 10.0, "deceleration": 10.0,
    })
    update_event = create_logic_node("event_update")
    query = create_logic_node("get_continuous_motion")
    query["properties"]["movement"] = "Corrida"
    key_faster = create_logic_node("event_key_pressed")
    key_faster["properties"]["key"] = "U"
    faster = create_logic_node("update_continuous_motion")
    faster["properties"].update({"movement": "Corrida", "x": 40.0, "y": 0.0, "acceleration": 20.0})
    key_pause = create_logic_node("event_key_pressed")
    key_pause["properties"]["key"] = "P"
    pause = create_logic_node("pause_continuous_motion")
    pause["properties"]["movement"] = "Corrida"
    key_resume = create_logic_node("event_key_pressed")
    key_resume["properties"]["key"] = "R"
    resume = create_logic_node("resume_continuous_motion")
    resume["properties"]["movement"] = "Corrida"
    key_stop = create_logic_node("event_key_pressed")
    key_stop["properties"]["key"] = "S"
    stop = create_logic_node("stop_continuous_motion")
    stop["properties"].update({"movement": "Corrida", "smooth": True})
    graph = default_logic_graph("ControlledMotion")
    graph["nodes"] = [
        start, motion, update_event, query, key_faster, faster,
        key_pause, pause, key_resume, resume, key_stop, stop,
    ]
    graph["edges"] = [
        _edge(start, "next", motion, "in"),
        _edge(update_event, "next", query, "in"),
        _edge(key_faster, "next", faster, "in"),
        _edge(key_pause, "next", pause, "in"),
        _edge(key_resume, "next", resume, "in"),
        _edge(key_stop, "next", stop, "in"),
    ]

    class Game:
        active = True
        rotation = 0.0

        def __init__(self):
            self.x = self.y = 0.0
            self.pressed = set()
            self.debug = {}

        def move(self, dx, dy=0.0):
            self.x += dx
            self.y += dy

        def key_pressed(self, key):
            return key in self.pressed

        def update_motion_debug(self, handle, state):
            self.debug[handle] = state

        def remove_motion_debug(self, handle):
            self.debug.pop(handle, None)

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.start(game)
    runtime.update(game, 1.0)
    state = next(iter(runtime._persistent_motion.values()))
    assert state["current_x"] == 10.0
    assert runtime.values[(query["id"], "speed")] == 10.0

    game.pressed = {"u"}
    runtime.update(game, 1.0)
    game.pressed.clear()
    assert state["desired_x"] == 40.0

    game.pressed = {"p"}
    runtime.update(game, 0.0)
    game.pressed.clear()
    runtime.update(game, 1.0)
    assert state["paused"] is True and state["current_x"] == 10.0

    game.pressed = {"r"}
    runtime.update(game, 0.0)
    game.pressed.clear()
    runtime.update(game, 1.0)
    assert state["paused"] is False and state["current_x"] == 30.0

    game.pressed = {"s"}
    runtime.update(game, 0.0)
    game.pressed.clear()
    for _ in range(4):
        runtime.update(game, 1.0)
    assert not runtime._persistent_motion
    assert not game.debug


def test_permanent_motion_nodes_expose_handles_and_query_outputs():
    assert node_port_definitions("start_continuous_motion")["outputs"][-1] == ("movement", "movement")
    for node_type in (
        "update_continuous_motion", "pause_continuous_motion",
        "resume_continuous_motion", "stop_continuous_motion",
    ):
        assert ("movement", "movement") in node_port_definitions(node_type)["inputs"]
    outputs = node_port_definitions("get_continuous_motion")["outputs"]
    assert {"x", "y", "speed", "paused", "active"}.issubset({name for name, _kind in outputs})
    assert "update_motion" in node_code_preview(create_logic_node("update_continuous_motion"))
    assert any(recipe["id"] == "controlled_permanent_motion" for recipe in LOGIC_RECIPES)


def test_held_and_just_pressed_keys_are_distinct_conditions():
    held = create_logic_node("key_held")
    pressed = create_logic_node("key_pressed")
    assert held["title"] == "Key Held?"
    assert pressed["title"] == "Key Pressed Now?"


def test_prefab_node_rejects_invalid_extension_and_override_size():
    graph = default_logic_graph("PrefabValidation")
    node = create_logic_node("create_prefab")
    node["properties"]["path"] = "Assets/Prefabs/bullet.png"
    node["properties"]["override_scale"] = True
    node["properties"]["width"] = 0.0
    node["properties"]["height"] = 0.0
    graph["nodes"] = [create_logic_node("event_start"), node]
    graph["edges"] = [_edge(graph["nodes"][0], "next", node, "in")]
    messages = {issue["message"] for issue in validate_logic_graph(graph)}
    assert "The chosen file must be a .zprefab." in messages
    assert "Prefab width and height must be greater than zero." in messages
