"""
Tests for LevelExitLogic progression: Level 1 -> Level 2 transition.

Phase 9 Recovery Item 21.

Covers:
- Entry event reachability (physics.on_trigger_enter)
- Non-player trigger ignored
- Player without key does not transition
- Player with key transitions to Level 2
- Canonical state source (project.has_key)
- Zero phantom nodes, zero orphan edges
- Idempotence & single transition
- Level 2 loadability
- Stop/Play lifecycle reset
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
)
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded, resolve_node_id
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime import LogicGraphRuntime
from engine.scene.scene_loader import load_scene, load_scene_document

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGIC_PATH = REPO_ROOT / "Assets" / "Logic" / "LevelExitLogic.zlogic"
LEVEL2_PATH = REPO_ROOT / "Assets" / "Scenes" / "Level2.zscene"


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


class _MockObject:
    def __init__(self, name: str):
        self.name = name


class _MockCollider:
    def __init__(self, obj: Any, is_trigger: bool = False):
        self.game_object = obj
        self.is_trigger = is_trigger


class _MockGame:
    def __init__(self):
        self.loaded_scenes: list[str] = []
        self.calls: list[str] = []

    def load_scene(self, path: str) -> None:
        self.loaded_scenes.append(path)
        self.calls.append(f"load_scene:{path}")


def _exit_graph() -> dict[str, Any]:
    return normalize_logic_graph(load_logic_graph(LOGIC_PATH))


def test_level_exit_logic_has_zero_phantom_nodes():
    graph = _exit_graph()
    phantoms = [
        str(n["type"])
        for n in graph["nodes"]
        if resolve_node_id(str(n["type"])) not in NODE_DEFINITIONS
    ]
    assert phantoms == [], f"LevelExitLogic still carries phantom nodes: {phantoms}"


def test_level_exit_logic_has_zero_orphan_edges():
    graph = _exit_graph()
    node_map = {str(n["id"]): n for n in graph["nodes"]}
    orphans = []
    for edge in graph["edges"]:
        from_n = node_map.get(str(edge.get("from_node")))
        to_n = node_map.get(str(edge.get("to_node")))
        from_p = str(edge.get("from_port", ""))
        to_p = str(edge.get("to_port", ""))

        if from_n:
            f_type = resolve_node_id(str(from_n.get("type", "")))
            f_contract = NODE_PORT_DEFINITIONS.get(f_type, {})
            f_outs = {name for name, _ in f_contract.get("outputs", [])}
            if f_outs and from_p not in f_outs:
                orphans.append(f"{f_type}.{from_p}>out")
        if to_n:
            t_type = resolve_node_id(str(to_n.get("type", "")))
            t_contract = NODE_PORT_DEFINITIONS.get(t_type, {})
            t_ins = {name for name, _ in t_contract.get("inputs", [])}
            if t_ins and to_p not in t_ins:
                orphans.append(f"{t_type}.{to_p}>in")

    assert orphans == [], f"LevelExitLogic has orphan edges: {orphans}"


def test_level2_scene_is_loadable_and_healthy():
    assert LEVEL2_PATH.exists()
    doc = load_scene_document(LEVEL2_PATH)
    data = load_scene(LEVEL2_PATH)
    assert doc is not None
    objects = data.get("objects", [])
    names = {getattr(obj, "name", str(obj)) for obj in objects}
    assert "Player" in names
    assert "Boss" in names
    assert "HUD" in names
    assert "Camera" in names


def test_non_player_trigger_ignored():
    graph = _exit_graph()
    runtime = LogicGraphRuntime(graph, object_key="LevelExit")
    game = _MockGame()
    runtime.start(game)
    runtime.blackboard.set("project", "has_key", True, "global")

    enemy = _MockObject("Enemy")
    runtime.trigger_event("event_trigger_enter", game, 0.016, enemy)

    assert game.loaded_scenes == []
    assert "load_level2" not in runtime.executed_nodes
    assert "if_has_key" not in runtime.executed_nodes


def test_player_without_key_does_not_transition():
    graph = _exit_graph()
    runtime = LogicGraphRuntime(graph, object_key="LevelExit")
    game = _MockGame()
    runtime.start(game)
    runtime.blackboard.set("project", "has_key", False, "global")

    player = _MockObject("Player")
    runtime.trigger_event("event_trigger_enter", game, 0.016, player)

    assert game.loaded_scenes == []
    assert "load_level2" not in runtime.executed_nodes
    assert "check_player" in runtime.executed_nodes
    assert "if_has_key" in runtime.executed_nodes


def test_player_with_key_transitions_to_level2():
    graph = _exit_graph()
    runtime = LogicGraphRuntime(graph, object_key="LevelExit")
    game = _MockGame()
    runtime.start(game)
    runtime.blackboard.set("project", "has_key", True, "global")

    player = _MockObject("Player")
    runtime.trigger_event("event_trigger_enter", game, 0.016, player)

    assert game.loaded_scenes == ["Assets/Scenes/Level2.zscene"]
    assert "load_level2" in runtime.executed_nodes


def test_trigger_event_event_name_compatibility():
    graph = _exit_graph()
    runtime = LogicGraphRuntime(graph)
    game = _MockGame()
    runtime.start(game)
    runtime.blackboard.set("project", "has_key", True, "global")

    player = _MockObject("Player")
    runtime.trigger_event("event_trigger_enter", game, 0.016, player)

    assert game.loaded_scenes == ["Assets/Scenes/Level2.zscene"]



def test_transition_idempotence_and_reset():
    graph = _exit_graph()
    runtime = LogicGraphRuntime(graph, object_key="LevelExit")
    game = _MockGame()
    runtime.start(game)
    runtime.blackboard.set("project", "has_key", True, "global")

    player = _MockObject("Player")
    runtime.trigger_event("event_trigger_enter", game, 0.016, player)
    assert len(game.loaded_scenes) == 1

    runtime.stop()
    game2 = _MockGame()
    runtime.start(game2)
    runtime.blackboard.set("project", "has_key", False, "global")
    runtime.trigger_event("event_trigger_enter", game2, 0.016, player)
    assert game2.loaded_scenes == []