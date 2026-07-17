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
    assert any("Ciclo de execução" in message for message in messages)
    assert any("Nó desconectado" in message for message in messages)


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
    assert not any("Evento duplicado" in issue["message"] for issue in validate_logic_graph(merged))


def test_validation_explains_duplicate_frame_event():
    graph = default_logic_graph("DuplicateEvent")
    graph["nodes"] = [create_logic_node("event_update"), create_logic_node("event_update")]
    assert any("Evento duplicado" in issue["message"] for issue in validate_logic_graph(graph))


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


def test_patrol_y_recipe_reverses_at_positive_and_negative_limits():
    recipe = next(recipe for recipe in LOGIC_RECIPES if recipe["id"] == "patrol_y_between_limits")
    fragment = build_logic_recipe(str(recipe["id"]))
    graph = default_logic_graph("PatrolY")
    graph["nodes"], graph["edges"] = fragment["nodes"], fragment["edges"]

    class Game:
        def __init__(self): self.x, self.y, self.overridden = 0.0, 0.0, []
        def move(self, dx, dy=0.0): self.x += dx; self.y += dy
        def override_physics_axis(self, axis): self.overridden.append(axis)

    game = Game()
    runtime = LogicGraphRuntime(graph)
    positions = []
    for _ in range(7):
        runtime.update(game, 0.5)
        positions.append(game.y)
    assert positions == [50.0, 100.0, 50.0, 0.0, -50.0, -100.0, -50.0]
    assert game.overridden == ["y"] * 7


def test_every_visual_node_has_a_readable_code_backside():
    patrol = create_logic_node("patrol_axis")
    patrol["properties"].update({"axis": "Y", "minimum": -100, "maximum": 100, "speed": 80})
    code = node_code_preview(patrol)
    assert "pos >= 100" in code
    assert "pos <= -100" in code
    assert "direção" in code
    assert "dt" in code
    assert node_code_preview(create_logic_node("event_update")).startswith("a_cada_frame")
    assert node_code_preview(create_logic_node("set_sprite"))


def test_create_object_node_returns_reference_for_following_actions():
    event = create_logic_node("event_start")
    create = create_logic_node("create_object")
    create["properties"].update({"name": "Moeda", "x": 10, "y": 20, "relative": True})
    position = create_logic_node("set_position")
    position["properties"].update({"x": 80, "y": 90})
    graph = default_logic_graph("Spawner")
    graph["nodes"] = [event, create, position]
    graph["edges"] = [
        _edge(event, "next", create, "in"),
        _edge(create, "next", position, "in"),
        _edge(create, "object", position, "target", "object"),
    ]

    class Created:
        def __init__(self, x, y): self.x, self.y = x, y

    class Game:
        x, y = 100.0, 200.0
        def __init__(self): self.created = []; self.last = None
        def create_object(self, **values):
            self.created.append(values)
            self.last = Created(values["x"], values["y"])
            return self.last

    game = Game()
    LogicGraphRuntime(graph).start(game)
    assert game.created[0]["name"] == "Moeda"
    assert (game.created[0]["x"], game.created[0]["y"]) == (110.0, 220.0)
    assert (game.last.x, game.last.y) == (80.0, 90.0)
    result = game.created[0]
    assert result["width"] == 64.0 and result["height"] == 64.0
    assert node_port_definitions("create_object")["outputs"] == [
        ("next", "flow"), ("limit_reached", "flow"), ("object", "object")
    ]
    assert "criar_objeto" in node_code_preview(create)


def test_create_object_can_inherit_original_as_an_independent_clone():
    event = create_logic_node("event_start")
    create = create_logic_node("create_object")
    create["properties"].update({"name": "PlayerClone", "x": 40, "y": 50})
    graph = default_logic_graph("CloneSpawner")
    graph["nodes"] = [event, create]
    graph["edges"] = [_edge(event, "next", create, "in")]

    class Created:
        x = y = 0.0

    class Game:
        x = y = 0.0
        def __init__(self): self.clone = Created(); self.source = None
        def clone_object(self, source, name):
            self.source = source
            assert name == "PlayerClone"
            return self.clone

    game = Game()
    LogicGraphRuntime(graph).start(game)
    assert game.source is game
    assert (game.clone.x, game.clone.y) == (40.0, 50.0)


def test_key_event_starts_motion_once_and_motion_continues_after_release():
    key_event = create_logic_node("event_key_pressed")
    key_event["properties"]["key"] = "D"
    motion = create_logic_node("start_continuous_motion")
    motion["properties"].update({"x": 120.0, "y": 0.0})
    graph = default_logic_graph("PermanentMovement")
    graph["nodes"] = [key_event, motion]
    graph["edges"] = [_edge(key_event, "next", motion, "in")]

    class Game:
        active = True
        def __init__(self): self.x = 0.0; self.y = 0.0; self.just_pressed = True
        def key_pressed(self, key):
            assert key == "d"
            value = self.just_pressed
            self.just_pressed = False
            return value
        def move(self, dx, dy=0.0): self.x += dx; self.y += dy

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.update(game, 0.1)
    first_position = game.x
    runtime.update(game, 0.1)
    runtime.update(game, 0.1)

    assert first_position == 12.0
    assert game.x == 36.0
    assert runtime._persistent_motion


def test_created_object_becomes_implicit_target_for_following_actions():
    key_event = create_logic_node("event_key_pressed")
    key_event["properties"]["key"] = "D"
    create = create_logic_node("create_object")
    create["properties"].update({"name": "Projectile", "x": 10.0, "y": 20.0})
    motion = create_logic_node("start_continuous_motion")
    motion["properties"].update({"x": 100.0, "y": 0.0})
    graph = default_logic_graph("SpawnAndMove")
    graph["nodes"] = [key_event, create, motion]
    # Somente os fios de fluxo: a referência criada é carregada implicitamente.
    graph["edges"] = [
        _edge(key_event, "next", create, "in"),
        _edge(create, "next", motion, "in"),
    ]

    class Created:
        active = True
        def __init__(self): self.x = 0.0; self.y = 0.0
        def move(self, dx, dy=0.0): self.x += dx; self.y += dy

    class Game:
        active = True
        x = y = 0.0
        def __init__(self): self.created = Created(); self.pressed = True
        def key_pressed(self, _key):
            value = self.pressed
            self.pressed = False
            return value
        def clone_object(self, _source, _name): return self.created
        def move(self, dx, dy=0.0): self.x += dx; self.y += dy

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.update(game, 0.1)
    runtime.update(game, 0.1)

    assert game.x == 0.0
    assert (game.created.x, game.created.y) == (30.0, 20.0)
    assert next(iter(runtime._persistent_motion.values()))["target"] is game.created


def test_held_and_just_pressed_keys_are_distinct_conditions():
    pressed = create_logic_node("key_pressed")
    held = create_logic_node("key_held")
    assert pressed["title"] == "Tecla apertada agora?"
    assert held["title"] == "Tecla está segurada?"
    assert "tecla_acionada" in node_code_preview(pressed)
    assert "tecla_ativa" in node_code_preview(held)


def test_create_object_recipe_is_available_for_beginners():
    recipe = next(item for item in LOGIC_RECIPES if item["id"] == "create_object_on_start")
    fragment = build_logic_recipe(str(recipe["id"]))
    assert [node["type"] for node in fragment["nodes"]] == ["event_start", "create_object"]


def test_once_and_cooldown_control_repeated_frame_flow():
    event = create_logic_node("event_update")
    once = create_logic_node("once")
    cooldown = create_logic_node("cooldown")
    cooldown["properties"]["seconds"] = 1.0
    once_log = create_logic_node("log_message")
    once_log["properties"]["text"] = "once"
    cooldown_log = create_logic_node("log_message")
    cooldown_log["properties"]["text"] = "cooldown"
    graph = default_logic_graph("FlowControl")
    graph["nodes"] = [event, once, cooldown, once_log, cooldown_log]
    graph["edges"] = [
        _edge(event, "next", once, "in"),
        _edge(event, "next", cooldown, "in"),
        _edge(once, "next", once_log, "in"),
        _edge(cooldown, "next", cooldown_log, "in"),
    ]

    class Game:
        def __init__(self): self.messages = []
        def log(self, message): self.messages.append(message)

    game = Game()
    runtime = LogicGraphRuntime(graph)
    runtime.update(game, 0.25)
    runtime.update(game, 0.25)
    runtime.update(game, 0.75)
    assert game.messages == ["once", "cooldown", "cooldown"]


def test_prefab_and_component_nodes_share_created_object_reference():
    event = create_logic_node("event_start")
    prefab = create_logic_node("create_prefab")
    prefab["properties"]["path"] = "Assets/Prefabs/Enemy.zprefab"
    component = create_logic_node("add_component")
    component["properties"].update({"component": "RigidBody2D", "properties": {"gravity_scale": 2}})
    graph = default_logic_graph("PrefabSpawner")
    graph["nodes"] = [event, prefab, component]
    graph["edges"] = [
        _edge(event, "next", prefab, "in"),
        _edge(prefab, "next", component, "in"),
        _edge(prefab, "object", component, "target", "object"),
    ]

    class Created:
        def __init__(self): self.components = []
        def add_component(self, name, properties): self.components.append((name, properties))

    class Game:
        x = y = 0
        def __init__(self): self.created = Created()
        def create_prefab(self, path, x, y):
            assert (path, x, y) == ("Assets/Prefabs/Enemy.zprefab", 0.0, 0.0)
            return self.created

    game = Game()
    LogicGraphRuntime(graph).start(game)
    assert game.created.components == [("RigidBody2D", {"gravity_scale": 2})]
    assert not validate_logic_graph(graph)


def test_prefab_node_requires_an_asset():
    graph = default_logic_graph("InvalidPrefab")
    graph["nodes"] = [create_logic_node("event_start"), create_logic_node("create_prefab")]
    assert any(".zprefab" in issue["message"] for issue in validate_logic_graph(graph))


def test_fan_out_uses_explicit_stable_order_and_tolerates_invalid_order():
    event = create_logic_node("event_start")
    first = create_logic_node("log_message")
    first["properties"]["text"] = "first"
    second = create_logic_node("log_message")
    second["properties"]["text"] = "second"
    graph = default_logic_graph("OrderedFanOut")
    graph["nodes"] = [event, first, second]
    graph["edges"] = [
        {**_edge(event, "next", second, "in"), "order": 20},
        {**_edge(event, "next", first, "in"), "order": 10},
    ]

    class Game:
        def __init__(self): self.messages = []
        def log(self, message): self.messages.append(message)

    game = Game()
    LogicGraphRuntime(graph).start(game)
    assert game.messages == ["first", "second"]

    graph["edges"][0]["order"] = "inválida"
    normalized = normalize_logic_graph(graph)
    assert isinstance(normalized["edges"][0]["order"], int)


def test_clone_remove_component_and_restart_scene_nodes_execute_together():
    event = create_logic_node("event_start")
    clone = create_logic_node("clone_object")
    clone["properties"]["name"] = "Clone"
    remove = create_logic_node("remove_component")
    remove["properties"]["component"] = "BoxCollider"
    restart = create_logic_node("restart_scene")
    graph = default_logic_graph("CloneAndRestart")
    graph["nodes"] = [event, clone, remove, restart]
    graph["edges"] = [
        _edge(event, "next", clone, "in"),
        _edge(clone, "next", remove, "in"),
        _edge(clone, "object", remove, "target", "object"),
        _edge(remove, "next", restart, "in"),
    ]

    class Created:
        def __init__(self): self.removed = []
        def remove_component(self, name): self.removed.append(name)

    class Game:
        def __init__(self): self.created = Created(); self.restarted = False
        def clone_object(self, source, name):
            assert source is self and name == "Clone"
            return self.created
        def restart(self): self.restarted = True

    game = Game()
    LogicGraphRuntime(graph).start(game)
    assert game.created.removed == ["BoxCollider"]
    assert game.restarted is True
