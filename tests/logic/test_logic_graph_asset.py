from __future__ import annotations

from pathlib import Path

from engine.logic.graph_asset import (
    create_logic_node,
    default_logic_graph,
    load_logic_graph,
    normalize_logic_graph,
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
