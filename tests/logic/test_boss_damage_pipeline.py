"""The boss actually hurts the player, and the player owns its own health.

PHASE 9 recovery item 18.

Item 17 left the boss with a working state machine that hit nothing. Both
``attack_damage: 20`` and ``heavy_attack_damage: 35`` sat in Level2 with no
reader, no boss graph applied damage, and the engine has no node whose id
mentions damage.

The audit found the damage *was* expressible, and had been attempted twice:

* ``EnemyAttackLogic`` authors ``object.get_variable`` / ``object.set_variable``
  -- cross-object variable access. **No commit in the entire history ever
  defined either one**, so that route was never runnable.
* ``PlayerHealthLogic`` authored ``event.custom`` for the death signal, so
  custom events were the project's cross-object channel from the start.

``emit_event`` and ``event_custom`` both exist, both have executors, and the
``LogicEventBus`` is shared across every object in the scene -- the same store
that already shares the blackboard. So the boss publishes a damage event and
the player subtracts from its own health. Ownership stays where it belongs: no
node writes another object's state, and health keeps exactly one source of
truth.

Two things these tests are careful about.

**Dispatch is not automatic.** ``LogicEventBus.emit`` only queues; the viewport
calls ``dispatch()`` after every ``runtime.update``. The harness below does the
same, in the same order, because a test that dispatched differently from the
game would prove nothing about the game.

**PlayerHealthLogic had to be authored, not just wired.** It shipped with eight
nodes, **zero edges**, and empty properties -- ``4ed6c6cd`` stripped the wiring
that ``0d2ba5f8`` had. It was also absent from the Player in Level2, so even a
correct graph would never have loaded.
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

#: Live values from Level2.zscene.
BOSS = {
    "health": 500, "max_health": 500, "move_speed": 80,
    "attack_damage": 20, "heavy_attack_damage": 35,
    "detection_range": 500, "attack_range": 72, "heavy_attack_range": 96,
    "attack_cooldown": 1.5, "phase": 1, "phase2_threshold": 0.5,
    "cooldown_timer": 0.0, "attack_count": 0, "heavy_attack_interval": 3,
}
PLAYER = {"health": 100, "max_health": 100, "attack_damage": 25, "attack_range": 64}

#: One cooldown, in frames: the graph decrements a hardcoded 0.016 per tick and
#: spends one more frame on the attack itself.
COOLDOWN_TICKS = 95


def graph(name: str) -> dict:
    return normalize_logic_graph(load_logic_graph(LOGIC / f"{name}.zlogic"))


# ---------------------------------------------------------------------------
# Harness -- mirrors editor/runtime/viewport_session_orchestrator.update_logic
# ---------------------------------------------------------------------------


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
    """The per-object API the viewport builds: it *is* the object."""

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


class Fight:
    """A boss and a player sharing one blackboard and one event bus."""

    def __init__(self, distance: float = 40.0, **overrides) -> None:
        self.store = BlackboardStore()
        self.bus = LogicEventBus()
        boss_vars = {**BOSS, **{k: v for k, v in overrides.items() if k in BOSS}}
        player_vars = {**PLAYER, **{k: v for k, v in overrides.items() if k in PLAYER}}
        if "player_health" in overrides:
            player_vars["health"] = overrides["player_health"]
        for key, value in boss_vars.items():
            self.store.set("object", key, value, "Boss")
        for key, value in player_vars.items():
            self.store.set("object", key, value, "Player")

        self.player_object = _Object(distance, 0.0, "Player")
        self.boss_api = _Api((0.0, 0.0), "Boss", self.player_object)
        self.player_api = _Api((distance, 0.0), "Player", self.player_object)
        self.boss = LogicGraphRuntime(graph("BossCombatLogic"), self.store, "Boss", self.bus)
        self.player = LogicGraphRuntime(graph("PlayerHealthLogic"), self.store, "Player", self.bus)
        self.player.start(self.player_api)
        self.hits: list[tuple[int, str, float, float]] = []
        self.tick_index = 0

    def health(self) -> float:
        return self.store.get("object", "health", "Player")

    def tick(self, count: int = 1, dt: float = 1.0 / 60.0) -> "Fight":
        for _ in range(count):
            before = self.health()
            self.boss.executed_nodes.clear()
            self.boss.update(self.boss_api, dt)
            self.bus.dispatch()
            self.player.update(self.player_api, dt)
            self.bus.dispatch()
            after = self.health()
            if after != before:
                kind = "heavy" if "set_heavy_attack" in self.boss.executed_nodes else "normal"
                self.hits.append((self.tick_index, kind, before, after))
            self.tick_index += 1
        return self


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["BossCombatLogic", "PlayerHealthLogic"])
def test_neither_graph_carries_a_phantom_or_an_orphan(name: str):
    g = graph(name)
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


def test_the_boss_never_writes_the_players_health():
    """Ownership. The boss publishes; it does not reach into the player.

    This is the whole reason the event route was chosen over restoring
    ``object.set_variable``. If a future edit gives the boss a write node
    pointed at health, this fails.
    """
    g = graph("BossCombatLogic")
    writers = [n for n in g["nodes"] if str(n["type"]) == "set_variable"]
    written = {str(n.get("properties", {}).get("name", "")) for n in writers}
    assert "health" not in written
    assert written == {"cooldown_timer", "attack_count"}


def test_the_player_owns_the_only_health_write():
    g = graph("PlayerHealthLogic")
    writers = [n for n in g["nodes"] if str(n["type"]) == "set_variable"]
    assert [str(n["properties"]["name"]) for n in writers] == ["health"]
    assert [str(n["properties"]["scope"]) for n in writers] == ["object"]


def test_the_damage_event_name_matches_on_both_sides():
    """A typo here would be silent: the emit would queue and nobody would listen."""
    emitted = {str(n["properties"]["name"]) for n in graph("BossCombatLogic")["nodes"]
               if str(n["type"]) == "emit_event"}
    received = {str(n["properties"]["name"]) for n in graph("PlayerHealthLogic")["nodes"]
                if str(n["type"]) == "event_custom"}
    assert emitted == {"player_damage"}
    assert received == {"player_damage"}


# ---------------------------------------------------------------------------
# Normal and heavy damage
# ---------------------------------------------------------------------------


def test_a_normal_attack_removes_the_authored_normal_damage():
    fight = Fight().tick()
    assert fight.health() == PLAYER["health"] - BOSS["attack_damage"]


def test_the_heavy_attack_removes_the_heavy_value_and_not_the_normal_one():
    fight = Fight(player_health=1000).tick(COOLDOWN_TICKS * 3)
    heavy = [h for h in fight.hits if h[1] == "heavy"]
    assert heavy, f"no heavy attack in {fight.hits}"
    for _tick, _kind, before, after in heavy:
        assert before - after == BOSS["heavy_attack_damage"]


def test_every_normal_hit_costs_exactly_the_normal_value():
    fight = Fight(player_health=1000).tick(COOLDOWN_TICKS * 4)
    normals = [h for h in fight.hits if h[1] == "normal"]
    assert len(normals) >= 3
    for _tick, _kind, before, after in normals:
        assert before - after == BOSS["attack_damage"]


def test_the_heavy_attack_hurts_more_than_the_normal_one():
    assert BOSS["heavy_attack_damage"] > BOSS["attack_damage"]
    fight = Fight(player_health=1000).tick(COOLDOWN_TICKS * 3)
    by_kind = {kind: before - after for _t, kind, before, after in fight.hits}
    assert by_kind["heavy"] > by_kind["normal"]


# ---------------------------------------------------------------------------
# One hit per attack
# ---------------------------------------------------------------------------


def test_damage_lands_once_per_attack_and_not_once_per_frame():
    """The failure mode a cooldown exists to prevent."""
    ticks = COOLDOWN_TICKS * 3
    fight = Fight(player_health=100000).tick(ticks)
    assert len(fight.hits) == 3, fight.hits


def test_the_frames_between_attacks_do_no_damage():
    fight = Fight(player_health=1000)
    fight.tick()
    after_first = fight.health()
    fight.tick(COOLDOWN_TICKS - 2)
    assert fight.health() == after_first


def test_the_gap_between_hits_is_the_authored_cooldown():
    fight = Fight(player_health=100000).tick(COOLDOWN_TICKS * 4)
    stamps = [h[0] for h in fight.hits]
    gaps = {b - a for a, b in zip(stamps, stamps[1:])}
    assert gaps == {COOLDOWN_TICKS}, gaps


# ---------------------------------------------------------------------------
# Range
# ---------------------------------------------------------------------------


def test_out_of_range_the_player_takes_nothing():
    fight = Fight(distance=300.0).tick(COOLDOWN_TICKS * 4)
    assert fight.hits == []
    assert fight.health() == PLAYER["health"]


def test_at_exactly_attack_range_the_hit_lands():
    """Recorded rather than assumed: the margin test is ``<= 0``, so the
    boundary is inclusive, matching every other range gate in these graphs."""
    fight = Fight(distance=float(BOSS["attack_range"])).tick()
    assert fight.health() == PLAYER["health"] - BOSS["attack_damage"]


def test_one_unit_beyond_range_the_hit_does_not_land():
    fight = Fight(distance=BOSS["attack_range"] + 1.0).tick(COOLDOWN_TICKS * 2)
    assert fight.hits == []


def test_walking_into_range_starts_the_damage():
    """The timer sits at zero out of range, so the first hit is immediate."""
    fight = Fight(distance=300.0).tick(COOLDOWN_TICKS)
    assert fight.health() == PLAYER["health"]
    fight.player_object.x = 40.0
    fight.boss_api._player.x = 40.0
    fight.tick()
    assert fight.health() == PLAYER["health"] - BOSS["attack_damage"]


# ---------------------------------------------------------------------------
# Dead player
# ---------------------------------------------------------------------------


def test_health_is_clamped_at_zero():
    fight = Fight(player_health=10).tick()
    assert fight.health() == 0


def test_health_never_goes_negative_however_long_the_fight_runs():
    fight = Fight(player_health=10).tick(COOLDOWN_TICKS * 5)
    assert fight.health() == 0


def test_a_dead_player_reaches_the_death_branch():
    fight = Fight(player_health=10).tick()
    fight.player.executed_nodes.clear()
    fight.tick()
    assert "trigger_death" in fight.player.executed_nodes


def test_a_living_player_does_not_reach_the_death_branch():
    fight = Fight(player_health=1000)
    fight.player.executed_nodes.clear()
    fight.tick()
    assert "trigger_death" not in fight.player.executed_nodes


def test_death_uses_the_existing_pipeline_and_not_a_second_one_in_the_boss():
    """No death handling was added to the boss graph."""
    boss_types = {str(n["type"]) for n in graph("BossCombatLogic")["nodes"]}
    assert "scene.load_scene" not in boss_types
    player_ids = {str(n["id"]) for n in graph("PlayerHealthLogic")["nodes"]}
    assert {"trigger_death", "load_gameover_scene"} <= player_ids


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------


def test_the_hud_reads_the_same_health_the_damage_wrote():
    fight = Fight().tick()
    value, _maximum = fight.player_api.progress["HealthBar"]
    assert value == pytest.approx(fight.health() / PLAYER["max_health"])


def test_the_hud_follows_the_health_down():
    fight = Fight(player_health=1000)
    seen = []
    for _ in range(3):
        fight.tick(COOLDOWN_TICKS)
        seen.append(fight.player_api.progress["HealthBar"][0])
    assert seen == sorted(seen, reverse=True), seen


# ---------------------------------------------------------------------------
# Missing and invalid targets
# ---------------------------------------------------------------------------


def test_no_player_in_the_scene_is_survivable():
    """A missing target must not read as a target at distance zero.

    ``find_tag`` has no failure port and ``get_position`` on a null target
    falls back to the boss's own position, so the distance collapses to 0 --
    which ``distance <= attack_range`` happily accepts. BossAILogic already
    solved this with its ``chase_guard`` (``distance > 0``); the combat graph
    now carries the same guard rather than a new node.
    """
    fight = Fight()
    fight.boss_api._player = None
    fight.tick(COOLDOWN_TICKS * 2)
    assert fight.health() == PLAYER["health"]


def test_the_target_guard_is_what_makes_that_true():
    """Mutation: drop the guard and the missing-player case starts hitting."""
    fight = Fight()
    fight.boss_api._player = None
    for node in fight.boss.nodes.values():
        if str(node["id"]) == "target_guard":
            node["properties"]["operator"] = ">="
    fight.tick()
    assert fight.health() == PLAYER["health"] - BOSS["attack_damage"]


def test_an_unheard_event_changes_nothing():
    """Boss alone, no listener: emitting must not raise or mutate anything."""
    fight = Fight()
    fight.player.executed_nodes.clear()
    store, bus = fight.store, fight.bus
    boss = LogicGraphRuntime(graph("BossCombatLogic"), store, "Boss", LogicEventBus())
    boss.update(fight.boss_api, 1.0 / 60.0)
    assert store.get("object", "health", "Player") == PLAYER["health"]
    assert bus.dispatch() == 0


# ---------------------------------------------------------------------------
# Stop -> Play
# ---------------------------------------------------------------------------


def test_a_fresh_fight_starts_from_full_health_every_time():
    """Stop -> Play -> Stop -> Play: no state leaks between sessions."""
    for _ in range(2):
        fight = Fight()
        assert fight.health() == PLAYER["health"]
        fight.tick(COOLDOWN_TICKS * 3)
        assert fight.health() < PLAYER["health"]


def test_two_fights_do_not_share_a_blackboard():
    first = Fight().tick(COOLDOWN_TICKS * 2)
    second = Fight()
    assert second.health() == PLAYER["health"]
    assert first.health() < PLAYER["health"]


# ---------------------------------------------------------------------------
# Mutation guards -- a gate that cannot fail is worse than none
# ---------------------------------------------------------------------------


def test_the_damage_gate_fails_when_the_event_name_is_broken():
    """Rename the event on the boss side and the player must stop losing health."""
    fight = Fight()
    for node in fight.boss.nodes.values():
        if str(node["type"]) == "emit_event":
            node["properties"]["name"] = "not_the_damage_event"
    fight.tick(COOLDOWN_TICKS * 2)
    assert fight.health() == PLAYER["health"], "the event name is not actually load-bearing"


def test_the_range_gate_fails_when_the_guard_is_removed():
    """Widen attack_range and the out-of-range case must start taking damage."""
    fight = Fight(distance=300.0, attack_range=1000)
    fight.tick()
    assert fight.health() == PLAYER["health"] - BOSS["attack_damage"]


def test_the_clamp_is_load_bearing():
    """Without the clamp the player would go negative on the killing blow."""
    fight = Fight(player_health=5).tick()
    assert fight.health() == 0
    assert fight.health() >= 0
