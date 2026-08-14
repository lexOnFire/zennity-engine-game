"""BossAILogic and EnemyAILogic chase on canonical nodes, and keep chasing.

PHASE 9 recovery item 14E. Item 14D.2 proved the scalar chain works in a
prototype; this is the same chain applied to the two shipping assets, and the
gate that keeps it applied.

What was wrong is worth stating precisely, because it is what these tests
watch for. Both graphs measured distance with ``math.distance`` and built a
direction with ``vector2`` / ``normalize_vector`` -- three node types the
engine does not have. They read positions through ``get_position.object`` and
``.position``, and compared through ``if_else.value`` / ``.compare_value``:
four more pins that do not exist. And no flow edge ever reached any of the
branches, so the whole chase was unreachable even before the phantom nodes
mattered.

The assertions here are structural and behavioural rather than positional --
no test indexes a node by ordinal or asserts on a uuid -- so re-laying out
either graph in the editor does not break them.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.node_definitions import NODE_DEFINITIONS
from engine.logic.node_definitions.catalogue import resolve_node_id
from engine.logic.runtime import LogicGraphRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]

ASSETS = {
    "boss": REPO_ROOT / "Assets" / "Logic" / "BossAILogic.zlogic",
    "enemy": REPO_ROOT / "Assets" / "Logic" / "EnemyAILogic.zlogic",
}

#: Live values from the scenes that instantiate these objects, so the harness
#: exercises the same thresholds the game does.
VARIABLES = {
    "boss": {
        "move_speed": 80,
        "detection_range": 500,
        "attack_range": 72,
        "phase": 1,
        "health": 500,
        "max_health": 500,
        # Item 17 wired the phase-2 gate to this scene variable instead of
        # comparing health against max_health, which was true at full health.
        "phase2_threshold": 0.5,
    },
    "enemy": {
        "move_speed": 100,
        "detection_range": 300,
        "attack_range": 48,
        "health": 100,
        "max_health": 100,
        "attack_cooldown": 1.0,
        "cooldown_timer": 1.0,
    },
}

#: The API item 14C declined. Their absence from these two assets is the point
#: of the item, so it is asserted rather than assumed.
REJECTED_TYPES = frozenset({"vector2", "normalize_vector", "math.distance"})

#: Animation stays debt (item 14E section 14). Listed so that a phantom which
#: is NOT one of these fails the test: this is a named debt, not a blanket
#: exemption.
#: Item 17 mapped animator.set_trigger onto the canonical animator_set_trigger,
#: so it left this set on both graphs -- a recovered id must leave the baseline.
#: variable.increment stays for the enemy: it is still NEVER_IMPLEMENTED, and
#: only the boss graph was reauthored off it.
ACCEPTED_PHANTOM_DEBT = {
    "boss": {"set_animator_parameter"},
    "enemy": {"set_animator_parameter", "variable.increment"},
}


def graph(name: str) -> dict:
    return normalize_logic_graph(load_logic_graph(ASSETS[name]))


def _types(g: dict) -> set[str]:
    return {str(node["type"]) for node in g["nodes"]}


def _by_id(g: dict) -> dict[str, dict]:
    return {str(node["id"]): node for node in g["nodes"]}


def _orphan_edges(g: dict) -> list[str]:
    """Edges naming a port the node's contract does not declare."""
    nodes = _by_id(g)
    orphans: list[str] = []
    for edge in g.get("edges", []):
        source = nodes.get(str(edge.get("from_node") or ""))
        target = nodes.get(str(edge.get("to_node") or ""))
        from_port = str(edge.get("from_port") or "")
        to_port = str(edge.get("to_port") or "")
        if source is not None and from_port:
            outputs = {n for n, _k in node_port_definitions(source)["outputs"]}
            if from_port not in outputs:
                orphans.append(f"{source.get('type')}.{from_port}>out")
        if target is not None and to_port:
            inputs = {n for n, _k in node_port_definitions(target)["inputs"]}
            if to_port not in inputs:
                orphans.append(f"{target.get('type')}.{to_port}>in")
    return sorted(set(orphans))


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


class _Object:
    def __init__(self, x: float, y: float, tag: str) -> None:
        self.x = float(x)
        self.y = float(y)
        self.tag = tag
        # Declared, not served by __getattr__: a catch-all makes ``rigidbody``
        # truthy and sends move_by down a physics branch these graphs do not
        # ask for. Neither object carries a RigidBody in any shipping scene.
        self.rigidbody = None
        self.components: list = []

    def move(self, delta_x: float, delta_y: float = 0.0) -> None:
        self.x += float(delta_x)
        self.y += float(delta_y)


class _Game(_Object):
    """The per-object API the viewport builds: it *is* the AI object."""

    def __init__(self, own: tuple[float, float], player: tuple[float, float], tag: str) -> None:
        super().__init__(own[0], own[1], tag)
        self.player = _Object(player[0], player[1], "Player")

    def find(self, tag: str):
        return self.player if str(tag).lower() == "player" else None


def _run(
    name: str,
    own: tuple[float, float],
    player: tuple[float, float],
    *,
    ticks: int = 1,
    dt: float = 1.0 / 60.0,
    overrides: dict | None = None,
) -> _Game:
    game = _Game(own, player, name.capitalize())
    runtime = LogicGraphRuntime(graph(name))
    variables = {**VARIABLES[name], **(overrides or {})}
    for key, value in variables.items():
        runtime.blackboard.set("object", key, value, runtime.object_key)
    for _ in range(ticks):
        runtime.update(game, dt)
    return game


def _chase_start(name: str) -> float:
    """A distance inside detection range and well outside attack range."""
    return (VARIABLES[name]["detection_range"] + VARIABLES[name]["attack_range"]) / 2.0


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_the_vector_api_is_gone(name: str):
    assert not _types(graph(name)) & REJECTED_TYPES


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_the_chase_uses_the_canonical_scalar_nodes(name: str):
    types = _types(graph(name))
    for required in ("find_tag", "get_position", "distance_to_point",
                     "subtract_number", "divide_number", "multiply_number",
                     "compare_number", "get_variable", "move_by"):
        assert required in types, f"{name} lost {required}"


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_no_orphan_edges_remain(name: str):
    assert _orphan_edges(graph(name)) == []


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_only_the_named_animation_debt_is_still_phantom(name: str):
    """A phantom outside the accepted set fails; so does a debt that vanished.

    The second half matters as much as the first: if animation gets fixed, this
    test must be updated deliberately rather than quietly keep passing.
    """
    g = graph(name)
    phantom = {t for t in _types(g) if resolve_node_id(t) not in NODE_DEFINITIONS}
    assert phantom == ACCEPTED_PHANTOM_DEBT[name]


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_positions_are_read_through_target_x_and_y(name: str):
    """``get_position`` takes ``target`` and yields ``x``/``y`` -- nothing else."""
    g = graph(name)
    nodes = _by_id(g)
    position_ids = {i for i, n in nodes.items() if n["type"] == "get_position"}
    assert position_ids, name

    for edge in g["edges"]:
        if str(edge.get("to_node")) in position_ids:
            assert str(edge.get("to_port")) == "target"
        if str(edge.get("from_node")) in position_ids:
            assert str(edge.get("from_port")) in {"x", "y"}


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_distance_to_point_receives_four_live_coordinates(name: str):
    """All four coordinates arrive on edges, so no default can leak in.

    Item 14D.1 made connected inputs win over properties; this asserts the
    asset actually connects them, which is the half that lives in the graph.
    """
    g = graph(name)
    distance_ids = {i for i, n in _by_id(g).items() if n["type"] == "distance_to_point"}
    assert len(distance_ids) == 1, name
    wired = {
        str(e["to_port"])
        for e in g["edges"]
        if str(e.get("to_node")) in distance_ids and str(e.get("to_port")) in {"x1", "y1", "x2", "y2"}
    }
    assert wired == {"x1", "y1", "x2", "y2"}


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_move_by_is_driven_through_x_and_y(name: str):
    """``velocity`` stays unused: item 14F owns its fate, not this item."""
    g = graph(name)
    move_ids = {i for i, n in _by_id(g).items() if n["type"] == "move_by"}
    assert move_ids, name
    ports = {
        str(e["to_port"])
        for e in g["edges"]
        if str(e.get("to_node")) in move_ids and str(e.get("kind")) != "flow"
    }
    assert "velocity" not in ports
    assert {"x", "y"} <= ports


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_speed_still_comes_from_the_blackboard(name: str):
    g = graph(name)
    names = {
        str(n["properties"].get("name"))
        for n in g["nodes"]
        if n["type"] == "get_variable"
    }
    assert "move_speed" in names
    assert "detection_range" in names
    assert "attack_range" in names


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_every_edge_names_a_declared_port(name: str):
    """The generic gate that would have caught the original defect.

    ``get_position.position`` and ``if_else.value`` were both edges into pins
    that never existed. Nothing checked that, so the graphs looked authored and
    silently did nothing.
    """
    g = graph(name)
    nodes = _by_id(g)
    for edge in g["edges"]:
        source = nodes[str(edge["from_node"])]
        target = nodes[str(edge["to_node"])]
        outputs = {n for n, _k in node_port_definitions(source)["outputs"]}
        inputs = {n for n, _k in node_port_definitions(target)["inputs"]}
        assert str(edge["from_port"]) in outputs, f"{source['type']}.{edge['from_port']}"
        assert str(edge["to_port"]) in inputs, f"{target['type']}.{edge['to_port']}"


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_save_and_reopen_is_stable(name: str, tmp_path):
    original = graph(name)
    destination = tmp_path / f"{name}.zlogic"
    save_logic_graph(destination, original)
    reloaded = normalize_logic_graph(load_logic_graph(destination))
    assert reloaded == original
    assert _orphan_edges(reloaded) == []


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_normalize_is_idempotent(name: str):
    once = graph(name)
    assert normalize_logic_graph(once) == once


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------

DIRECTIONS = {
    "east": (1.0, 0.0),
    "west": (-1.0, 0.0),
    "north": (0.0, 1.0),
    "south": (0.0, -1.0),
    "north_east": (0.7071067811865476, 0.7071067811865476),
    "north_west": (-0.7071067811865476, 0.7071067811865476),
    "south_east": (0.7071067811865476, -0.7071067811865476),
    "south_west": (-0.7071067811865476, -0.7071067811865476),
}


@pytest.mark.parametrize("name", sorted(ASSETS))
@pytest.mark.parametrize("direction", sorted(DIRECTIONS))
def test_the_ai_moves_towards_the_player(name: str, direction: str):
    reach = _chase_start(name)
    unit = DIRECTIONS[direction]
    player = (unit[0] * reach, unit[1] * reach)

    game = _run(name, (0.0, 0.0), player)

    step = math.hypot(game.x, game.y)
    assert step > 0.0, f"{name} did not move"
    cosine = (game.x * player[0] + game.y * player[1]) / (step * reach)
    assert cosine == pytest.approx(1.0), "moved, but not towards the player"

    after = math.hypot(player[0] - game.x, player[1] - game.y)
    assert after < reach


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_the_step_matches_the_authored_speed(name: str):
    game = _run(name, (0.0, 0.0), (_chase_start(name), 0.0))
    assert math.hypot(game.x, game.y) == pytest.approx(VARIABLES[name]["move_speed"] / 60.0)


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_an_undetected_player_is_ignored(name: str):
    outside = VARIABLES[name]["detection_range"] * 3.0
    game = _run(name, (0.0, 0.0), (outside, 0.0))
    assert (game.x, game.y) == (0.0, 0.0)


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_inside_attack_range_the_ai_stops(name: str):
    """The stop branch is only reachable because the chase is exclusive.

    These objects have no RigidBody, so ``move_by(0, 0)`` moves nothing and
    cancels nothing -- a stop wired in parallel with the chase would be a no-op
    and the AI would walk through the player.
    """
    inside = VARIABLES[name]["attack_range"] / 2.0
    game = _run(name, (0.0, 0.0), (inside, 0.0))
    assert (game.x, game.y) == (0.0, 0.0)


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_standing_on_the_player_is_safe(name: str):
    """``divide_number`` raises on a zero divisor; the guard must prevent it."""
    game = _run(name, (10.0, 10.0), (10.0, 10.0))
    assert (game.x, game.y) == (10.0, 10.0)
    assert math.isfinite(game.x) and math.isfinite(game.y)


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_zero_speed_does_not_move(name: str):
    game = _run(name, (0.0, 0.0), (_chase_start(name), 0.0), overrides={"move_speed": 0})
    assert (game.x, game.y) == (0.0, 0.0)


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_the_chase_converges_and_settles_in_attack_range(name: str):
    """Many frames, never retreating, ending inside the attack range.

    A single frame proves direction; only a loop proves the thresholds hand
    over to each other -- chase until in range, then stop and stay stopped.
    """
    start = _chase_start(name)
    attack_range = VARIABLES[name]["attack_range"]
    game = _Game((0.0, 0.0), (start, 0.0), name.capitalize())
    runtime = LogicGraphRuntime(graph(name))
    for key, value in VARIABLES[name].items():
        runtime.blackboard.set("object", key, value, runtime.object_key)

    previous = start
    for _ in range(600):
        runtime.update(game, 1.0 / 60.0)
        distance = math.hypot(start - game.x, -game.y)
        assert distance <= previous + 1e-9, f"{name} retreated"
        previous = distance

    assert previous <= attack_range
    assert previous > attack_range - VARIABLES[name]["move_speed"] / 60.0 - 1e-9


@pytest.mark.parametrize("name", sorted(ASSETS))
def test_the_graph_builds_a_runtime_without_error(name: str):
    assert LogicGraphRuntime(graph(name)) is not None


def test_the_boss_phase_branch_still_exists():
    """Re-authoring the movement must not have eaten the phase logic."""
    g = graph("boss")
    nodes = _by_id(g)
    assert nodes["set_phase2"]["type"] == "set_variable"
    assert nodes["set_phase2"]["properties"]["name"] == "phase"
    assert nodes["check_phase2"]["type"] == "compare_number"
    reached = {str(e["to_node"]) for e in g["edges"] if str(e.get("from_node")) == "check_phase2"}
    assert "set_phase2" in reached


def test_the_enemy_attack_branch_still_exists():
    g = graph("enemy")
    nodes = _by_id(g)
    assert "set_attack_trigger" in nodes
    assert nodes["reset_cooldown_timer"]["type"] == "set_variable"
    reached = {str(e["to_node"]) for e in g["edges"] if str(e.get("from_node")) == "check_can_attack"}
    assert "set_attack_trigger" in reached


def test_the_enemy_idle_animation_edge_survives():
    """Animation is untouched debt, so its wiring must still be there."""
    g = graph("enemy")
    edges = {(str(e["from_node"]), str(e["from_port"]), str(e["to_node"])) for e in g["edges"]}
    assert ("check_detected", "false", "idle_state") in edges
    assert ("check_detected", "true", "set_speed_parameter") in edges
