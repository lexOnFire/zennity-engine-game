"""The numeric ``logic.branch`` comparisons run on canonical nodes now.

PHASE 9 recovery item 16B. Item 16A's RC-01 recorded 8 orphan edges feeding
``if_else.value`` / ``if_else.compare_value`` -- pins ``if_else`` does not
declare. This item resolved the 5 that are genuinely *numeric* comparisons, in
``BossCombatLogic`` and ``BossHealthLogic``, using the transformation proven in
item 14D.2 and applied in 14E: ``compare_number``, preceded by a
``subtract_number`` only when both operands arrive on wires.

The other 3 were deliberately **not** touched, and the tests at the bottom of
this file assert they are still there so the debt cannot be forgotten:

* ``CoinCollectionLogic`` and ``KeyCollectionLogic`` compare an *object's tag*
  against the text "Player". ``compare_number`` calls ``float()`` on its input
  and would raise. A canonical path exists (``get_tag`` -> ``compare_text``) but
  it is a different transformation than this item authorized.
* ``EnemyAttackLogic`` feeds the branch from ``physics.raycast_2d.hit``, and
  ``physics.raycast_2d`` has no definition at all. Repairing the branch would
  leave the edge orphaned on its source side regardless -- it belongs to item
  16A's RC-03, which needs design.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.runtime import LogicGraphRuntime
from engine.logic.runtime.registry import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
REAUTHORED = ("BossCombatLogic", "BossHealthLogic")
#: Still carrying a legacy comparison, each for a reason recorded above.
HELD_BACK = {
    "CoinCollectionLogic": "check_player",
    "KeyCollectionLogic": "check_player",
    "EnemyAttackLogic": "check_hit_player",
}


def graph(name: str) -> dict:
    return normalize_logic_graph(load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{name}.zlogic"))


def _legacy_if_else_edges(g: dict) -> list[tuple[str, str]]:
    types = {str(n["id"]): str(n["type"]) for n in g["nodes"]}
    return [
        (str(e["to_node"]), str(e["to_port"]))
        for e in g["edges"]
        if types.get(str(e.get("to_node"))) == "if_else"
        and str(e.get("to_port")) in ("value", "compare_value")
    ]


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


def _branch(asset: str, node_id: str, variables: dict) -> str:
    """Which flow port the comparison fires, driven from the real asset."""
    g = graph(asset)
    runtime = LogicGraphRuntime(g)
    for key, value in variables.items():
        runtime.blackboard.set("object", key, value, runtime.object_key)
    node = next(n for n in g["nodes"] if str(n["id"]) == node_id)
    return registry.executors["compare_number"](runtime, node, object(), 1.0 / 60.0)[0]


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("asset", REAUTHORED)
def test_no_legacy_comparison_pin_remains(asset: str):
    assert _legacy_if_else_edges(graph(asset)) == []


@pytest.mark.parametrize("asset", REAUTHORED)
def test_the_comparisons_are_compare_number_now(asset: str):
    types = {str(n["type"]) for n in graph(asset)["nodes"]}
    assert "compare_number" in types


@pytest.mark.parametrize("asset", REAUTHORED)
def test_no_orphan_edge_touches_a_comparison(asset: str):
    """Other debt may remain in these files; none of it may be a comparison."""
    for orphan in _orphans(graph(asset)):
        assert not orphan.startswith("if_else."), orphan
        assert not orphan.startswith("compare_number."), orphan


def test_boss_combat_has_no_orphan_edge_left_at_all():
    """This asset's entire orphan debt was RC-01, so it should now be clean."""
    assert _orphans(graph("BossCombatLogic")) == []


def test_boss_health_has_no_orphan_edge_left_either():
    """Inverted by item 16C, which paid the debt this recorded.

    Item 16B left BossHealthLogic with only its unrelated math.divide /
    ui.set_progress_bar orphans, and asserted exactly that. Item 16C added both
    to the legacy migration map -- one line each -- so the asset now has none.
    """
    assert _orphans(graph("BossHealthLogic")) == []


@pytest.mark.parametrize("asset", REAUTHORED)
def test_normalize_is_idempotent_and_survives_save_reopen(asset: str, tmp_path):
    once = graph(asset)
    assert normalize_logic_graph(once) == once

    destination = tmp_path / f"{asset}.zlogic"
    save_logic_graph(destination, once)
    reloaded = normalize_logic_graph(load_logic_graph(destination))
    assert reloaded == once
    assert _legacy_if_else_edges(reloaded) == [], "reopening reintroduced a legacy pin"


@pytest.mark.parametrize("asset", REAUTHORED)
def test_the_graph_still_builds_a_runtime(asset: str):
    assert LogicGraphRuntime(graph(asset)) is not None


def test_the_boss_combat_branches_still_fan_out_the_same_way():
    """Reauthoring a comparison must not rewire the branches around it."""
    g = graph("BossCombatLogic")
    edges = {(str(e["from_node"]), str(e["from_port"]), str(e["to_node"])) for e in g["edges"]}
    assert ("check_can_attack", "true", "get_phase") in edges
    assert ("check_can_attack", "true", "get_attack_count") in edges
    assert ("check_can_attack", "false", "decrease_timer") in edges


def test_the_attack_state_is_written_before_the_animation_is_asked_for():
    """Item 17. Both branches update state first and trigger the animator last.

    ``animator_set_trigger`` returns ``exec_failure`` when the object has no
    AnimationController, and a failed flow port continues nothing. With the
    trigger in the middle of the chain -- where the asset had it -- an object
    without an animator would stop counting attacks and stop resetting its
    cooldown. So the counter write and the timer reset happen upstream of it,
    and the trigger is a leaf: gameplay cannot depend on animation succeeding.
    """
    g = graph("BossCombatLogic")
    edges = {(str(e["from_node"]), str(e["from_port"]), str(e["to_node"])) for e in g["edges"]}
    assert ("check_heavy", "true", "reset_count") in edges
    assert ("reset_count", "next", "set_heavy_attack") in edges
    assert ("check_heavy", "false", "increment_count") in edges
    assert ("increment_count", "next", "set_normal_attack") in edges

    sources = {str(e["from_node"]) for e in g["edges"]}
    for trigger in ("set_heavy_attack", "set_normal_attack"):
        assert trigger not in sources, f"{trigger} must stay a leaf"


def test_the_boss_health_death_chain_was_preserved():
    g = graph("BossHealthLogic")
    edges = {(str(e["from_node"]), str(e["from_port"]), str(e["to_node"])) for e in g["edges"]}
    assert ("check_dead", "true", "set_dead_trigger") in edges


# ---------------------------------------------------------------------------
# Behaviour, driven from the real assets
# ---------------------------------------------------------------------------

BOSS = {"cooldown_timer": 2.0, "attack_cooldown": 1.5, "phase": 2,
        "attack_count": 3, "health": 10, "max_health": 500,
        # Item 17 wired the heavy-attack threshold to the scene variable.
        "heavy_attack_interval": 3}


@pytest.mark.parametrize("timer,expected", [
    (0.0, "true"),      # boundary: <= is inclusive, and 0 means ready
    (-0.1, "true"),
    (0.0001, "false"),
    (1.5, "false"),
])
def test_can_attack_reads_the_cooldown_as_a_countdown(timer: float, expected: str):
    """``cooldown_timer <= 0``, the reading item 17 settled on.

    The asset held both readings at once: it compared ``cooldown_timer -
    attack_cooldown >= 0`` (count up) while decrementing the timer every frame
    and resetting it to 0 after an attack (count down). Under the count-up
    reading the boss attacked once and never again, because the timer only ever
    moved away from the threshold. Level2 seeds ``cooldown_timer`` at 1.5, the
    same value as ``attack_cooldown``, which is what a countdown looks like at
    rest -- so countdown is what the scene authored, and the graph now matches:
    the timer falls to zero, the attack fires, and the reset puts it back at
    ``attack_cooldown`` rather than at 0.
    """
    assert _branch("BossCombatLogic", "check_can_attack",
                   dict(BOSS, cooldown_timer=timer)) == expected


@pytest.mark.parametrize("phase,expected", [(2, "true"), (1, "false"), (3, "false")])
def test_phase_two_compares_against_a_literal(phase: int, expected: str):
    """``phase == 2``: the literal stays a property, so no subtraction is needed."""
    assert _branch("BossCombatLogic", "check_phase2", dict(BOSS, phase=phase)) == expected


@pytest.mark.parametrize("count,expected", [(0, "false"), (1, "false"), (2, "true"), (3, "true")])
def test_heavy_attack_compares_against_the_authored_interval(count: int, expected: str):
    """``attack_count + 1 >= heavy_attack_interval``, both operands wired.

    Two changes from the literal ``== 3`` the asset carried. The threshold is
    now the scene's ``heavy_attack_interval``, which was declared and ignored;
    since ``compare_number`` takes its right operand from a property, a wired
    threshold needs the margin trick -- subtract, then compare the remainder
    against zero. And the comparison is on the *incremented* count, because the
    attack about to happen is the one being numbered: with the stored count,
    an interval of 3 fired the heavy attack on the fourth attack, not the third.
    ``>=`` rather than ``==`` so a count that somehow overshoots still fires
    instead of locking the heavy attack out forever.
    """
    assert _branch("BossCombatLogic", "check_heavy", dict(BOSS, attack_count=count)) == expected


@pytest.mark.parametrize("health,expected", [
    (10, "false"),
    (1, "false"),
    (0, "true"),      # boundary: <= is inclusive, and 0 hp means dead
    (-5, "true"),
])
def test_death_check_is_inclusive_at_zero(health: int, expected: str):
    assert _branch("BossHealthLogic", "check_dead", dict(BOSS, health=health)) == expected


# ---------------------------------------------------------------------------
# The three deliberately held back
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("asset,node_id", sorted(HELD_BACK.items()))
def test_the_held_back_comparisons_are_still_recorded(asset: str, node_id: str):
    """Debt, not exemption. If one is fixed, this fails and must be updated.

    Keeping them asserted is what stops "we did the if_else item" from reading
    as "there are no legacy comparisons left".
    """
    legacy = _legacy_if_else_edges(graph(asset))
    assert legacy, f"{asset} no longer has a legacy comparison -- update this item's record"
    assert all(target == node_id for target, _port in legacy), legacy


def test_the_tag_comparisons_are_not_numeric():
    """Why Coin and Key were not transformed: their operand is not a number.

    ``event_trigger_enter.other`` is an object and the authored comparison is
    against the text "Player". ``compare_number`` floats its input, so the
    authorized transformation does not apply. ``get_tag`` -> ``compare_text``
    is the canonical path, and it is a different change.
    """
    for asset in ("CoinCollectionLogic", "KeyCollectionLogic"):
        g = graph(asset)
        node = next(n for n in g["nodes"] if str(n["id"]) == "check_player")
        assert isinstance(node["properties"].get("compare_value"), str)
        source = next(
            str(e["from_port"]) for e in g["edges"]
            if str(e["to_node"]) == "check_player" and str(e["to_port"]) == "value"
        )
        assert source == "other", "the operand is the colliding object, not a number"

    from engine.logic.graph_asset import NODE_DEFINITIONS

    assert "get_tag" in NODE_DEFINITIONS and "compare_text" in NODE_DEFINITIONS


def test_the_enemy_attack_comparison_is_blocked_by_a_phantom_source():
    """Why EnemyAttack was not transformed: the source node does not exist.

    Fixing the branch would leave the edge orphaned on its *source* side, so the
    orphan count would not move. It belongs to item 16A's RC-03.
    """
    from engine.logic.graph_asset import NODE_DEFINITIONS

    g = graph("EnemyAttackLogic")
    types = {str(n["id"]): str(n["type"]) for n in g["nodes"]}
    source = next(
        str(e["from_node"]) for e in g["edges"]
        if str(e["to_node"]) == "check_hit_player" and str(e["to_port"]) == "value"
    )
    assert types[source] == "physics.raycast_2d"
    assert "physics.raycast_2d" not in NODE_DEFINITIONS


def test_exactly_three_legacy_comparisons_remain_repository_wide():
    """8 at item 16A, minus the 5 numeric ones resolved here."""
    total = 0
    for path in sorted((REPO_ROOT / "Assets").rglob("*.zlogic")):
        total += len(_legacy_if_else_edges(normalize_logic_graph(load_logic_graph(path))))
    assert total == 3
