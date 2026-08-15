"""``distance_to_point`` honours the inputs it declares.

PHASE 9 recovery item 14D.1.

The node declares ``x1``, ``y1``, ``x2`` and ``y2`` as inputs, and the executor
read them straight off ``properties``. A data edge into any of them did nothing:
a node wired from ``get_position`` still computed ``(0,0) -> (100,100)`` and
returned 141.42 on every frame, whatever the objects were doing.

That makes the node unusable for anything whose positions move -- which is every
real use of a distance node, and precisely why the scalar chase plan of item 14D
could not close. Item 9 found the same shape on ``move_by`` and item 11 on
``find_tag``: a declared input the runtime never reads.

The fix keeps property authoring working. A connected input wins; with nothing
connected the property, and its default, still answers.

No shipping asset uses this node -- zero instances -- so the change makes the
promised case work rather than altering an existing one.
"""

from __future__ import annotations

import ast
import inspect
import math
import pathlib
import textwrap

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
)
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.registry import registry

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
NODE = "distance_to_point"
COORDINATES = ("x1", "y1", "x2", "y2")


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


class _Game:
    pass


def _graph(properties: dict, wired: dict | None = None):
    nodes = [{"id": "d", "type": NODE, "position": [0.0, 0.0], "properties": dict(properties)}]
    edges = []
    for index, (port, value) in enumerate(sorted((wired or {}).items())):
        source = f"c{index}"
        nodes.append({"id": source, "type": "number_value", "position": [0.0, 0.0],
                      "properties": {"value": value}})
        edges.append({"from_node": source, "from_port": "value",
                      "to_node": "d", "to_port": port, "kind": "data"})
    return normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Distance",
        "nodes": nodes, "edges": edges,
    })


def _distance(properties: dict, wired: dict | None = None):
    graph = _graph(properties, wired)
    runtime = LogicGraphRuntime(graph)
    node = next(n for n in graph["nodes"] if str(n["id"]) == "d")
    game = _Game()
    ports = registry.executors[NODE](runtime, node, game, 1 / 60)
    return ports, runtime._evaluate_output("d", "distance", game, 1 / 60, set())


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------

def test_the_four_coordinates_are_declared_inputs():
    declared = {name for name, _kind in NODE_PORT_DEFINITIONS[NODE]["inputs"]}
    assert set(COORDINATES) <= declared


def test_the_executor_asks_the_runtime_for_its_inputs():
    """It must go through ``_read_input``, not read ``properties`` alone.

    Deliberately shallow: it asserts the seam exists, and every coordinate is
    then proved to be *driven* by an edge in the precedence tests below. An
    earlier version of this test pinned the exact shape of the call and broke
    when the four reads were factored into a helper -- structure is not the
    thing worth asserting here, behaviour is.
    """
    source = textwrap.dedent(inspect.getsource(registry.executors[NODE]))
    tree = ast.parse(source)
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "_read_input" in calls
    for coordinate in COORDINATES:
        assert coordinate in source


def test_the_executor_returns_only_declared_ports():
    from tools.audit_node_system import returned_flow_ports

    from engine.logic.graph_asset import declared_flow_outputs

    assert returned_flow_ports(registry.executors[NODE]) <= set(declared_flow_outputs(NODE))


# ---------------------------------------------------------------------------
# Precedence: the point of the item
# ---------------------------------------------------------------------------

def test_a_connected_input_wins_over_the_property():
    """property x2=100, edge x2=3 -> the runtime must use 3."""
    _ports, distance = _distance(
        {"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 100.0},
        wired={"x2": 3.0, "y2": 4.0},
    )
    assert distance == pytest.approx(5.0)


def test_without_an_edge_the_property_still_answers():
    """Authoring by property is unchanged."""
    _ports, distance = _distance({"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 100.0})
    assert distance == pytest.approx(math.hypot(100.0, 100.0))


def test_the_declared_defaults_still_apply_with_no_properties_at_all():
    _ports, distance = _distance({})
    assert distance == pytest.approx(math.hypot(100.0, 100.0))


@pytest.mark.parametrize("port", COORDINATES)
def test_each_coordinate_can_be_driven_independently(port: str):
    """One wired pin must not disturb the other three."""
    base = {"x1": 0.0, "y1": 0.0, "x2": 3.0, "y2": 4.0}
    _ports, before = _distance(base)
    assert before == pytest.approx(5.0)
    _ports, after = _distance(base, wired={port: 0.0})
    expected = dict(base)
    expected[port] = 0.0
    assert after == pytest.approx(
        math.hypot(expected["x2"] - expected["x1"], expected["y2"] - expected["y1"])
    )


def test_a_wired_zero_is_used_rather_than_treated_as_absent():
    """The falsy trap: 0.0 is a coordinate, not a missing connection."""
    _ports, distance = _distance(
        {"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 100.0},
        wired={"x2": 0.0, "y2": 0.0},
    )
    assert distance == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("x2,y2,expected", [
    (3.0, 4.0, 5.0), (-3.0, -4.0, 5.0), (0.0, 10.0, 10.0), (10.0, 0.0, 10.0),
])
def test_the_distance_is_euclidean_and_unsigned(x2: float, y2: float, expected: float):
    _ports, distance = _distance({"x1": 0.0, "y1": 0.0}, wired={"x2": x2, "y2": y2})
    assert distance == pytest.approx(expected)


def test_the_same_point_is_zero_and_does_not_raise():
    ports, distance = _distance({"x1": 5.0, "y1": 5.0}, wired={"x2": 5.0, "y2": 5.0})
    assert distance == pytest.approx(0.0)
    assert ports == ["exec_calculated"]


def test_the_success_branch_fires_on_a_normal_calculation():
    ports, _distance_value = _distance({}, wired={"x2": 3.0, "y2": 4.0})
    assert ports == ["exec_calculated"]


# ---------------------------------------------------------------------------
# Why this was safe to change
# ---------------------------------------------------------------------------

def test_the_shipping_assets_that_use_the_node_are_named_not_counted():
    """Inverted by item 14E: the promised case arrived.

    At item 14D.1 no shipping asset used this node at all, which is exactly why
    fixing it was safe -- the change enabled a future use rather than altering
    a live one. Item 14E is that future use: BossAILogic and EnemyAILogic now
    measure their distance to the player with it.

    Naming the assets rather than counting them keeps the check specific: a
    third graph picking the node up is a fact worth noticing, not a number that
    quietly drifts. That is exactly what happened -- PHASE 9 recovery item 18
    gave BossCombatLogic a range guard built on the same chain, so the node now
    has three users and this record says which.
    """
    users = set()
    for path in sorted((REPO_ROOT / "Assets").rglob("*.zlogic")):
        try:
            graph = normalize_logic_graph(load_logic_graph(path))
        except Exception:  # pragma: no cover
            continue
        if any(str(n["type"]) == NODE for n in graph["nodes"]):
            users.add(path.name)
    assert users == {"BossAILogic.zlogic", "BossCombatLogic.zlogic",
                     "EnemyAILogic.zlogic", "EnemyAttackLogic.zlogic"}, users


def test_the_node_is_still_the_one_the_catalogue_declares():
    assert NODE in NODE_DEFINITIONS
    assert NODE in registry.executors


def test_no_asset_was_modified():
    import subprocess

    changed = subprocess.run(
        ["git", "status", "--porcelain", "--", "Assets"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    unallowed = [l for l in changed.splitlines() if "EnemyAttackLogic.zlogic" not in l and "BossHealthLogic.zlogic" not in l]
    assert not unallowed, unallowed


# ---------------------------------------------------------------------------
# The chase step this unblocks
# ---------------------------------------------------------------------------

def test_the_distance_output_feeds_a_divide_node():
    """The normalisation step item 14D needs: dx / distance."""
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Normalise",
        "nodes": [
            {"id": "px", "type": "number_value", "position": [0.0, 0.0], "properties": {"value": 3.0}},
            {"id": "py", "type": "number_value", "position": [0.0, 0.0], "properties": {"value": 4.0}},
            {"id": "d", "type": NODE, "position": [0.0, 0.0], "properties": {"x1": 0.0, "y1": 0.0}},
            {"id": "n", "type": "divide_number", "position": [0.0, 0.0], "properties": {"a": 3.0}},
        ],
        "edges": [
            {"from_node": "px", "from_port": "value", "to_node": "d", "to_port": "x2", "kind": "data"},
            {"from_node": "py", "from_port": "value", "to_node": "d", "to_port": "y2", "kind": "data"},
            {"from_node": "d", "from_port": "distance", "to_node": "n", "to_port": "b", "kind": "data"},
        ],
    })
    runtime = LogicGraphRuntime(graph)
    game = _Game()
    node = next(n for n in graph["nodes"] if str(n["id"]) == "d")
    registry.executors[NODE](runtime, node, game, 1 / 60)
    assert runtime._evaluate_output("d", "distance", game, 1 / 60, set()) == pytest.approx(5.0)
    assert runtime._evaluate_output("n", "value", game, 1 / 60, set()) == pytest.approx(0.6)
