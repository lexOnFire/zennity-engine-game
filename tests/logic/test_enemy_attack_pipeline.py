"""Common enemy actually hurts the player, and the player owns its own health.

PHASE 9 recovery item 19.

EnemyAttackLogic was previously disabled because its only entry event was
``animation.on_event``, which was a phantom node.
This test suite proves that EnemyAttackLogic now runs via ``event.every_frame``
with range, target, and cooldown guards, emitting ``player_damage`` events
that are processed by ``PlayerHealthLogic``.
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
from engine.logic.node_definitions.catalogue import resolve_node_id
from engine.logic.runtime import LogicGraphRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGIC = REPO_ROOT / "Assets" / "Logic"

#: Live values from Enemy.zprfb / Level1.zscene / Level2.zscene.
ENEMY = {
    "health": 100, "max_health": 100, "move_speed": 100,
    "attack_damage": 10, "attack_range": 48, "detection_range": 300,
    "attack_cooldown": 1.0, "cooldown_timer": 1.0,
}
PLAYER = {"health": 100, "max_health": 100, "attack_damage": 25, "attack_range": 64}

#: One cooldown in frames: EnemyAttackLogic decrements 0.016 per tick from attack_cooldown (1.0).
#: 1.0 / 0.016 = 62.5 ticks => ~63 ticks per attack.
COOLDOWN_TICKS = 63


def graph(name: str) -> dict:
    return normalize_logic_graph(load_logic_graph(LOGIC / f"{name}.zlogic"))


class _Animator:
    def __init__(self) -> None:
        self.parameters: dict[str, object] = {}

    def set_parameter(self, name: str, value: object) -> None:
        self.parameters[str(name)] = value

    def get_parameter(self, name: str, default: object = None) -> object:
        return self.parameters.get(str(name), default)


class _Object:
    def __init__(self, x: float, y: float, name: str) -> None:
        self.x = float(x)
        self.y = float(y)
        self.name = name
        self.tag = name
        self.rigidbody = None
        self.components: list = []
        self.animator = _Animator()

    def get_component(self, _component_type):
        return self.animator

    def move(self, delta_x: float, delta_y: float = 0.0) -> None:
        self.x += float(delta_x)
        self.y += float(delta_y)


class _Api(_Object):
    def __init__(self, position: tuple[float, float], name: str, player: _Object | None) -> None:
        super().__init__(position[0], position[1], name)
        self._player = player
        self.progress: dict[str, tuple[float, float]] = {}

    def _lookup(self, wanted: str):
        return self._player if str(wanted).lower() == "player" else self

    find = _lookup
    find_object = _lookup
    find_by_tag = _lookup

    def set_ui_progress(self, widget: str, value: float, maximum: float) -> None:
        self.progress[str(widget)] = (float(value), float(maximum))


class EnemyFight:
    """An enemy and a player sharing one blackboard and one event bus."""

    def __init__(self, distance: float = 30.0, **overrides) -> None:
        self.store = BlackboardStore()
        self.bus = LogicEventBus()
        enemy_vars = {**ENEMY, **{k: v for k, v in overrides.items() if k in ENEMY}}
        player_vars = {**PLAYER, **{k: v for k, v in overrides.items() if k in PLAYER}}
        if "player_health" in overrides:
            player_vars["health"] = overrides["player_health"]
        for key, value in enemy_vars.items():
            self.store.set("object", key, value, "Enemy")
        for key, value in player_vars.items():
            self.store.set("object", key, value, "Player")

        self.player_object = _Object(distance, 0.0, "Player")
        self.enemy_api = _Api((0.0, 0.0), "Enemy", self.player_object)
        self.player_api = _Api((distance, 0.0), "Player", self.player_object)
        self.enemy_attack = LogicGraphRuntime(graph("EnemyAttackLogic"), self.store, "Enemy", self.bus)
        self.player = LogicGraphRuntime(graph("PlayerHealthLogic"), self.store, "Player", self.bus)
        self.player.start(self.player_api)
        self.hits: list[tuple[int, float, float]] = []
        self.tick_index = 0

    def health(self) -> float:
        return self.store.get("object", "health", "Player")

    def tick(self, count: int = 1, dt: float = 1.0 / 60.0) -> "EnemyFight":
        for _ in range(count):
            before = self.health()
            self.enemy_attack.executed_nodes.clear()
            self.enemy_attack.update(self.enemy_api, dt)
            self.bus.dispatch()
            self.player.update(self.player_api, dt)
            self.bus.dispatch()
            after = self.health()
            if after != before:
                self.hits.append((self.tick_index, before, after))
            self.tick_index += 1
        return self


# ---------------------------------------------------------------------------
# Structure tests
# ---------------------------------------------------------------------------


def test_enemy_attack_carries_no_phantom_or_orphan():
    g = graph("EnemyAttackLogic")
    nodes = {str(n["id"]): n for n in g["nodes"]}
    phantom = {str(n["type"]) for n in g["nodes"]
               if resolve_node_id(str(n["type"])) not in NODE_DEFINITIONS}
    orphans = []
    for edge in g["edges"]:
        source, target = nodes[str(edge["from_node"])], nodes[str(edge["to_node"])]
        if str(edge["from_port"]) not in {p for p, _ in node_port_definitions(source)["outputs"]}:
            orphans.append(f"{source['type']}.{edge['from_port']}>out")
        if str(edge["to_port"]) not in {p for p, _ in node_port_definitions(target)["inputs"]}:
            orphans.append(f"{target['type']}.{edge['to_port']}>in")
    assert phantom == set()
    assert sorted(set(orphans)) == []


def test_the_enemy_never_writes_the_players_health_directly():
    g = graph("EnemyAttackLogic")
    writers = [n for n in g["nodes"] if str(n["type"]) == "set_variable"]
    written = {str(n.get("properties", {}).get("name", "")) for n in writers}
    assert "health" not in written
    assert written == {"cooldown_timer"}


def test_enemy_damage_event_matches_player_receiver():
    emitted = {str(n["properties"]["name"]) for n in graph("EnemyAttackLogic")["nodes"]
               if str(n["type"]) == "emit_event"}
    received = {str(n["properties"]["name"]) for n in graph("PlayerHealthLogic")["nodes"]
                if str(n["type"]) == "event_custom"}
    assert emitted == {"player_damage"}
    assert received == {"player_damage"}


# ---------------------------------------------------------------------------
# Damage & Cooldown Execution Tests
# ---------------------------------------------------------------------------


def test_an_enemy_attack_removes_authored_damage():
    fight = EnemyFight().tick()
    assert fight.health() == PLAYER["health"] - ENEMY["attack_damage"]


def test_damage_lands_once_per_cooldown_cycle():
    ticks = COOLDOWN_TICKS * 3
    fight = EnemyFight(player_health=1000).tick(ticks)
    assert len(fight.hits) == 3, fight.hits


def test_out_of_range_enemy_does_no_damage():
    fight = EnemyFight(distance=300.0).tick(COOLDOWN_TICKS * 3)
    assert fight.hits == []
    assert fight.health() == PLAYER["health"]


def test_at_exactly_attack_range_enemy_hits():
    fight = EnemyFight(distance=float(ENEMY["attack_range"])).tick()
    assert fight.health() == PLAYER["health"] - ENEMY["attack_damage"]


def test_beyond_attack_range_enemy_does_not_hit():
    fight = EnemyFight(distance=ENEMY["attack_range"] + 1.0).tick(COOLDOWN_TICKS * 2)
    assert fight.hits == []


def test_missing_player_target_does_no_damage():
    fight = EnemyFight()
    fight.enemy_api._player = None
    fight.tick(COOLDOWN_TICKS * 2)
    assert fight.health() == PLAYER["health"]


def test_repeated_enemy_hits_reduce_player_health_to_zero_and_trigger_death():
    fight = EnemyFight(player_health=25).tick(COOLDOWN_TICKS * 3)
    assert fight.health() == 0
    assert "trigger_death" in fight.player.executed_nodes


def test_enemy_damage_updates_hud_health_bar():
    fight = EnemyFight().tick()
    value, _max_val = fight.player_api.progress["HealthBar"]
    assert value == pytest.approx(fight.health() / PLAYER["max_health"])


def test_stop_play_reset_preserves_initial_health():
    for _ in range(2):
        fight = EnemyFight()
        assert fight.health() == PLAYER["health"]
        fight.tick(COOLDOWN_TICKS * 2)
        assert fight.health() < PLAYER["health"]
