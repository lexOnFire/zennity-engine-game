"""``set_variable``: one definition, one executor, one contract, one identity.

PHASE 9 recovery item 8.

This node carried every kind of split the phase has been unpicking, at once:

* **two executors** -- ``misc_nodes`` and ``scene_nodes`` both registered one,
  and the winner was decided by load order;
* **a shadowed contract** -- the declaration in ``misc_nodes`` said
  ``exec_done``, while a ``_EXPLICIT_PORT_CONTRACTS`` entry silently overrode it
  with ``next``, so the file describing the node never described the node the
  editor showed;
* **an undeclared runtime output** -- the winning executor returned
  ``["done", "next"]``, and ``done`` was a branch no editor could wire;
* **a node id that resolved nowhere** -- ``variable.set``, used by 10 nodes
  across 8 shipping assets, sat in ``LEGACY_NODE_TYPES`` but not in
  ``NODE_ID_ALIASES``. ``all_aliases()`` merges both tables and reported it as
  an alias; ``resolve_node_id``, which the normalizer actually calls, reads only
  the second. So the graphs loaded, the flow continued on ``["next"]`` from the
  default branch of ``_execute`` -- and the variable was never written.

The evidence, not seniority, settled each one. The shipping assets wire 12 flow
edges to ``next`` and none to any other spelling; no test asserts a port name
here at all; and the two executors are not a semantic split -- both write the
blackboard identically, with ``scene_nodes`` additionally calling the optional
``game.set_variable`` host hook that a public-contract test already pins.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    declared_flow_outputs,
    load_logic_graph,
    normalize_logic_graph,
)
from engine.logic.node_definitions import definition_owner
from engine.logic.node_definitions.catalogue import (
    NODE_ID_ALIASES,
    all_aliases,
    ensure_catalogue_loaded,
    resolve_node_id,
)
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.registry import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_IDS = ("variable.set", "variables.set")


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


# ---------------------------------------------------------------------------
# 1-3. One owner, one executor, no second declaration
# ---------------------------------------------------------------------------

def test_there_is_exactly_one_definition_owner():
    assert definition_owner("set_variable") == "misc_nodes"


def test_there_is_exactly_one_executor_and_scene_nodes_owns_it():
    """scene_nodes is a strict superset of what misc_nodes implemented.

    Same blackboard write, plus the optional ``game.set_variable`` hook that
    ``test_set_variable_uses_the_authored_name`` pins. Picking the other body
    would have dropped that hook.
    """
    assert registry.executors["set_variable"].__module__ == (
        "engine.logic.runtime.nodes.scene_nodes"
    )


def test_misc_nodes_no_longer_registers_a_competing_executor():
    import engine.logic.runtime.nodes.misc_nodes as misc

    source = Path(misc.__file__).read_text(encoding="utf-8")
    assert "register_executor('set_variable')" not in source
    assert 'register_executor("set_variable")' not in source


def test_the_node_has_no_duplicate_owner_left():
    duplicated = {
        key: owners for key, owners in registry.duplicate_owners().items()
        if key.endswith(":set_variable")
    }
    assert not duplicated, duplicated


def test_set_variable_is_not_in_the_known_duplicate_debt():
    """It was resolved, so it must not keep a seat in the debt list."""
    from engine.logic.node_system import KNOWN_DUPLICATE_OWNERS

    assert "executor:set_variable" not in KNOWN_DUPLICATE_OWNERS


# ---------------------------------------------------------------------------
# 4-5. One contract, and the executor honours it
# ---------------------------------------------------------------------------

def test_the_canonical_flow_output_is_next():
    assert declared_flow_outputs("set_variable") == ("next",)


def test_the_declaration_and_the_effective_contract_agree():
    """The shadowing is what made this node undebuggable -- assert it is gone."""
    assert [tuple(pin) for pin in NODE_DEFINITIONS["set_variable"]["outputs"]] == [
        tuple(pin) for pin in NODE_PORT_DEFINITIONS["set_variable"]["outputs"]
    ]


def test_the_explicit_port_contract_override_is_gone():
    from engine.logic.node_definitions.catalogue import _EXPLICIT_PORT_CONTRACTS

    assert "set_variable" not in _EXPLICIT_PORT_CONTRACTS


def test_the_executor_returns_only_declared_ports():
    from tools.audit_node_system import returned_flow_ports

    returned = returned_flow_ports(registry.executors["set_variable"])
    assert returned <= set(declared_flow_outputs("set_variable"))
    assert "done" not in returned


def test_every_declared_branch_is_reachable():
    from tools.audit_node_system import returned_flow_ports

    unreachable = set(declared_flow_outputs("set_variable")) - returned_flow_ports(
        registry.executors["set_variable"]
    )
    assert not unreachable


def test_no_phantom_value_output():
    """It was declared and nothing evaluated it -- a pin no author could read."""
    assert "value" not in {
        name for name, _kind in NODE_PORT_DEFINITIONS["set_variable"]["outputs"]
    }
    assert "set_variable" not in registry.evaluators


# ---------------------------------------------------------------------------
# 7/9. One authoring identity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("legacy", LEGACY_IDS)
def test_the_legacy_ids_resolve_to_the_canonical_one(legacy: str):
    assert resolve_node_id(legacy) == "set_variable"
    assert legacy in NODE_ID_ALIASES


@pytest.mark.parametrize("legacy", LEGACY_IDS)
def test_a_legacy_id_is_not_a_second_palette_entry(legacy: str):
    """The regression that matters for the editor: one authorable row."""
    assert legacy not in NODE_DEFINITIONS
    assert legacy not in NODE_PORT_DEFINITIONS


def test_the_palette_holds_exactly_one_set_variable_entry():
    entries = [
        node_id for node_id in NODE_DEFINITIONS
        if resolve_node_id(node_id) == "set_variable"
    ]
    assert entries == ["set_variable"]


def test_the_two_alias_tables_agree_about_this_node():
    """``variable.set`` was in one table and not the other, so it never resolved.

    ``all_aliases()`` merges LEGACY_NODE_TYPES with NODE_ID_ALIASES for
    diagnostics, while ``resolve_node_id`` reads only the latter -- the node
    looked aliased and was not.
    """
    reported = set(all_aliases().get("set_variable", ()))
    assert set(LEGACY_IDS) <= reported
    for legacy in reported:
        assert resolve_node_id(legacy) == "set_variable", (
            f"{legacy} is reported as an alias but does not resolve"
        )


# ---------------------------------------------------------------------------
# 6. The shipping assets keep working, unedited
# ---------------------------------------------------------------------------

SHIPPING = sorted((REPO_ROOT / "Assets").rglob("*.zlogic"))


def test_every_asset_set_variable_node_resolves_and_has_a_contract():
    seen = 0
    for path in SHIPPING:
        graph = normalize_logic_graph(load_logic_graph(path))
        for node in graph["nodes"]:
            if str(node["type"]) == "set_variable":
                seen += 1
                assert "set_variable" in NODE_PORT_DEFINITIONS
    assert seen >= 24, f"expected the 24 recorded instances, found {seen}"


def test_no_asset_edge_on_set_variable_is_orphaned():
    from engine.logic.graph_asset import node_port_definitions

    for path in SHIPPING:
        graph = normalize_logic_graph(load_logic_graph(path))
        nodes = {str(n["id"]): n for n in graph["nodes"]}
        for edge in graph["edges"]:
            source = nodes.get(str(edge.get("from_node")))
            if source and str(source["type"]) == "set_variable":
                assert str(edge["from_port"]) in {
                    name for name, _k in node_port_definitions(source)["outputs"]
                }, f"{path.name}: {edge}"


def test_the_assets_were_not_edited():
    """Compatibility belongs in the engine, never in the saved graphs."""
    import subprocess

    changed = subprocess.run(
        ["git", "status", "--porcelain", "--", "Assets"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert not changed, f"assets modified: {changed}"


# ---------------------------------------------------------------------------
# End to end: the legacy id all the way to the variable being written
# ---------------------------------------------------------------------------

class _SpyGame:
    def __init__(self):
        self.variables: dict = {}

    def set_variable(self, name, value):
        self.variables[name] = value


@pytest.mark.parametrize("node_type", ("variable.set", "variables.set", "set_variable"))
def test_a_legacy_node_writes_the_variable_end_to_end(node_type: str):
    """The bug this item fixed, proven through the real load path.

    ``variable.set`` previously loaded, continued the flow on the default
    ``["next"]`` of ``_execute`` -- and wrote nothing at all.
    """
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "LegacySetVariable",
        "nodes": [
            {"id": "ev", "type": "event_start", "position": [0.0, 0.0]},
            {"id": "sv", "type": node_type, "position": [1.0, 0.0],
             "properties": {"name": "hp", "value": 42, "scope": "object"}},
        ],
        "edges": [{"from_node": "ev", "from_port": "next",
                   "to_node": "sv", "to_port": "in", "kind": "flow"}],
    })
    assert graph["nodes"][1]["type"] == "set_variable"

    runtime = LogicGraphRuntime(graph)
    game = _SpyGame()
    runtime.update(game, 1.0 / 60.0)
    runtime.stop()

    assert game.variables.get("hp") == 42, (
        f"{node_type} did not reach game.set_variable; got {game.variables}"
    )
    assert runtime.variables.get("hp") == pytest.approx(42.0)


def test_the_executor_continues_the_flow_on_the_declared_port():
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "SetVariableFlow",
        "nodes": [{"id": "sv", "type": "set_variable", "position": [0.0, 0.0],
                   "properties": {"name": "hp", "value": 1, "scope": "object"}}],
        "edges": [],
    })
    runtime = LogicGraphRuntime(graph)
    node = graph["nodes"][0]
    assert registry.executors["set_variable"](
        runtime, node, _SpyGame(), 1.0 / 60.0
    ) == ["next"]


# ---------------------------------------------------------------------------
# 10-12. The gates cannot be satisfied by an exemption
# ---------------------------------------------------------------------------

def test_the_audit_needs_no_special_case_for_this_node():
    from tools.audit_node_system import executor_output_failures, executor_output_violations

    assert "set_variable" not in executor_output_violations()
    assert executor_output_failures() == []


def test_the_executor_output_debt_is_now_empty():
    """45 at item 6, 1 at item 7, 0 here."""
    recorded = json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "stage2"
         / "executor_port_mismatch_baseline.json").read_text(encoding="utf-8")
    )
    assert recorded["nodes"] == {}
    assert recorded["count"] == 0


def test_a_second_definition_makes_the_duplicate_gate_fail(monkeypatch):
    """Mutation: the detector must still see a competitor."""
    from engine.logic.node_definitions.registry import get_registry

    registry_object = get_registry()
    assert not [
        conflict for conflict in registry_object.definition_conflicts()
        if conflict[0] == "set_variable"
    ], "set_variable still has a recorded definition conflict"

    # Claim the id from a second module and the detector must record it.
    registry_object.set_definition_owner("set_variable", "a_second_module")
    try:
        conflicts = [
            conflict for conflict in registry_object.definition_conflicts()
            if conflict[0] == "set_variable"
        ]
        assert conflicts, "the duplicate detector stopped seeing a competitor"
    finally:
        registry_object._definition_conflicts[:] = [
            conflict for conflict in registry_object._definition_conflicts
            if conflict[0] != "set_variable"
        ]


def test_an_invalid_runtime_output_makes_the_item_7_gate_fail(monkeypatch):
    """Mutation: reintroduce ``done`` and the executor-output gate must fail."""
    from tools import audit_node_system

    def _probe(runtime, node, game, dt):
        return ["done", "next"]

    monkeypatch.setitem(registry.executors, "set_variable", _probe)
    import linecache

    source = 'def _probe(runtime, node, game, dt):\n    return ["done", "next"]\n'
    linecache.cache[audit_node_system.__file__] = linecache.cache.get(
        audit_node_system.__file__, (0, None, [], "")
    )
    violations = audit_node_system.executor_output_violations()
    assert violations.get("set_variable") == ["done"]
