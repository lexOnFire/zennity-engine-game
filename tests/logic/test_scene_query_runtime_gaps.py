"""``find_nearest_object`` and ``get_object_name``: contracts that now run.

PHASE 9 recovery item 10.

Both nodes shipped a NodeDefinition, appeared in the palette, and had no runtime
at all. An author could place either one, wire it, save it -- and nothing
happened, because ``_execute`` falls through to ``return ["next"]`` when no
executor is registered and an unevaluated data pin yields nothing.

They were not missing because nobody wrote them. Both implementations exist on
the Stage 1 lineage (``03912bc``, and ``939764c`` for the nearest-object melee
work), which is **not an ancestor of this branch** -- the recovery lineage
rebuilt the catalogue from the declarative modules while the runtime modules
came from a different tree, so the definitions arrived and the executors did
not.

The contracts are byte-identical to the ones that shipped with the original
implementation, so restoring them invents no semantics:

    find_nearest_object
        inputs  exec, tag, max_distance
        outputs exec_found, exec_none, object, distance

One deliberate change: ties are now resolved by name. The original kept the
first object encountered, which depended on the ordering of the world mapping.

``get_object_name`` declares ``pure_data`` and has no flow pin, so it is an
evaluator -- the same shape as its sibling ``get_tag``, in the same file.
"""

from __future__ import annotations

import pathlib

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    declared_flow_outputs,
    load_logic_graph,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.contracts import resolve_execution_model
from engine.logic.node_definitions import definition_owner
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
from engine.logic.node_system import classify_runtime_coverage, load_runtime_node_modules
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.registry import registry

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DT = 1.0 / 60.0


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


class _Game:
    """A host shaped like the one the executors actually meet."""

    def __init__(self, world: dict, x: float = 0.0, y: float = 0.0, name: str = "Player"):
        self._world = world
        self.x = x
        self.y = y
        self.name = name

    def find(self, _name):  # the executor falls back when this yields nothing
        return None


WORLD = {
    "Player": {"x": 0, "y": 0, "tag": "Player"},
    "Near": {"x": 10, "y": 0, "tag": "Enemy"},
    "Far": {"x": 30, "y": 0, "tag": "Enemy"},
    "Distant": {"x": 900, "y": 0, "tag": "Enemy"},
    "Sleeping": {"x": 1, "y": 0, "tag": "Enemy", "active": False},
}


def _find(properties: dict, world: dict | None = None):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Nearest",
        "nodes": [{"id": "n", "type": "find_nearest_object", "position": [0.0, 0.0],
                   "properties": dict(properties)}],
        "edges": [],
    })
    runtime = LogicGraphRuntime(graph)
    game = _Game(WORLD if world is None else world)
    node = graph["nodes"][0]
    ports = registry.executors["find_nearest_object"](runtime, node, game, DT)
    evaluate = registry.evaluators["find_nearest_object"]
    return (
        ports,
        evaluate(runtime, "n", "object", node, game, DT, set()),
        evaluate(runtime, "n", "distance", node, game, DT, set()),
    )


# ---------------------------------------------------------------------------
# The gap itself
# ---------------------------------------------------------------------------

def test_no_declared_node_is_left_without_a_runtime():
    """The whole point of the item: the gap list must be empty."""
    assert classify_runtime_coverage()["missing_runtime"] == []


@pytest.mark.parametrize("node_id", ("find_nearest_object", "get_object_name"))
def test_the_definition_owner_is_unchanged(node_id: str):
    assert definition_owner(node_id) == "scene_nodes"


def test_find_nearest_object_has_both_halves_of_its_contract():
    """Flow ports need an executor; data ports need an evaluator."""
    assert "find_nearest_object" in registry.executors
    assert "find_nearest_object" in registry.evaluators


def test_get_object_name_is_an_evaluator_not_an_executor():
    """It declares pure_data and has no flow pin -- an executor would be wrong."""
    assert "get_object_name" in registry.evaluators
    assert "get_object_name" not in registry.executors


@pytest.mark.parametrize("node_id,expected", [
    ("find_nearest_object", "action"),
    ("get_object_name", "pure_data"),
])
def test_the_execution_model_is_the_declared_one(node_id: str, expected: str):
    ports = NODE_PORT_DEFINITIONS[node_id]
    assert resolve_execution_model(
        NODE_DEFINITIONS[node_id].get("execution_model"),
        ports["inputs"], ports["outputs"],
    ) == expected


def test_no_deprecation_or_allow_list_was_used_to_close_the_gap():
    """The gap had to be filled, not hidden."""
    for node_id in ("find_nearest_object", "get_object_name"):
        assert not NODE_DEFINITIONS[node_id].get("deprecated", False)


# ---------------------------------------------------------------------------
# Contract / implementation parity
# ---------------------------------------------------------------------------

def test_the_executor_returns_only_declared_ports():
    from tools.audit_node_system import returned_flow_ports

    returned = returned_flow_ports(registry.executors["find_nearest_object"])
    assert returned <= set(declared_flow_outputs("find_nearest_object"))


def test_every_declared_branch_is_reachable():
    from tools.audit_node_system import returned_flow_ports

    declared = set(declared_flow_outputs("find_nearest_object"))
    assert declared == returned_flow_ports(registry.executors["find_nearest_object"])


def test_the_audit_still_reports_no_undeclared_outputs():
    from tools.audit_node_system import executor_output_violations

    assert executor_output_violations() == {}


def test_every_authorable_property_is_consumed():
    import ast
    import inspect
    import textwrap

    source = textwrap.dedent(inspect.getsource(registry.executors["find_nearest_object"]))
    read = {
        argument.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("get", "_read_input")
        for argument in node.args[:2]
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str)
    }
    authorable = set(NODE_DEFINITIONS["find_nearest_object"].get("properties", {}))
    assert not authorable - read, f"ignored: {sorted(authorable - read)}"


# ---------------------------------------------------------------------------
# find_nearest_object behaviour
# ---------------------------------------------------------------------------

def test_it_picks_the_nearest_and_reports_the_distance():
    ports, found, distance = _find({"tag": "Enemy", "max_distance": 100.0})
    assert ports == ["exec_found"]
    assert found.name == "Near"
    assert distance == pytest.approx(10.0)


def test_the_origin_object_never_finds_itself():
    """Player sits at distance 0 and must not win."""
    _ports, found, _d = _find({"tag": "", "max_distance": 100.0})
    assert found.name != "Player"


def test_an_inactive_object_is_skipped_even_when_closest():
    """``Sleeping`` is at distance 1, nearer than every candidate."""
    _ports, found, _d = _find({"tag": "", "max_distance": 100.0})
    assert found.name == "Near"


def test_max_distance_bounds_the_search():
    ports, found, distance = _find({"tag": "Enemy", "max_distance": 5.0})
    assert ports == ["exec_none"]
    assert found is None and distance == 0.0


def test_a_tag_that_matches_nothing_reports_none():
    ports, found, distance = _find({"tag": "Ghost", "max_distance": 100.0})
    assert ports == ["exec_none"]
    assert found is None and distance == 0.0


def test_an_empty_world_reports_none():
    ports, found, _d = _find({"tag": "", "max_distance": 100.0}, world={})
    assert ports == ["exec_none"] and found is None


def test_an_empty_tag_is_no_filter_rather_than_a_tag_named_empty():
    _ports, found, _d = _find({"tag": "", "max_distance": 100.0})
    assert found is not None


def test_a_tie_is_broken_deterministically():
    """The original kept whichever the world mapping yielded first."""
    tied = {"Zebra": {"x": 10, "y": 0, "tag": "Enemy"},
            "Alpha": {"x": 10, "y": 0, "tag": "Enemy"}}
    first = _find({"tag": "Enemy", "max_distance": 100.0}, world=tied)[1]
    reversed_world = dict(reversed(list(tied.items())))
    second = _find({"tag": "Enemy", "max_distance": 100.0}, world=reversed_world)[1]
    assert first.name == second.name == "Alpha"


def test_the_result_exposes_name_and_tag_for_the_downstream_getters():
    """``get_object_name`` and ``get_tag`` read these off the found object."""
    _ports, found, _d = _find({"tag": "Enemy", "max_distance": 100.0})
    assert found.name == "Near" and found.tag == "Enemy"


# ---------------------------------------------------------------------------
# get_object_name behaviour
# ---------------------------------------------------------------------------

def _name_of(target):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Naming",
        "nodes": [{"id": "n", "type": "get_object_name", "position": [0.0, 0.0]}],
        "edges": [],
    })
    runtime = LogicGraphRuntime(graph)
    return registry.evaluators["get_object_name"](
        runtime, "n", "value", graph["nodes"][0], target, DT, set()
    )


class _Named:
    def __init__(self, name):
        self.name = name


def test_it_returns_the_authored_name():
    assert _name_of(_Named("Player")) == "Player"


def test_it_survives_unicode():
    assert _name_of(_Named("Inimigo Ç ñ 日本")) == "Inimigo Ç ñ 日本"


def test_an_empty_name_stays_empty():
    assert _name_of(_Named("")) == ""


def test_an_object_without_a_name_yields_empty_not_a_repr():
    class _Anonymous:
        pass

    value = _name_of(_Anonymous())
    assert value == ""
    assert "object at 0x" not in value and "_Anonymous" not in value


def test_it_always_returns_a_string():
    assert isinstance(_name_of(_Named(42)), str)


# ---------------------------------------------------------------------------
# Authoring -> save -> reopen -> runtime
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_type,properties", [
    ("find_nearest_object", {"tag": "Enemy", "max_distance": 42.0}),
    ("get_object_name", {}),
])
def test_save_reopen_preserves_the_contract(
    tmp_path: pathlib.Path, node_type: str, properties: dict
):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "RoundTrip",
        "nodes": [{"id": "n", "type": node_type, "position": [0.0, 0.0],
                   "properties": dict(properties)}],
        "edges": [],
    })
    destination = tmp_path / f"{node_type}.zlogic"
    save_logic_graph(destination, graph)
    reopened = normalize_logic_graph(load_logic_graph(destination))
    assert reopened == graph
    for key, value in properties.items():
        assert reopened["nodes"][0]["properties"][key] == value


def test_the_authored_values_reach_the_runtime_after_a_reopen(tmp_path: pathlib.Path):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Authored",
        "nodes": [{"id": "n", "type": "find_nearest_object", "position": [0.0, 0.0],
                   "properties": {"tag": "Enemy", "max_distance": 15.0}}],
        "edges": [],
    })
    destination = tmp_path / "authored.zlogic"
    save_logic_graph(destination, graph)
    reopened = normalize_logic_graph(load_logic_graph(destination))

    runtime = LogicGraphRuntime(reopened)
    game = _Game(WORLD)
    node = reopened["nodes"][0]
    ports = registry.executors["find_nearest_object"](runtime, node, game, DT)
    evaluate = registry.evaluators["find_nearest_object"]

    # max_distance=15 admits Near (10) and excludes Far (30).
    assert ports == ["exec_found"]
    assert evaluate(runtime, "n", "object", node, game, DT, set()).name == "Near"


# ---------------------------------------------------------------------------
# Mutation: the gate must notice if the runtime disappears again
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_id", ("find_nearest_object", "get_object_name"))
def test_losing_the_runtime_again_makes_the_gap_gate_fail(monkeypatch, node_id: str):
    for table in ("executors", "evaluators"):
        registrations = dict(getattr(registry, table))
        registrations.pop(node_id, None)
        monkeypatch.setattr(registry, table, registrations)
    assert node_id in classify_runtime_coverage()["missing_runtime"]


# ---------------------------------------------------------------------------
# Found on the way, recorded rather than fixed
# ---------------------------------------------------------------------------

def _model(node_id: str) -> str:
    ports = NODE_PORT_DEFINITIONS.get(node_id, {})
    return resolve_execution_model(
        NODE_DEFINITIONS[node_id].get("execution_model"),
        ports.get("inputs", ()), ports.get("outputs", ()),
    )


def test_no_action_node_is_backed_by_an_evaluator_alone():
    """Item 10 recorded this gap; item 11 closed it.

    ``has_runtime`` used to accept an evaluator for an ACTION node, and item
    10's mutation test exposed it: dropping ``find_nearest_object``'s executor
    left it "backed" because the evaluator remained. Applying the model strictly
    found two nodes hiding behind that -- ``find_tag`` and
    ``get_progress_bar_value`` -- and item 11 restored both executors and made
    the classifier consult ``execution_model``.

    Asserted as empty rather than deleted: an ACTION node that loses its
    executor tomorrow fails here, which is the whole reason the check exists.
    """
    strict_gaps = sorted(
        node_id for node_id in NODE_DEFINITIONS
        if not NODE_DEFINITIONS[node_id].get("deprecated", False)
        and _model(node_id) == "action"
        and node_id not in registry.executors
        and node_id in registry.evaluators
    )
    assert strict_gaps == [], strict_gaps


def test_neither_item_10_node_is_among_those():
    for node_id in ("find_nearest_object", "get_object_name"):
        assert node_id in registry.executors or _model(node_id) == "pure_data"
