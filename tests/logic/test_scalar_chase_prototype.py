"""A full 2D chase, authored with nothing but nodes that already exist.

PHASE 9 recovery item 14D.2. Item 14C refused to adopt a new vector API and
item 14D chose scalar re-authoring instead; the plan could not be proven
because ``distance_to_point`` ignored its declared inputs, which item 14D.1
fixed. What was still missing was evidence that the *whole* chain closes --
that the engine as it stands can find the player, measure the gap, normalize a
direction and move along it, with no ``vector2``, no ``normalize_vector`` and
no ``math.distance``.

Everything here is built in memory and, where a file is needed, in ``tmp_path``.
No shipping asset is read for mutation and none is written: ``BossAILogic`` and
``EnemyAILogic`` are item 14E's job, and this suite is the gate that authorizes
it.

The chain, in scalar form::

    dx = player.x - self.x
    dy = player.y - self.y
    distance = distance_to_point(self.x, self.y, player.x, player.y)
    if distance > 0:                      # also the division guard
        move_by.x = (dx / distance) * move_speed
        move_by.y = (dy / distance) * move_speed
"""

from __future__ import annotations

import copy
import math

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

# ---------------------------------------------------------------------------
# The prototype
# ---------------------------------------------------------------------------

#: Node types the chase is allowed to use. Listing them is the point: if the
#: chain ever needs a type outside this set, that is a new API, which is
#: exactly what item 14C declined.
ALLOWED_TYPES = frozenset(
    {
        "event_update",
        "find_tag",
        "get_position",
        "subtract_number",
        "distance_to_point",
        "compare_number",
        "divide_number",
        "get_variable",
        "multiply_number",
        "move_by",
    }
)

#: The API item 14C refused. Named so the refusal is enforced, not remembered.
REJECTED_VECTOR_TYPES = frozenset({"vector2", "normalize_vector", "math.distance"})


def _node(node_id: str, node_type: str, **properties) -> dict:
    return {
        "id": node_id,
        "type": node_type,
        "position": [0.0, 0.0],
        "properties": dict(properties),
    }


def _edge(from_node: str, from_port: str, to_node: str, to_port: str) -> dict:
    return {
        "from_node": from_node,
        "from_port": from_port,
        "to_node": to_node,
        "to_port": to_port,
    }


def chase_graph() -> dict:
    """The scalar chase, authored against the current palette.

    ``n_spos`` deliberately has no ``target`` edge: that is how a node addresses
    the object its graph is attached to. ``_read_target`` falls back to
    ``_implicit_target or game``, and the host passes a per-object API as
    ``game`` -- so "self" is a mechanism that already exists, not one invented
    here.
    """
    return {
        "format": "zennity.logic_graph",
        "version": 1,
        "name": "ScalarChasePrototype",
        "target": {"type": "name", "value": "Enemy"},
        "variables": {"move_speed": 200.0},
        "nodes": [
            _node("n_event", "event_update"),
            _node("n_player", "find_tag", tag="Player"),
            _node("n_ppos", "get_position"),
            _node("n_spos", "get_position"),
            _node("n_dx", "subtract_number"),
            _node("n_dy", "subtract_number"),
            _node("n_dist", "distance_to_point"),
            _node("n_gate", "compare_number", operator=">", value=0.0),
            _node("n_nx", "divide_number"),
            _node("n_ny", "divide_number"),
            _node("n_speed", "get_variable", scope="object", name="move_speed"),
            _node("n_vx", "multiply_number"),
            _node("n_vy", "multiply_number"),
            _node("n_move", "move_by"),
        ],
        "edges": [
            # Flow. It reaches move_by only through the distance > 0 branch.
            _edge("n_event", "next", "n_player", "in"),
            _edge("n_player", "next", "n_dist", "exec"),
            _edge("n_dist", "exec_calculated", "n_gate", "in"),
            _edge("n_gate", "true", "n_speed", "in"),
            _edge("n_speed", "next", "n_move", "in"),
            # Player position (self position needs no edge -- see the docstring).
            _edge("n_player", "object", "n_ppos", "target"),
            # Distance between the two points.
            _edge("n_spos", "x", "n_dist", "x1"),
            _edge("n_spos", "y", "n_dist", "y1"),
            _edge("n_ppos", "x", "n_dist", "x2"),
            _edge("n_ppos", "y", "n_dist", "y2"),
            # Component deltas.
            _edge("n_ppos", "x", "n_dx", "a"),
            _edge("n_spos", "x", "n_dx", "b"),
            _edge("n_ppos", "y", "n_dy", "a"),
            _edge("n_spos", "y", "n_dy", "b"),
            # Guard.
            _edge("n_dist", "distance", "n_gate", "value"),
            # Normalization.
            _edge("n_dx", "value", "n_nx", "a"),
            _edge("n_dist", "distance", "n_nx", "b"),
            _edge("n_dy", "value", "n_ny", "a"),
            _edge("n_dist", "distance", "n_ny", "b"),
            # Scaling by the authored speed.
            _edge("n_nx", "value", "n_vx", "a"),
            _edge("n_speed", "value", "n_vx", "b"),
            _edge("n_ny", "value", "n_vy", "a"),
            _edge("n_speed", "value", "n_vy", "b"),
            # Motion.
            _edge("n_vx", "value", "n_move", "x"),
            _edge("n_vy", "value", "n_move", "y"),
        ],
    }


def threshold_chase_graph() -> dict:
    """The same chain, stopping at a *variable* range instead of at zero.

    ``compare_number`` takes its right-hand operand from a property, so it
    cannot compare against a value that comes down a wire -- and both AI assets
    compare the distance against ``detection_range`` / ``attack_range``, which
    are blackboard variables. Subtracting first and comparing the remainder
    against zero expresses the same test with no node type the palette lacks.
    This is the shape item 14E needs; proving it here keeps 14E from
    discovering a blocker after it has already touched an asset.
    """
    graph = copy.deepcopy(chase_graph())
    graph["name"] = "ScalarChaseWithRange"
    graph["variables"]["arrival_range"] = 10.0
    graph["nodes"] += [
        _node("n_range", "get_variable", scope="object", name="arrival_range"),
        _node("n_margin", "subtract_number"),
    ]
    graph["edges"] = [
        edge
        for edge in graph["edges"]
        if not (edge["to_node"] == "n_gate" and edge["to_port"] == "value")
    ]
    graph["edges"] += [
        _edge("n_dist", "distance", "n_margin", "a"),
        _edge("n_range", "value", "n_margin", "b"),
        _edge("n_margin", "value", "n_gate", "value"),
    ]
    return graph


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


class _Object:
    """A movable thing with a position, and nothing else.

    Attributes are declared rather than served by ``__getattr__`` on purpose: a
    catch-all makes ``rigidbody`` truthy and sends ``move_by`` down a physics
    branch this graph never asks for. The same trap is documented in
    ``tests/logic/stage2/test_shipping_graphs_still_work.py``.
    """

    def __init__(self, x: float, y: float, tag: str) -> None:
        self.x = float(x)
        self.y = float(y)
        self.tag = tag
        self.rigidbody = None
        self.components: list = []

    def move(self, delta_x: float, delta_y: float = 0.0) -> None:
        self.x += float(delta_x)
        self.y += float(delta_y)


class _Game(_Object):
    """The per-object host API: it *is* the enemy, and it can find the player.

    This mirrors ``PlayLogicAPI``, which the viewport builds one-per-object and
    passes to ``LogicGraphRuntime.start`` -- so ``game`` being the self object
    is the shipping arrangement, not a test convenience.
    """

    def __init__(self, enemy: tuple[float, float], player: tuple[float, float]) -> None:
        super().__init__(enemy[0], enemy[1], "Enemy")
        self.player = _Object(player[0], player[1], "Player")

    def find(self, tag: str):
        return self.player if str(tag).lower() == "player" else None


def _run(
    enemy: tuple[float, float],
    player: tuple[float, float],
    *,
    speed: float = 200.0,
    dt: float = 1.0 / 60.0,
    ticks: int = 1,
    graph: dict | None = None,
    variables: dict | None = None,
) -> tuple[_Game, LogicGraphRuntime]:
    game = _Game(enemy, player)
    runtime = LogicGraphRuntime(normalize_logic_graph(graph or chase_graph()))
    runtime.blackboard.set("object", "move_speed", speed, runtime.object_key)
    for name, value in (variables or {}).items():
        runtime.blackboard.set("object", name, value, runtime.object_key)
    for _ in range(ticks):
        runtime.update(game, dt)
    return game, runtime


def _orphan_edges(graph: dict) -> list[str]:
    """Edges naming a port the node's contract does not declare.

    Same rule as the shipping-asset gate: a prototype is only evidence if it is
    measured by the check the real graphs are measured by.
    """
    nodes = {str(node["id"]): node for node in graph.get("nodes", [])}
    orphans: list[str] = []
    for edge in graph.get("edges", []):
        source = nodes.get(str(edge.get("from_node") or ""))
        target = nodes.get(str(edge.get("to_node") or ""))
        from_port = str(edge.get("from_port") or "")
        to_port = str(edge.get("to_port") or "")
        if source is not None and from_port:
            outputs = {name for name, _kind in node_port_definitions(source)["outputs"]}
            if from_port not in outputs:
                orphans.append(f"{source.get('type')}.{from_port}>out")
        if target is not None and to_port:
            inputs = {name for name, _kind in node_port_definitions(target)["inputs"]}
            if to_port not in inputs:
                orphans.append(f"{target.get('type')}.{to_port}>in")
    return sorted(set(orphans))


def _phantom_nodes(graph: dict) -> list[str]:
    return sorted(
        {
            str(node["type"])
            for node in graph.get("nodes", [])
            if resolve_node_id(str(node["type"])) not in NODE_DEFINITIONS
        }
    )


GRAPHS = {"chase": chase_graph, "threshold": threshold_chase_graph}


# ---------------------------------------------------------------------------
# Construction, and the four zero-counts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("builder", sorted(GRAPHS))
def test_prototype_uses_only_existing_nodes(builder: str):
    types = {str(node["type"]) for node in GRAPHS[builder]()["nodes"]}
    assert types <= ALLOWED_TYPES, f"outside the current palette: {sorted(types - ALLOWED_TYPES)}"
    for node_type in sorted(types):
        assert resolve_node_id(node_type) in NODE_DEFINITIONS, node_type


@pytest.mark.parametrize("builder", sorted(GRAPHS))
def test_prototype_has_no_phantom_nodes(builder: str):
    assert _phantom_nodes(normalize_logic_graph(GRAPHS[builder]())) == []


@pytest.mark.parametrize("builder", sorted(GRAPHS))
def test_prototype_has_no_orphan_edges(builder: str):
    assert _orphan_edges(normalize_logic_graph(GRAPHS[builder]())) == []


@pytest.mark.parametrize("builder", sorted(GRAPHS))
def test_normalize_is_idempotent(builder: str):
    """A freshly authored graph must need no correction at all.

    If normalize changes something on the second pass, the first pass was
    repairing the graph rather than canonicalizing it -- which would mean the
    prototype was not authored against the current contract after all.
    """
    once = normalize_logic_graph(GRAPHS[builder]())
    assert normalize_logic_graph(once) == once


def test_no_vector_api_node_is_required():
    """The chain closes without the API item 14C declined."""
    types = {str(node["type"]) for node in chase_graph()["nodes"]}
    assert not types & REJECTED_VECTOR_TYPES
    for rejected in REJECTED_VECTOR_TYPES:
        assert resolve_node_id(rejected) not in NODE_DEFINITIONS, (
            f"{rejected} now exists; the premise of this suite changed and the "
            "scalar re-authoring plan needs re-deciding, not silently keeping"
        )


def test_the_prototype_writes_no_shipping_asset():
    """The graph is built in memory; no string here names a shipping path.

    Read out of the AST rather than off the raw text, and with this function
    excluded: a plain substring scan matches the needle sitting in its own
    assertion, which makes the check pass or fail for a reason that has nothing
    to do with the prototype.
    """
    import ast
    import pathlib

    tree = ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    this_test = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "test_the_prototype_writes_no_shipping_asset"
    )
    excluded = {id(node) for node in ast.walk(this_test)}
    # Docstrings are prose: they discuss the assets on purpose. Only code can
    # actually open one.
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                excluded.add(id(first.value))

    offenders = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in excluded
        # A bare filename is a tmp_path leaf; a separator makes it a location.
        and (
            (".zlogic" in node.value and ("/" in node.value or "\\" in node.value))
            or node.value.lower().startswith("assets")
        )
    ]
    assert offenders == [], f"the prototype names a shipping path: {offenders}"


def test_find_tag_is_the_canonical_id():
    """A new graph uses ``find_tag``, not the legacy spelling.

    ``object.find_by_name`` still resolves -- item 14A restored that alias for
    the assets that already carry it -- but an alias is a migration path, not an
    authoring choice.
    """
    types = {str(node["type"]) for node in chase_graph()["nodes"]}
    assert "find_tag" in types
    assert "object.find_by_name" not in types
    assert resolve_node_id("object.find_by_name") == "find_tag"


# ---------------------------------------------------------------------------
# Save / reopen
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("builder", sorted(GRAPHS))
def test_save_and_reopen_preserves_the_graph(tmp_path, builder: str):
    original = normalize_logic_graph(GRAPHS[builder]())
    destination = tmp_path / f"{builder}.zlogic"
    save_logic_graph(destination, original)
    reloaded = normalize_logic_graph(load_logic_graph(destination))

    assert reloaded == original
    assert _orphan_edges(reloaded) == []
    assert _phantom_nodes(reloaded) == []
    assert {n["id"] for n in reloaded["nodes"]} == {n["id"] for n in original["nodes"]}
    assert len(reloaded["edges"]) == len(original["edges"])


def test_the_reopened_graph_still_chases(tmp_path):
    destination = tmp_path / "reopened.zlogic"
    save_logic_graph(destination, normalize_logic_graph(chase_graph()))
    game, _ = _run((0.0, 0.0), (3.0, 4.0), graph=load_logic_graph(destination))
    assert (game.x, game.y) == pytest.approx((2.0, 8.0 / 3.0))


# ---------------------------------------------------------------------------
# The math, measured node by node
# ---------------------------------------------------------------------------


def test_every_intermediate_value_is_correct():
    """(0,0) chasing (3,4) is the 3-4-5 triangle, so every step is exact."""
    game, runtime = _run((0.0, 0.0), (3.0, 4.0), speed=200.0)
    values = runtime.values

    assert values[("n_dx", "value")] == pytest.approx(3.0)
    assert values[("n_dy", "value")] == pytest.approx(4.0)
    assert values[("n_dist", "distance")] == pytest.approx(5.0)
    assert values[("n_nx", "value")] == pytest.approx(0.6)
    assert values[("n_ny", "value")] == pytest.approx(0.8)
    assert values[("n_speed", "value")] == pytest.approx(200.0)
    assert values[("n_vx", "value")] == pytest.approx(120.0)
    assert values[("n_vy", "value")] == pytest.approx(160.0)


def test_move_by_consumes_x_and_y():
    """``move_by`` treats x/y as velocity, so one frame moves v * dt."""
    game, _ = _run((0.0, 0.0), (3.0, 4.0), speed=200.0, dt=1.0 / 60.0)
    assert game.x == pytest.approx(120.0 / 60.0)
    assert game.y == pytest.approx(160.0 / 60.0)


def test_the_normalized_direction_is_a_unit_vector():
    game, runtime = _run((10.0, -20.0), (310.0, 380.0))
    nx = runtime.values[("n_nx", "value")]
    ny = runtime.values[("n_ny", "value")]
    assert math.hypot(nx, ny) == pytest.approx(1.0)


def test_distance_to_the_player_decreases():
    before = 5.0
    game, _ = _run((0.0, 0.0), (3.0, 4.0))
    after = math.hypot(3.0 - game.x, 4.0 - game.y)
    assert after < before
    assert after == pytest.approx(5.0 - 200.0 / 60.0)


def test_self_position_comes_from_the_owner_object():
    """No ``target`` edge means the graph's own object -- and it is read live.

    Starting the enemy away from the origin is what makes this a real check: if
    ``get_position`` fell back to a default or to the player, the first frame
    would move in a different direction entirely.
    """
    game, runtime = _run((100.0, 100.0), (100.0, 300.0))
    assert runtime.values[("n_dx", "value")] == pytest.approx(0.0)
    assert runtime.values[("n_dy", "value")] == pytest.approx(200.0)
    assert game.x == pytest.approx(100.0)
    assert game.y > 100.0


def test_player_position_comes_from_find_tag():
    game, runtime = _run((0.0, 0.0), (42.0, 0.0))
    assert runtime.values[("n_dist", "distance")] == pytest.approx(42.0)


# ---------------------------------------------------------------------------
# Direction
# ---------------------------------------------------------------------------

DIRECTIONS = {
    "east": (100.0, 0.0),
    "west": (-100.0, 0.0),
    "north": (0.0, 100.0),
    "south": (0.0, -100.0),
    "north_east": (100.0, 100.0),
    "north_west": (-100.0, 100.0),
    "south_east": (100.0, -100.0),
    "south_west": (-100.0, -100.0),
}


@pytest.mark.parametrize("name", sorted(DIRECTIONS))
def test_movement_points_at_the_player(name: str):
    """Moving is not enough -- it has to move *towards*.

    The cosine between the step and the line to the player must be 1: any wrong
    sign, or a swapped axis, lands well away from it. A distance check alone
    would pass for a step that merely happens to shorten the gap.
    """
    player = DIRECTIONS[name]
    game, _ = _run((0.0, 0.0), player)

    step = math.hypot(game.x, game.y)
    assert step > 0.0, "the enemy did not move at all"
    cosine = (game.x * player[0] + game.y * player[1]) / (step * math.hypot(*player))
    assert cosine == pytest.approx(1.0)

    before = math.hypot(*player)
    after = math.hypot(player[0] - game.x, player[1] - game.y)
    assert after < before


# ---------------------------------------------------------------------------
# Degenerate and boundary cases
# ---------------------------------------------------------------------------


def test_standing_on_the_player_is_safe():
    """distance == 0 must not divide, and must not nudge the object.

    ``divide_number`` raises on a zero divisor, so the guard is not cosmetic:
    without it the frame would end in a runtime error. The normalization nodes
    are never evaluated here, which is the whole reason the guard sits on the
    flow rather than on the value.
    """
    game, runtime = _run((50.0, 50.0), (50.0, 50.0))

    assert runtime.values[("n_dist", "distance")] == pytest.approx(0.0)
    assert ("n_nx", "value") not in runtime.values
    assert ("n_ny", "value") not in runtime.values
    assert (game.x, game.y) == (50.0, 50.0)


def test_no_nan_or_infinity_anywhere():
    for enemy, player in (((0.0, 0.0), (0.0, 0.0)), ((0.0, 0.0), (3.0, 4.0)), ((-7.5, 2.25), (0.0, 0.0))):
        game, runtime = _run(enemy, player)
        assert math.isfinite(game.x) and math.isfinite(game.y)
        for key, value in runtime.values.items():
            if isinstance(value, float):
                assert math.isfinite(value), f"{key} = {value}"


def test_zero_speed_does_not_move():
    game, runtime = _run((0.0, 0.0), (3.0, 4.0), speed=0.0)
    assert runtime.values[("n_vx", "value")] == pytest.approx(0.0)
    assert runtime.values[("n_vy", "value")] == pytest.approx(0.0)
    assert (game.x, game.y) == (0.0, 0.0)


@pytest.mark.parametrize("speed", [100.0, 200.0, 300.0])
def test_speed_scales_the_step(speed: float):
    """The step is proportional to the authored speed, with no constant in the graph."""
    game, runtime = _run((0.0, 0.0), (300.0, 400.0), speed=speed, dt=1.0 / 60.0)
    magnitude = math.hypot(runtime.values[("n_vx", "value")], runtime.values[("n_vy", "value")])
    assert magnitude == pytest.approx(speed)
    assert math.hypot(game.x, game.y) == pytest.approx(speed / 60.0)


@pytest.mark.parametrize("dt", [1.0 / 30.0, 1.0 / 60.0, 1.0 / 120.0])
def test_distance_per_second_is_independent_of_dt(dt: float):
    """``move_by`` multiplies by dt, so speed means pixels per second.

    That semantic is not changed here -- it is asserted, so a later change to
    ``move_by`` cannot silently make the chase frame-rate dependent.
    """
    game, _ = _run((0.0, 0.0), (300.0, 400.0), speed=200.0, dt=dt)
    assert math.hypot(game.x, game.y) / dt == pytest.approx(200.0)


def test_speed_comes_from_the_blackboard_not_from_the_graph():
    """``move_speed`` is read with ``get_variable``, as the real assets do.

    Two runs of the same graph with different variables must differ; if the
    speed were baked into a property, they would not.
    """
    fast, _ = _run((0.0, 0.0), (300.0, 400.0), speed=300.0)
    slow, _ = _run((0.0, 0.0), (300.0, 400.0), speed=100.0)
    assert math.hypot(fast.x, fast.y) > math.hypot(slow.x, slow.y)
    speed_nodes = [n for n in chase_graph()["nodes"] if n["type"] == "get_variable"]
    assert [n["properties"]["name"] for n in speed_nodes] == ["move_speed"]


# ---------------------------------------------------------------------------
# Over time
# ---------------------------------------------------------------------------


def test_the_chase_converges():
    """150 frames at 200 px/s is exactly the 500 px gap, and then it stops.

    Landing on the player is what arms the zero-distance guard in a loop rather
    than in a single contrived frame: every later frame measures 0, takes the
    false branch, and leaves the object alone.
    """
    game = _Game((0.0, 0.0), (300.0, 400.0))
    runtime = LogicGraphRuntime(normalize_logic_graph(chase_graph()))
    runtime.blackboard.set("object", "move_speed", 200.0, runtime.object_key)

    previous = 500.0
    for _ in range(200):
        runtime.update(game, 1.0 / 60.0)
        distance = math.hypot(300.0 - game.x, 400.0 - game.y)
        assert distance <= previous + 1e-9, "the enemy moved away from the player"
        previous = distance

    assert previous == pytest.approx(0.0, abs=1e-9)


def test_a_variable_range_stops_the_chase_short():
    """The shape item 14E needs: compare against a value that arrives on a wire.

    ``compare_number`` reads its right-hand operand from a property, so it
    cannot see ``detection_range``. Subtracting first and testing the remainder
    against zero says the same thing with node types the palette already has --
    and it also removes the one-step oscillation a bare ``> 0`` leaves when the
    step does not divide the gap evenly.
    """
    graph = threshold_chase_graph()
    game = _Game((0.0, 0.0), (7.0, 0.0))
    runtime = LogicGraphRuntime(normalize_logic_graph(graph))
    runtime.blackboard.set("object", "move_speed", 200.0, runtime.object_key)
    runtime.blackboard.set("object", "arrival_range", 5.0, runtime.object_key)

    for _ in range(10):
        runtime.update(game, 1.0 / 60.0)

    remaining = 7.0 - game.x
    assert game.y == pytest.approx(0.0)
    assert remaining == pytest.approx(7.0 - 200.0 / 60.0)
    assert remaining <= 5.0, "it should have stopped once inside the range"
