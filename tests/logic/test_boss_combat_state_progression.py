"""The boss counts its attacks, reaches the heavy one, changes phase, and dies.

PHASE 9 recovery item 17.

Item 16A filed the boss debt as "animation/visual only". That was wrong, and
item 14E already said so: ``variable.increment`` is the node that writes
``attack_count``, so a phantom there stops state, not pixels. This item started
from that correction and measured the graph instead of the node list.

The counter was the fourth defect in line, not the first. Executing
``BossCombatLogic`` against a harness reached **two of its eighteen nodes**::

    frame_loop -> get_cooldown_timer -> (nothing)

The edge leaving ``get_cooldown_timer`` left its *data* port and arrived at a
flow port, and ``_follow`` only walks ``next``. Everything downstream --
the cooldown check, both branches, both triggers, the counter -- was
unreachable. ``BossHealthLogic`` was the same shape: ``check_dead`` had a data
edge carrying health into it and no flow edge reaching it, so the boss could
not die and its health bar never updated.

So four things were wrong at once, and each hid the next:

1. the flow chain stopped two nodes in, in both graphs;
2. ``cooldown_timer`` was authored as a countdown and compared as a count-up;
3. ``variable.increment`` and ``animator.set_trigger`` were phantom;
4. phase 2 compared ``health <= max_health``, true at full health.

These tests drive the shipping assets, not copies, and assert behaviour over
ticks rather than structure, so re-laying out either graph in the editor does
not break them.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
)
from engine.logic.node_definitions.catalogue import resolve_node_id
from engine.logic.runtime import LogicGraphRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Live values from Level2.zscene, so the harness runs the game's numbers.
BOSS_VARIABLES = {
    "health": 500,
    "max_health": 500,
    "move_speed": 80,
    "attack_damage": 20,
    "heavy_attack_damage": 35,
    "detection_range": 500,
    "attack_range": 72,
    "heavy_attack_range": 96,
    "attack_cooldown": 1.5,
    "phase": 1,
    "phase2_threshold": 0.5,
    "cooldown_timer": 1.5,
    "attack_count": 0,
    "heavy_attack_interval": 3,
}


def graph(name: str) -> dict:
    return normalize_logic_graph(load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{name}.zlogic"))


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


class _Animator:
    """Just enough AnimationController for animator_set_trigger to succeed."""

    def __init__(self) -> None:
        self.parameters: dict[str, object] = {}
        self.pulses: list[str] = []

    def set_parameter(self, name: str, value: object) -> None:
        self.parameters[str(name)] = value
        self.pulses.append(str(name))

    def get_parameter(self, name: str, default: object = None) -> object:
        return self.parameters.get(str(name), default)


class _Target:
    """A stand-in Player, close enough for item 18's range guard to pass."""

    def __init__(self, x: float = 40.0, y: float = 0.0) -> None:
        self.x = float(x)
        self.y = float(y)
        self.name = "Player"
        self.tag = "Player"
        self.rigidbody = None
        self.components: list = []

    def get_component(self, _component_type):
        return None

    def move(self, delta_x: float, delta_y: float = 0.0) -> None:
        self.x += float(delta_x)
        self.y += float(delta_y)


class _Boss:
    def __init__(self, *, animator: bool = True) -> None:
        self.x = 0.0
        self.y = 0.0
        self.tag = "Boss"
        self.name = "Boss"
        self.rigidbody = None
        self.components: list = []
        self.animator = _Animator() if animator else None
        # Item 18 put a range guard in front of the attack, so a boss with no
        # target no longer attacks. These tests are about the state machine,
        # not about targeting, so they keep a player within attack_range.
        self.player = _Target()

    def get_component(self, _component_type):
        return self.animator

    def move(self, delta_x: float, delta_y: float = 0.0) -> None:
        self.x += float(delta_x)
        self.y += float(delta_y)

    def find(self, name: str):
        return self.player if str(name).lower() == "player" else self

    find_object = find
    find_by_tag = find


class _Run:
    """Drives one graph for N ticks and records what happened."""

    def __init__(self, name: str, *, animator: bool = True, **overrides) -> None:
        self.runtime = LogicGraphRuntime(graph(name))
        self.boss = _Boss(animator=animator)
        for key, value in {**BOSS_VARIABLES, **overrides}.items():
            self.runtime.blackboard.set("object", key, value, self.runtime.object_key)
        self.attacks: list[str] = []

    def variable(self, name: str, scope: str = "object"):
        return self.runtime.blackboard.get(scope, name, self.runtime.object_key)

    def tick(self, count: int = 1, dt: float = 1.0 / 60.0) -> "_Run":
        for _ in range(count):
            self.runtime.executed_nodes.clear()
            self.runtime.update(self.boss, dt)
            executed = set(self.runtime.executed_nodes)
            if "set_heavy_attack" in executed:
                self.attacks.append("heavy")
            elif "set_normal_attack" in executed:
                self.attacks.append("normal")
        return self


def _executed(name: str, **overrides) -> set[str]:
    run = _Run(name, **overrides)
    run.tick()
    return set(run.runtime.executed_nodes)


# ---------------------------------------------------------------------------
# The flow reaches the graph at all
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,terminal", [
    ("BossCombatLogic", "check_can_attack"),
    ("BossHealthLogic", "check_dead"),
])
def test_the_frame_event_reaches_the_decision_node(name: str, terminal: str):
    """The defect that hid the other three: execution stopped two nodes in.

    Before this item ``BossCombatLogic`` executed ``frame_loop`` and
    ``get_cooldown_timer`` and nothing else, out of eighteen nodes.
    """
    assert terminal in _executed(name)


@pytest.mark.parametrize("name", ["BossCombatLogic", "BossHealthLogic", "BossAILogic"])
def test_every_edge_names_a_port_its_node_declares(name: str):
    g = graph(name)
    nodes = {str(n["id"]): n for n in g["nodes"]}
    orphans = []
    for edge in g["edges"]:
        source = nodes[str(edge["from_node"])]
        target = nodes[str(edge["to_node"])]
        if str(edge["from_port"]) not in {p for p, _ in node_port_definitions(source)["outputs"]}:
            orphans.append(f"{source['type']}.{edge['from_port']}>out")
        if str(edge["to_port"]) not in {p for p, _ in node_port_definitions(target)["inputs"]}:
            orphans.append(f"{target['type']}.{edge['to_port']}>in")
    assert sorted(set(orphans)) == []


def test_boss_combat_has_no_phantom_node_left():
    """The other two boss graphs keep named debt; this one is now clean."""
    g = graph("BossCombatLogic")
    phantom = {str(n["type"]) for n in g["nodes"]
               if resolve_node_id(str(n["type"])) not in NODE_DEFINITIONS}
    assert phantom == set()


# ---------------------------------------------------------------------------
# attack_count
# ---------------------------------------------------------------------------


def test_the_counter_starts_where_the_scene_puts_it():
    assert _Run("BossCombatLogic").variable("attack_count") == 0


def test_each_normal_attack_advances_the_counter():
    """One tick per attack, forced by seeding the timer at zero each time."""
    run = _Run("BossCombatLogic", cooldown_timer=0.0)
    seen = []
    for _ in range(2):
        run.tick()
        seen.append(run.variable("attack_count"))
        run.runtime.blackboard.set("object", "cooldown_timer", 0.0, run.runtime.object_key)
    assert seen == [1, 2]


def test_the_heavy_attack_resets_the_counter():
    run = _Run("BossCombatLogic", cooldown_timer=0.0, attack_count=2)
    run.tick()
    assert run.attacks == ["heavy"]
    assert run.variable("attack_count") == 0


def test_the_counter_never_runs_away():
    """Over a long run the count stays inside one interval."""
    run = _Run("BossCombatLogic", cooldown_timer=0.0).tick(1200)
    assert 0 <= run.variable("attack_count") < BOSS_VARIABLES["heavy_attack_interval"]


# ---------------------------------------------------------------------------
# The heavy attack
# ---------------------------------------------------------------------------


def test_the_heavy_attack_is_reachable_at_all():
    """The claim item 16A's classification made false."""
    assert "heavy" in _Run("BossCombatLogic", cooldown_timer=0.0).tick(1200).attacks


def test_the_heavy_attack_lands_on_every_third_attack():
    attacks = _Run("BossCombatLogic", cooldown_timer=0.0).tick(1200).attacks
    assert len(attacks) >= 9, f"too few attacks to judge the rhythm: {attacks}"
    expected = ["heavy" if (i + 1) % BOSS_VARIABLES["heavy_attack_interval"] == 0 else "normal"
                for i in range(len(attacks))]
    assert attacks == expected


def test_the_interval_comes_from_the_scene_and_not_from_a_literal():
    """Change the variable, and the rhythm changes with it."""
    attacks = _Run("BossCombatLogic", cooldown_timer=0.0, heavy_attack_interval=2).tick(800).attacks
    assert attacks[:4] == ["normal", "heavy", "normal", "heavy"]


# ---------------------------------------------------------------------------
# Cooldown
# ---------------------------------------------------------------------------


def test_the_boss_does_not_attack_every_frame():
    ticks = 600
    attacks = _Run("BossCombatLogic", cooldown_timer=0.0).tick(ticks).attacks
    assert 0 < len(attacks) < ticks / 10


def test_the_gap_between_attacks_matches_the_authored_cooldown():
    """``attack_cooldown`` seconds apart, give or take the frames it costs.

    The graph decrements by a hardcoded 0.016 per frame -- the authored value,
    kept as it was, since replacing it with real ``dt`` is a change to the
    cooldown's meaning and not part of this recovery. So the timer needs
    ``ceil(1.5 / 0.016)`` = 94 frames to reach zero, and the frame that fires
    the attack and rearms the timer is a 95th. Two frames of tolerance covers
    that arithmetic without letting a genuinely wrong cooldown through.
    """
    run = _Run("BossCombatLogic", cooldown_timer=0.0)
    stamps = []
    for tick in range(1200):
        before = len(run.attacks)
        run.tick()
        if len(run.attacks) > before:
            stamps.append(tick)
    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    assert gaps, "no second attack to measure a gap against"
    ideal = BOSS_VARIABLES["attack_cooldown"] / 0.016
    assert all(abs(gap - ideal) <= 2 for gap in gaps), gaps
    assert len(set(gaps)) == 1, f"the cooldown drifted: {gaps}"


def test_an_attack_reloads_the_timer_instead_of_zeroing_it():
    """The count-up/countdown mix-up, pinned: reset must arm, not disarm."""
    run = _Run("BossCombatLogic", cooldown_timer=0.0)
    run.tick()
    assert run.variable("cooldown_timer") == pytest.approx(BOSS_VARIABLES["attack_cooldown"])


def test_the_timer_never_falls_below_zero():
    run = _Run("BossCombatLogic", cooldown_timer=0.05).tick(600)
    assert run.variable("cooldown_timer") >= 0


# ---------------------------------------------------------------------------
# State before animation
# ---------------------------------------------------------------------------


def test_the_animator_receives_the_triggers_it_declares():
    """BossController has Attack and HeavyAttack states; both get pulsed."""
    run = _Run("BossCombatLogic", cooldown_timer=0.0).tick(1200)
    assert {"attack", "heavy_attack"} <= set(run.boss.animator.parameters)


def test_the_counter_still_advances_without_an_animator():
    """Item 17's decoupling, and the reason for it.

    ``animator_set_trigger`` returns ``exec_failure`` when the object has no
    AnimationController. With the trigger in the middle of the chain -- where
    the asset had it -- that failure would swallow the counter write and the
    cooldown reset. An object with no animator must still fight.
    """
    run = _Run("BossCombatLogic", cooldown_timer=0.0, animator=False).tick(1200)
    assert run.variable("attack_count") is not None
    assert "heavy" in run.attacks


# ---------------------------------------------------------------------------
# Phase 2
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("health,expected", [
    (500, 1),
    (251, 1),
    (250, 2),   # boundary: half of max_health, inclusive
    (100, 2),
])
def test_phase_two_starts_at_the_authored_threshold(health: int, expected: int):
    """Level2 declares ``phase2_threshold: 0.5`` and the graph ignored it.

    ``margin_phase`` subtracted ``max_health`` from ``health``, so the ``<= 0``
    test was true at full health and the boss entered phase 2 on its first
    tick. It now subtracts ``max_health * phase2_threshold``.
    """
    run = _Run("BossAILogic", health=health)
    run.boss.player = _Boss()
    run.boss.player.x, run.boss.player.tag = 200.0, "Player"
    run.boss.find = lambda name: run.boss.player if str(name).lower() == "player" else None
    run.boss.find_object = run.boss.find
    run.tick()
    assert run.variable("phase") == expected


# ---------------------------------------------------------------------------
# Death
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("health,dead", [(500, False), (1, False), (0, True), (-5, True)])
def test_death_is_reachable_and_inclusive_at_zero(health: int, dead: bool):
    run = _Run("BossHealthLogic", health=health)
    run.tick()
    assert ("set_boss_defeated" in run.runtime.executed_nodes) is dead


def test_death_publishes_the_project_flag_the_victory_scene_reads():
    run = _Run("BossHealthLogic", health=0)
    run.tick()
    assert run.variable("boss_defeated", scope="project") is True


def test_death_pulses_the_animator_without_gating_the_state_on_it():
    """The dead trigger is a leaf here too, for the same reason."""
    run = _Run("BossHealthLogic", health=0)
    run.tick()
    assert "dead" in run.boss.animator.parameters

    without = _Run("BossHealthLogic", health=0, animator=False)
    without.tick()
    assert without.variable("boss_defeated", scope="project") is True


def test_a_living_boss_is_left_alone():
    executed = _executed("BossHealthLogic", health=500)
    assert "set_boss_defeated" not in executed
    assert "set_dead_trigger" not in executed
