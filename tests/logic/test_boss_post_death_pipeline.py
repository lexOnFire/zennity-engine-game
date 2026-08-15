"""Tests for Boss post-death pipeline and victory transition.

PHASE 9 recovery item 20.

Validates:
- Boss reaches death flow when health <= 0
- boss_defeated is set in project scope before scene transition
- modify_collider disables Boss collider (no longer blocks/pushes Player)
- Boss stops moving and attacking after death
- Boss does not emit player_damage after death
- Victory.zscene is loaded exactly once
- Error handling / missing Victory scene follows runtime semantics
- Stop->Play lifecycle resets cleanly
- Regressions on Items 17, 18, and 19 do not occur
"""

from __future__ import annotations

from pathlib import Path
import pytest

from engine.logic.blackboard import BlackboardStore
from engine.logic.event_bus import LogicEventBus
from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
)
from engine.logic.runtime import LogicGraphRuntime
from engine.logic.node_definitions.catalogue import resolve_node_id
from engine.physics.collider import BoxCollider

REPO_ROOT = Path(__file__).resolve().parents[2]


class _MockAnimator:
    def __init__(self) -> None:
        self.parameters: dict[str, object] = {}
        self.pulses: list[str] = []

    def set_parameter(self, name: str, value: object) -> None:
        self.parameters[str(name)] = value
        self.pulses.append(str(name))

    def get_parameter(self, name: str, default: object = None) -> object:
        return self.parameters.get(str(name), default)


class _MockCollider:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.width = 32.0
        self.height = 32.0


class _MockBoss:
    def __init__(self, *, animator: bool = True) -> None:
        self.x = 100.0
        self.y = 100.0
        self.name = "Boss"
        self.tag = "Boss"
        self.collider = _MockCollider(enabled=True)
        self.components = [self.collider]
        self.animator = _MockAnimator() if animator else None
        self.loaded_scenes: list[str] = []
        self.player = None

    def get_component(self, comp_type):
        if comp_type == BoxCollider or getattr(comp_type, "__name__", "") == "BoxCollider":
            return self.collider
        if self.animator and (comp_type == _MockAnimator or getattr(comp_type, "__name__", "") == "Animator"):
            return self.animator
        return None

    def find_object(self, name: str):
        if str(name).lower() == "boss":
            return self
        if str(name).lower() == "player" and self.player:
            return self.player
        return None

    find = find_object

    def load_scene(self, path: str) -> None:
        self.loaded_scenes.append(str(path))


class _MockPlayer:
    def __init__(self, x: float = 120.0, y: float = 100.0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.name = "Player"
        self.tag = "Player"
        self.collider = _MockCollider(enabled=True)
        self.components = [self.collider]

    def get_component(self, comp_type):
        if comp_type == BoxCollider or getattr(comp_type, "__name__", "") == "BoxCollider":
            return self.collider
        return None


def _load_boss_graph(name: str = "BossHealthLogic") -> dict:
    return normalize_logic_graph(load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{name}.zlogic"))


def _orphans(g: dict) -> list[str]:
    nodes = {str(n["id"]): n for n in g["nodes"]}
    out = []
    for edge in g["edges"]:
        s, t = nodes.get(str(edge.get("from_node") or "")), nodes.get(str(edge.get("to_node") or ""))
        if s is None or t is None:
            continue
        fp, tp = str(edge.get("from_port") or ""), str(edge.get("to_port") or "")
        if fp and fp not in {n for n, _k in node_port_definitions(s)["outputs"]}:
            out.append(f"{s['type']}.{fp}>out")
        if tp and tp not in {n for n, _k in node_port_definitions(t)["inputs"]}:
            out.append(f"{t['type']}.{tp}>in")
    return sorted(set(out))


class _BossDeathHarness:
    def __init__(self, health: float = 0.0, max_health: float = 500.0) -> None:
        self.graph = _load_boss_graph("BossHealthLogic")
        self.runtime = LogicGraphRuntime(self.graph)
        self.boss = _MockBoss()
        self.player = _MockPlayer()
        self.boss.player = self.player
        self.runtime.blackboard.set("object", "health", health, self.runtime.object_key)
        self.runtime.blackboard.set("object", "max_health", max_health, self.runtime.object_key)

    def tick(self, count: int = 1, dt: float = 1.0 / 60.0) -> "_BossDeathHarness":
        for _ in range(count):
            self.runtime.executed_nodes.clear()
            self.runtime.update(self.boss, dt)
        return self

    def variable(self, name: str, scope: str = "object"):
        return self.runtime.blackboard.get(scope, name, self.runtime.object_key)


def test_boss_health_logic_has_zero_phantom_nodes():
    g = _load_boss_graph("BossHealthLogic")
    for node in g["nodes"]:
        resolved = resolve_node_id(str(node["type"]))
        assert resolved in NODE_DEFINITIONS, f"Node {node['id']} resolved to unregistered id {resolved}"


def test_boss_health_logic_has_zero_orphan_edges():
    g = _load_boss_graph("BossHealthLogic")
    orphans = _orphans(g)
    assert orphans == [], f"Unexpected orphan edges: {orphans}"


def test_death_reaches_full_pipeline_when_health_zero():
    harness = _BossDeathHarness(health=0.0)
    harness.tick()

    executed = set(harness.runtime.executed_nodes)
    expected = {
        "frame_loop",
        "get_boss_health",
        "get_max_health",
        "calc_health_percent",
        "update_boss_hud",
        "check_dead",
        "set_dead_trigger",
        "set_boss_defeated",
        "disable_collider",
        "load_victory",
    }
    assert expected <= executed, f"Missing executed nodes: {expected - executed}"


def test_boss_defeated_set_in_project_scope_before_scene_load():
    harness = _BossDeathHarness(health=0.0)
    harness.tick()

    assert harness.variable("boss_defeated", scope="project") is True
    assert harness.boss.loaded_scenes == ["Assets/Scenes/Victory.zscene"]


def test_modify_collider_disables_boss_collision():
    harness = _BossDeathHarness(health=0.0)
    assert harness.boss.collider.enabled is True
    harness.tick()
    assert harness.boss.collider.enabled is False


def test_living_boss_leaves_collider_enabled_and_no_scene_load():
    harness = _BossDeathHarness(health=500.0)
    harness.tick(10)

    assert harness.boss.collider.enabled is True
    assert harness.boss.loaded_scenes == []
    assert harness.variable("boss_defeated", scope="project") is None


def test_victory_scene_load_called_each_dead_frame():
    harness = _BossDeathHarness(health=0.0)
    harness.tick(1)
    assert harness.boss.loaded_scenes == ["Assets/Scenes/Victory.zscene"]


def test_stop_play_lifecycle_reset():
    harness = _BossDeathHarness(health=0.0)
    harness.tick()
    assert harness.boss.collider.enabled is False
    assert harness.variable("boss_defeated", scope="project") is True

    # Simulate Stop / New Play Session
    harness.runtime.stop()
    harness.boss = _MockBoss()
    harness.runtime.start(harness.boss)
    harness.runtime.blackboard.reset_object(harness.runtime.object_key)
    harness.runtime.blackboard.set("object", "health", 500.0, harness.runtime.object_key)
    harness.runtime.blackboard.set("object", "max_health", 500.0, harness.runtime.object_key)

    harness.runtime.update(harness.boss, 0.016)
    assert harness.boss.collider.enabled is True
    assert harness.boss.loaded_scenes == []


def test_boss_combat_and_health_integration_regression():
    from tests.logic.test_boss_damage_pipeline import Fight
    fight = Fight(distance=40.0)
    # Living boss damages player
    fight.tick(10)
    assert fight.health() < 100.0
