"""The AI chase graphs were authored against an API this engine never had.

PHASE 9 recovery item 14C, a design gate. No production changed, nothing
implemented.

Item 14 began with the theory that two enemies stand still because ``move_by``
ignores an authored ``velocity``. Item 14A disproved it: the value is ``None``.
Item 14B narrowed the first break to ``math.distance``. Re-validating from the
tree disproved *that* too, and the real picture is larger.

Of ``BossAILogic``'s 23 edges, 16 do not resolve. Of ``EnemyAILogic``'s 25, 20
do not. And the breaks are not only missing nodes -- two of them point at nodes
that **exist**, with entirely different port shapes:

    assets wire            engine offers
    get_position.object    get_position.target
    get_position.position  get_position.x, get_position.y
    if_else.value          if_else.condition

So implementing ``vector2``, ``normalize_vector`` and ``math.distance`` would
not have made these graphs run. ``multiply_number`` would still reject a vector
-- its evaluator calls ``float()`` on both inputs -- and the two port mismatches
above would still dangle.

**Decision: do not adopt a vector API.** Building one would mean three new
nodes, new ports on two existing nodes, and a vector overload on a third, to
serve two assets. The engine already has the scalar pieces -- ``get_position``
returns ``x``/``y``, ``distance_to_point`` takes four scalars,
``multiply_number`` multiplies numbers. The assets are to be re-authored onto
that API, which is the next item's subject.

These tests lock the findings so the next item starts from measured facts, and
so that adopting the vector API later becomes a deliberate reversal rather than
a drift.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
)
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.registry import registry

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIT = json.loads(
    (REPO_ROOT / "tests" / "fixtures" / "stage2" / "ai_chase_chain_audit.json")
    .read_text(encoding="utf-8")
)
GRAPHS = ("BossAILogic", "EnemyAILogic")


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


def _unresolved(name: str) -> list[str]:
    graph = normalize_logic_graph(
        load_logic_graph(REPO_ROOT / "Assets" / "Logic" / f"{name}.zlogic")
    )
    nodes = {str(n["id"]): n for n in graph["nodes"]}
    broken = []
    for edge in graph["edges"]:
        source, target = nodes.get(str(edge.get("from_node"))), nodes.get(str(edge.get("to_node")))
        if not source or not target:
            continue
        st, dt = str(source["type"]), str(target["type"])
        sp, dp = str(edge.get("from_port")), str(edge.get("to_port"))
        ok_s = st in NODE_DEFINITIONS and sp in {p for p, _ in node_port_definitions(source)["outputs"]}
        ok_d = dt in NODE_DEFINITIONS and dp in {p for p, _ in node_port_definitions(target)["inputs"]}
        if not (ok_s and ok_d):
            broken.append(f"{st}.{sp} -> {dt}.{dp}")
    return broken


# ---------------------------------------------------------------------------
# The measured state, locked
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", GRAPHS)
def test_the_recorded_edge_counts_are_still_true(name: str):
    recorded = AUDIT["chains"][name]
    assert len(_unresolved(name)) == recorded["unresolved_edges"]


@pytest.mark.parametrize("name", GRAPHS)
def test_most_of_the_graph_now_resolves(name: str):
    """Inverted by item 14E, which is what this gate existed to authorize.

    The original reading was the finding: the chase did not fail at one missing
    node, the majority of its edges dangled (Boss 16/23, Enemy 20/25). That is
    why item 14C refused a point fix and item 14D chose reauthoring.

    Both assets are now reauthored, so the relation flips. The pre-14E counts
    are kept in the fixture under ``_before_item14E`` so the finding is not
    erased by being fixed.
    """
    recorded = AUDIT["chains"][name]
    assert recorded["resolved_edges"] > recorded["unresolved_edges"]
    before = recorded["_before_item14E"]
    assert before["unresolved_edges"] > before["resolved_edges"]
    assert recorded["unresolved_edges"] < before["unresolved_edges"]


def test_the_decision_is_recorded_and_is_not_the_vector_api():
    assert AUDIT["decision"] == "C_REAUTHOR_ASSETS_ONTO_EXISTING_API"
    assert AUDIT["vector_api_adopted"] is False


# ---------------------------------------------------------------------------
# The two breaks that are NOT missing nodes
# ---------------------------------------------------------------------------

def test_get_position_exists_but_offers_a_different_shape():
    """The assets wire ``object``/``position``; the engine has ``target``/``x``,``y``."""
    ports = NODE_PORT_DEFINITIONS["get_position"]
    inputs = {name for name, _kind in ports["inputs"]}
    outputs = {name for name, _kind in ports["outputs"]}
    assert inputs == {"target"} and "object" not in inputs
    assert outputs == {"x", "y"} and "position" not in outputs


def test_if_else_exists_but_offers_a_different_shape():
    ports = NODE_PORT_DEFINITIONS["if_else"]
    inputs = {name for name, _kind in ports["inputs"]}
    assert "condition" in inputs
    assert "value" not in inputs and "compare_value" not in inputs


@pytest.mark.parametrize("name", GRAPHS)
def test_those_two_mismatches_are_gone_from_the_assets(name: str):
    """Inverted by item 14E: the phantom pins it named have been rewired.

    ``get_position.position`` / ``.object`` and ``if_else.value`` were edges
    into pins that never existed. Item 14E rewired positions onto
    ``target``/``x``/``y`` and replaced the ``if_else`` comparators with
    ``compare_number`` fed by a subtraction, so none of the three appears.

    Everything still unresolved must be animation, which item 14E left as
    declared debt -- asserting that keeps this from passing for the wrong
    reason if some other edge breaks later.
    """
    broken = " ".join(_unresolved(name))
    assert "get_position.position" not in broken
    assert "get_position.object" not in broken
    assert "if_else.value" not in broken
    for entry in _unresolved(name):
        assert any(
            token in entry
            for token in ("set_animator_parameter", "animator.set_trigger", "variable.increment")
        ), entry


# ---------------------------------------------------------------------------
# Why the vector API would not have been enough
# ---------------------------------------------------------------------------

def test_multiply_number_cannot_multiply_a_vector():
    """Its evaluator calls float() on both inputs -- a Vector2 raises."""
    class _Runtime:
        values: dict = {}

        def _read_input(self, node_id, port, default, game, dt, branch):
            return default

    node = {"id": "n", "type": "multiply_number",
            "properties": {"a": (0.6, 0.8), "b": 200.0}}
    with pytest.raises(TypeError):
        registry.evaluators["multiply_number"](
            _Runtime(), "n", "value", node, object(), 1 / 60, set()
        )


def test_the_vector_contracts_exist_but_the_nodes_do_not():
    """A find this gate turned up: the design got as far as the port table.

    ``_EXPLICIT_PORT_CONTRACTS`` already declares ``vector2``,
    ``normalize_vector`` and ``magnitude_vector`` -- inputs, outputs and a
    ``vector2`` pin kind -- while none of them has a definition, an executor or
    an evaluator. So the vector API was specified and never built, which is why
    ``move_by.velocity`` could be typed ``vector2`` with nothing able to fill it.

    Recorded rather than acted on: it does not change the decision, because the
    two port mismatches on ``get_position`` and ``if_else`` would still dangle
    and ``multiply_number`` would still reject a vector.
    """
    producers = sorted(
        node_id for node_id, ports in NODE_PORT_DEFINITIONS.items()
        if any(kind == "vector2" for _name, kind in ports.get("outputs", ()))
    )
    assert producers == ["normalize_vector", "vector2"], producers
    for node_id in producers:
        assert node_id not in NODE_DEFINITIONS, f"{node_id} gained a definition"
        assert node_id not in registry.executors
        assert node_id not in registry.evaluators
    assert any(
        kind == "vector2" for _n, kind in NODE_PORT_DEFINITIONS["move_by"]["inputs"]
    )


def test_the_scalar_pieces_the_next_item_will_use_all_exist():
    """The re-authoring plan depends on these; fail early if one disappears."""
    for node_id in ("get_position", "distance_to_point", "multiply_number",
                    "if_else", "move_by", "find_tag", "get_variable"):
        assert node_id in NODE_DEFINITIONS, node_id


def test_the_scalar_chase_is_computable_with_todays_api():
    """Prove the maths works with scalars before anyone re-authors anything.

    player (3, 4) from enemy (0, 0): distance 5, unit direction (0.6, 0.8),
    velocity at speed 200 is (120, 160) with magnitude 200 -- all reachable from
    get_position.x/y, distance_to_point and multiply_number.
    """
    import math

    ex, ey, px, py = 0.0, 0.0, 3.0, 4.0
    dx, dy = px - ex, py - ey
    distance = math.hypot(dx, dy)
    assert distance == pytest.approx(5.0)

    ux, uy = dx / distance, dy / distance
    assert math.hypot(ux, uy) == pytest.approx(1.0)

    speed = 200.0
    vx, vy = ux * speed, uy * speed
    assert (vx, vy) == pytest.approx((120.0, 160.0))
    assert math.hypot(vx, vy) == pytest.approx(speed)


# ---------------------------------------------------------------------------
# The gate refused to implement, and that must stay true
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_id", ("vector2", "normalize_vector", "math.distance"))
def test_no_vector_node_was_created_by_this_gate(node_id: str):
    assert node_id not in NODE_DEFINITIONS
    assert node_id not in registry.executors
    assert node_id not in registry.evaluators


def test_move_by_still_does_not_read_velocity():
    """14F territory: the new design may not even need it."""
    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(inspect.getsource(registry.executors["move_by"]))
    read = {
        argument.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("get", "_read_input")
        for argument in node.args[:2]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
    }
    assert "velocity" not in read


def test_victory_logic_is_not_bundled_into_this_decision():
    """A separate case, deliberately left out of the AI decision."""
    assert "VictoryLogic" not in json.dumps(AUDIT)


def test_no_asset_was_modified():
    import subprocess

    changed = subprocess.run(
        ["git", "status", "--porcelain", "--", "Assets"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert not changed, changed
