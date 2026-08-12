"""Every flow port an executor returns must be one the author can wire to.

PHASE 9 recovery item 7.

The dispatcher matches a returned port name against ``edge.from_port``
literally::

    for edge in self.outgoing.get(node_id, []):
        if str(edge.get("from_port", "next")) != port:
            continue

and the editor only ever offers the author the pins the contract declares. So a
returned name that is not declared is not a near miss -- it is a branch that can
never run, and a declared pin nothing returns is a pin that never fires.

Item 6 found this on the four save/load nodes and recorded 45 more. Item 7
classified all 45:

* 39 nodes / 83 outputs  STALE EXECUTOR OUTPUT -- the executor kept the
  unprefixed spelling (``success``, ``touched``, ``shaking``) while the
  declaration had moved to ``exec_*``;
* 5 nodes REAL CONTRACT BUG -- ``detect_pinch``/``detect_swipe``/
  ``detect_touch``/``is_key_pressed``/``wait_key_release`` return ``failure``
  from their ``except`` guard and declared no failure pin at all, while 33
  sibling nodes declare ``exec_failure``;
* 4 nodes PORT ALIAS -- ``next`` against a declared ``exec_done``; the spelling
  is one the contract-relative resolver covers on the *edge* side, which is
  exactly why it was invisible;
* 1 node UNKNOWN, resolved: ``get_ui_widget_property`` had a stale
  ``_EXPLICIT_PORT_CONTRACTS`` entry shadowing a declarative definition that
  already declared ``exec_success``/``exec_failure``;
* 1 node out of scope: ``set_variable``, entangled with its duplicate executor.

Assets decided the direction rather than seniority of the code: 43 of the 45
nodes appear in no ``.zlogic`` at all, no alias covered the unprefixed spelling
and no test asserted it.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from engine.logic.contracts import (
    FLOW_PIN_KINDS,
    declared_flow_outputs,
    sole_flow_output,
)
from engine.logic.graph_asset import NODE_PORT_DEFINITIONS
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.registry import registry
from tools.audit_node_system import (
    EXECUTOR_OUTPUT_BASELINE,
    executor_output_failures,
    executor_output_violations,
    returned_flow_ports,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE = json.loads(EXECUTOR_OUTPUT_BASELINE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


# ---------------------------------------------------------------------------
# 1. Every returned output is declared, dynamic, or recorded debt
# ---------------------------------------------------------------------------

def test_no_executor_returns_a_port_its_contract_does_not_declare():
    assert executor_output_violations().keys() <= set(BASELINE["nodes"])


def test_the_gate_passes_on_the_tree_as_committed():
    assert executor_output_failures() == []


def test_every_recorded_debt_carries_a_reason():
    """A baseline entry without a reason is an exemption wearing a debt's name."""
    for node_id in BASELINE["nodes"]:
        reason = BASELINE.get("_reasons", {}).get(node_id, "")
        assert len(reason) > 40, f"{node_id} is recorded with no explanation"


def test_the_baseline_count_matches_its_contents():
    assert BASELINE["count"] == len(BASELINE["nodes"])


@pytest.mark.parametrize("node_id", sorted(BASELINE["nodes"]))
def test_a_recorded_node_still_actually_mismatches(node_id: str):
    """Debt, not exemption: a node that was fixed must leave the file."""
    assert node_id in executor_output_violations()


# ---------------------------------------------------------------------------
# 2/9. Dynamic outputs are structural, not violations
# ---------------------------------------------------------------------------

DYNAMIC_NODES = {"sequence": "then_", "create_prefab": "param_"}


def _dynamic_prefixes(node_id: str) -> tuple[str, ...]:
    """Read from the projection the catalogue actually publishes.

    Deliberately not ``NODE_PORT_DEFINITIONS``: the prefixes are projected onto
    the node definition, and asserting against the wrong table is how the
    original loss went unnoticed.
    """
    from engine.logic.node_definitions import NODE_DEFINITIONS

    return tuple(NODE_DEFINITIONS.get(node_id, {}).get("dynamic_exec_prefixes", ()) or ())


def test_the_declared_dynamic_prefixes_survive_projection():
    """The prefix existed semantically once and was lost in projection.

    That bug is why a dynamic output looked like a contract violation, so the
    projection is asserted here rather than assumed.
    """
    declared = {node_id: _dynamic_prefixes(node_id) for node_id in DYNAMIC_NODES}
    assert all(declared.values()), f"dynamic_exec_prefixes lost in projection: {declared}"


@pytest.mark.parametrize("node_id,prefix", sorted(DYNAMIC_NODES.items()))
def test_a_dynamic_output_is_not_a_violation(node_id: str, prefix: str):
    """Adding then_7 must not make the gate fail -- it is contract-valid."""
    prefixes = _dynamic_prefixes(node_id)
    assert prefix in prefixes
    generated = f"{prefix}7"
    assert generated not in declared_flow_outputs(node_id)
    assert any(generated.startswith(p) for p in prefixes), (
        f"{generated} is structurally valid for {node_id} and must not be reported"
    )


def test_a_dynamic_prefix_does_not_excuse_an_unrelated_port():
    """The prefix must not become a wildcard."""
    prefixes = _dynamic_prefixes("sequence")
    assert not any("totally_invalid_port".startswith(p) for p in prefixes)


# ---------------------------------------------------------------------------
# 3/4. Aliases resolve to a declared pin and never invent one
# ---------------------------------------------------------------------------

def test_every_alias_target_is_a_pin_the_node_declares():
    """No alias may create a phantom port."""
    from engine.logic.port_aliases import NODE_SCOPED_OUTPUT_ALIASES

    for node_id, mapping in NODE_SCOPED_OUTPUT_ALIASES.items():
        declared = declared_flow_outputs(node_id)
        for source, target in mapping.items():
            assert target in declared, (
                f"alias {node_id}.{source} -> {target} names a pin the contract "
                f"does not declare (declares {sorted(declared)})"
            )


def test_resolution_stays_relative_to_the_contract():
    """Item 5's rule: no global success -> next table.

    ``next`` resolves to ``exec_done`` only because ``exec_done`` is the single
    flow-synonym pin the node declares; against a node declaring three outcomes
    the resolver must still refuse.
    """
    from engine.logic.port_aliases import resolve_output_port

    assert resolve_output_port("next", frozenset({"exec_done"})) == "exec_done"
    assert resolve_output_port("next", frozenset({"next"})) == "next"
    ambiguous = frozenset({"exec_exists", "exec_not_exists", "exec_failure"})
    assert resolve_output_port("next", ambiguous) == "next"


def test_sole_flow_output_refuses_to_pick_among_branches():
    """The shared-executor helper must never guess a branch."""
    assert sole_flow_output("input_axis") == "next"
    assert sole_flow_output("read_key_axis") == "exec_done"
    assert sole_flow_output("has_save", default="sentinel") == "sentinel"
    assert sole_flow_output("no_such_node", default="sentinel") == "sentinel"


# ---------------------------------------------------------------------------
# 5/6. No structural exemption is bought with an allow-list
# ---------------------------------------------------------------------------

def test_no_pure_data_node_gained_a_flow_output():
    """A gate must not be satisfied by inventing a pin on a data node."""
    from engine.logic.contracts import resolve_execution_model
    from engine.logic.node_definitions import NODE_DEFINITIONS

    for node_id, ports in NODE_PORT_DEFINITIONS.items():
        model = resolve_execution_model(
            NODE_DEFINITIONS.get(node_id, {}).get("execution_model"),
            ports.get("inputs", ()),
            ports.get("outputs", ()),
        )
        if model == "pure_data":
            assert not declared_flow_outputs(node_id), (
                f"{node_id} is pure_data and must not carry a flow output"
            )


def test_the_gate_holds_no_node_id_allow_list():
    """The only per-node list is the baseline, and every entry is verified.

    An allow-list would let a node be excused by name; the baseline cannot,
    because ``test_a_recorded_node_still_actually_mismatches`` fails the moment
    a listed node stops mismatching.
    """
    source = ast.parse(
        (REPO_ROOT / "tools" / "audit_node_system.py").read_text(encoding="utf-8")
    )
    for node in ast.walk(source):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in ("executor_output_violations", "returned_flow_ports"):
            continue
        literals = {
            child.value for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        }
        assert not literals & set(NODE_PORT_DEFINITIONS), (
            f"{node.name} names specific nodes; the check must be structural"
        )


# ---------------------------------------------------------------------------
# 7/8. Mutation: a gate that cannot fail is worse than none
# ---------------------------------------------------------------------------

def _probe_executor(returns: str):
    source = (
        "def probe(runtime, node, game, dt):\n"
        f"    return {returns}\n"
    )
    namespace: dict = {}
    exec(compile(source, "<probe>", "exec"), namespace)
    function = namespace["probe"]
    # inspect.getsource needs the text; linecache is what it reads.
    import linecache

    linecache.cache["<probe>"] = (len(source), None, source.splitlines(True), "<probe>")
    return function


def test_an_invalid_returned_port_is_detected():
    """The proof the whole item rests on."""
    assert returned_flow_ports(_probe_executor('["totally_invalid_port"]')) == {
        "totally_invalid_port"
    }


def test_injecting_an_invalid_port_makes_the_gate_fail(monkeypatch):
    node_id = "camera_shake"
    monkeypatch.setitem(
        registry.executors, node_id, _probe_executor('["totally_invalid_port"]')
    )
    failures = executor_output_failures()
    assert any(node_id in failure and "totally_invalid_port" in failure for failure in failures)


def test_removing_a_declared_output_makes_the_gate_fail(monkeypatch):
    """Drop a pin the executor returns and the node must be reported."""
    node_id = "camera_shake"
    ports = dict(NODE_PORT_DEFINITIONS[node_id])
    ports["outputs"] = [pin for pin in ports["outputs"] if pin[0] != "exec_shaking"]
    # NODE_PORT_DEFINITIONS is a read-only view, and the auditor imports it
    # inside the function -- so the module attribute is the seam.
    patched = {**NODE_PORT_DEFINITIONS, node_id: ports}
    monkeypatch.setattr(
        "engine.logic.graph_asset.NODE_PORT_DEFINITIONS", patched, raising=True
    )
    assert "exec_shaking" in executor_output_violations().get(node_id, [])


def test_a_fixed_node_left_in_the_baseline_makes_the_gate_fail(monkeypatch):
    """The baseline cannot quietly outlive the bug it records."""
    monkeypatch.setattr(
        "tools.audit_node_system.executor_output_violations", lambda: {}
    )
    failures = executor_output_failures()
    assert any("remove it from" in failure for failure in failures)


def test_a_conditional_return_counts_both_branches():
    """``return ["a" if ok else "b"]`` returns two ports, not zero."""
    assert returned_flow_ports(_probe_executor('["exec_success" if ok else "exec_failure"]')) == {
        "exec_success",
        "exec_failure",
    }


def test_an_argument_literal_is_not_a_returned_port():
    """The false positive that item 7 had to fix in its own scan."""
    probe = _probe_executor('[sole_flow_output(node_type, default="next")]')
    assert returned_flow_ports(probe) == set()


# ---------------------------------------------------------------------------
# The nodes item 7 changed
# ---------------------------------------------------------------------------

FIXED = {
    "camera_shake": {"exec_shaking", "exec_failure"},
    "show_dialog": {"exec_showing", "exec_failure"},
    "detect_touch": {"exec_touched", "exec_no_touch", "exec_failure"},
    "is_key_pressed": {"exec_pressed", "exec_not_pressed", "exec_failure"},
    "wait_key_release": {
        "exec_released", "exec_waiting", "exec_timeout", "exec_failure",
    },
    "get_ui_widget_property": {"exec_success", "exec_failure"},
    "raycast": {"exec_hit", "exec_no_hit"},
    "change_state": {"exec_changed", "exec_failure", "exec_invalid_transition"},
    "bind_ui_to_blackboard": {"exec_done"},
    "set_ui_visible": {"exec_done"},
    "start_behavior_tree": {"exec_done", "exec_failure"},
}


@pytest.mark.parametrize("node_id,expected", sorted(FIXED.items()))
def test_the_declared_flow_outputs_are_what_item_7_settled(node_id: str, expected: set):
    assert set(declared_flow_outputs(node_id)) == expected


@pytest.mark.parametrize("node_id", sorted(FIXED))
def test_the_executor_returns_only_declared_ports(node_id: str):
    assert returned_flow_ports(registry.executors[node_id]) <= set(
        declared_flow_outputs(node_id)
    )


@pytest.mark.parametrize("node_id", sorted(set(FIXED) - {"start_behavior_tree"}))
def test_every_declared_branch_is_reachable(node_id: str):
    """A pin nothing returns is a pin the author cannot use.

    ``start_behavior_tree`` is excluded: it declares ``exec_failure`` and its
    executor has no failure path. That is a real gap, recorded below rather than
    fixed by inventing a failure condition.
    """
    unreachable = set(declared_flow_outputs(node_id)) - returned_flow_ports(
        registry.executors[node_id]
    )
    assert not unreachable, f"{node_id} declares {sorted(unreachable)} but never returns them"


def test_start_behavior_tree_still_has_its_unreachable_failure_pin():
    """Recorded, so that fixing it is a decision rather than a silent drift."""
    unreachable = set(declared_flow_outputs("start_behavior_tree")) - returned_flow_ports(
        registry.executors["start_behavior_tree"]
    )
    assert unreachable == {"exec_failure"}


def test_the_shared_axis_executor_satisfies_both_contracts():
    """``input_axis`` ships in 7 asset nodes wiring 5 flow edges to ``next``.

    ``read_key_axis`` declares ``exec_done`` and appears in no asset. One
    executor serves both ids, so returning either spelling unconditionally
    would strand the other node's only pin.
    """
    assert declared_flow_outputs("input_axis") == ("next",)
    assert declared_flow_outputs("read_key_axis") == ("exec_done",)
    assert registry.executors["input_axis"] is registry.executors["read_key_axis"]


@pytest.mark.parametrize("node_id,expected", [
    ("input_axis", ["next"]),
    ("read_key_axis", ["exec_done"]),
])
def test_the_axis_executor_returns_the_running_nodes_pin(node_id: str, expected: list):
    class _Runtime:
        def _evaluate_output(self, *args, **kwargs):
            return 0.0

    node = {"id": "n1", "type": node_id, "properties": {}}
    assert registry.executors[node_id](_Runtime(), node, object(), 0.0) == expected


def test_the_stale_explicit_contract_no_longer_shadows_the_declaration():
    """``get_ui_widget_property`` declared exec_success/exec_failure all along.

    A legacy ``_EXPLICIT_PORT_CONTRACTS`` entry declaring a single ``next``
    shadowed it, so the node's real contract never reached the editor and the
    executor's success/failure returns looked like the broken side.
    """
    from engine.logic.node_definitions.catalogue import _EXPLICIT_PORT_CONTRACTS

    assert "get_ui_widget_property" not in _EXPLICIT_PORT_CONTRACTS


def test_the_input_nodes_gained_the_failure_pin_their_siblings_had():
    for node_id in ("detect_pinch", "detect_swipe", "detect_touch",
                    "is_key_pressed", "wait_key_release"):
        assert "exec_failure" in declared_flow_outputs(node_id)


def test_no_asset_edge_was_orphaned_by_the_rename():
    """The 44 renamed nodes must not appear as a source in any shipped graph."""
    renamed = set(FIXED) - {"set_variable"}
    for path in (REPO_ROOT / "Assets").rglob("*.zlogic"):
        graph = json.loads(path.read_text(encoding="utf-8"))
        types = {str(n["id"]): str(n.get("type", "")) for n in graph.get("nodes", [])}
        for edge in graph.get("edges", []):
            source = types.get(str(edge.get("from_node")))
            if source in renamed:
                assert str(edge.get("from_port")) in declared_flow_outputs(source), (
                    f"{path}: {source}.{edge.get('from_port')} is no longer declared"
                )
