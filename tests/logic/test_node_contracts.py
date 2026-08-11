"""Phase 9.5B Stage 1 — the node contract is enforced, not merely audited.

ONE NODE ID -> ONE DEFINITION -> ONE PORT CONTRACT -> ONE RUNTIME CONTRACT
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Stage 1 exit criterion.  This list may only ever SHRINK.
#
# Both entries are deprecated nodes with no runtime handler at all.  They are
# hidden from the palette, so an author cannot reach them; implementing them
# would be new gameplay feature work, explicitly out of Stage 1 scope.
# ---------------------------------------------------------------------------
ALLOWED_VIOLATION_KINDS = {
    "DEPRECATED_NO_RUNTIME": 2,
}


@pytest.fixture(scope="module")
def audit() -> dict:
    """Run the read-only audit tool and return its machine-readable report."""
    out = ROOT / "tests" / "fixtures" / "stage1" / "_audit_current.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit_node_system.py"),
         "--json", str(out)],
        capture_output=True, text=True, cwd=str(ROOT), timeout=300,
    )
    assert out.exists(), f"audit tool produced no report:\n{proc.stdout}\n{proc.stderr}"
    return json.loads(out.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ contracts
def test_no_unexpected_contract_violations(audit):
    counts = {}
    for v in audit["violations"]:
        counts[v["kind"]] = counts.get(v["kind"], 0) + 1

    unexpected = {k: n for k, n in counts.items() if k not in ALLOWED_VIOLATION_KINDS}
    assert not unexpected, (
        "New node contract violations introduced:\n"
        + "\n".join(f"  [{v['kind']}] {v['node']}: {v['detail']}"
                    for v in audit["violations"]
                    if v["kind"] in unexpected)
    )


def test_allow_list_only_shrinks(audit):
    counts = {}
    for v in audit["violations"]:
        counts[v["kind"]] = counts.get(v["kind"], 0) + 1
    for kind, allowed in ALLOWED_VIOLATION_KINDS.items():
        actual = counts.get(kind, 0)
        assert actual <= allowed, (
            f"{kind} grew from {allowed} to {actual}; the Stage 1 allow-list "
            f"must only ever shrink."
        )


@pytest.mark.parametrize("kind", [
    "EXEC_PORT_MISMATCH",
    "UNREACHABLE_EXEC_PORT",
    "NO_DEFINITION",
    "DATA_PORT_MISMATCH",
    "INPUT_PORT_MISMATCH",
    "NO_RUNTIME",
])
def test_stage1_violation_class_is_eliminated(audit, kind):
    """Each of the six Phase 9.5A classes must be at zero."""
    offenders = [v for v in audit["violations"] if v["kind"] == kind]
    assert not offenders, (
        f"{kind} regressed:\n"
        + "\n".join(f"  {v['node']}: {v['detail']}" for v in offenders)
    )


# ------------------------------------------------------------------ the API
def test_validator_flags_a_returned_port_that_is_not_declared():
    from engine.logic.contracts import (
        DefinitionContract, RuntimeContract, validate_node_contract)

    d = DefinitionContract("probe", outputs=[("next", "flow")])
    r = RuntimeContract("probe", returns={"surprise"}, has_executor=True)
    kinds = {v.kind for v in validate_node_contract(d, r)}
    assert "EXEC_PORT_MISMATCH" in kinds


def test_validator_flags_a_declared_port_that_is_never_returned():
    from engine.logic.contracts import (
        DefinitionContract, RuntimeContract, validate_node_contract)

    d = DefinitionContract("probe", outputs=[("next", "flow"), ("ghost", "flow")])
    r = RuntimeContract("probe", returns={"next"}, has_executor=True)
    kinds = {v.kind for v in validate_node_contract(d, r)}
    assert "UNREACHABLE_EXEC_PORT" in kinds


def test_validator_accepts_matching_contract():
    from engine.logic.contracts import (
        DefinitionContract, RuntimeContract, validate_node_contract)

    d = DefinitionContract(
        "probe",
        inputs=[("exec", "flow"), ("amount", "number")],
        outputs=[("next", "flow"), ("result", "number")],
    )
    r = RuntimeContract("probe", reads={"amount"}, stores={"result"},
                        returns={"next"}, has_executor=True)
    assert validate_node_contract(d, r) == []


def test_event_source_needs_no_runtime_handler():
    from engine.logic.contracts import (
        DefinitionContract, ExecutionModel, validate_node_contract)

    d = DefinitionContract("event_start", outputs=[("next", "flow")],
                           execution_model=ExecutionModel.EVENT_SOURCE)
    assert validate_node_contract(d, None) == []


def test_plain_action_without_runtime_is_a_violation():
    from engine.logic.contracts import DefinitionContract, validate_node_contract

    d = DefinitionContract("orphan", outputs=[("next", "flow")])
    assert [v.kind for v in validate_node_contract(d, None)] == ["NO_RUNTIME"]


def test_dynamic_port_family_is_accepted():
    """`sequence` returns then_0..then_N built from a property."""
    from engine.logic.contracts import (
        DefinitionContract, RuntimeContract, validate_node_contract)

    d = DefinitionContract(
        "sequence",
        outputs=[("then_0", "flow"), ("then_1", "flow"), ("next", "flow")],
        dynamic_prefixes=("then_",),
    )
    r = RuntimeContract("sequence", returns={"next"}, dynamic={"then_"},
                        has_executor=True)
    assert validate_node_contract(d, r) == []


# ------------------------------------------------------- structural guarantees
def test_every_executor_id_resolves_to_a_definition():
    """No runtime handler may be invisible in the palette."""
    from engine.logic.node_definitions import NODE_DEFINITIONS
    from engine.logic.port_aliases import canonical_node_id
    from engine.logic.runtime.registry import registry
    import engine.logic.provider  # noqa: F401  (imports every runtime module)

    for module in (
        "actions_nodes", "components_nodes", "event_nodes", "flow_nodes",
        "math_nodes", "misc_nodes", "movement_nodes", "prefab_nodes",
        "scene_nodes", "string_nodes", "dynamic_ui_nodes", "animation_nodes",
        "physics_nodes", "dialog_nodes", "audio_advanced_nodes",
        "particle_nodes", "camera_nodes", "state_machine_nodes",
        "save_load_nodes", "pathfinding_nodes", "input_advanced_nodes",
        "ui_binding_nodes", "ui_nodes",
    ):
        __import__(f"engine.logic.runtime.nodes.{module}")

    missing = sorted(
        nid for nid in set(registry.executors) | set(registry.evaluators)
        if canonical_node_id(nid) not in NODE_DEFINITIONS
    )
    assert not missing, f"runtime handlers with no definition: {missing}"


def test_math_and_logic_nodes_are_authorable():
    """The biggest authoring gap found in Phase 9.5A."""
    from engine.logic.node_definitions import NODE_DEFINITIONS

    for node_id in ("add_number", "subtract_number", "multiply_number",
                    "divide_number", "clamp_number", "absolute_number",
                    "random_number", "and", "or", "not",
                    "join_text", "to_text"):
        assert node_id in NODE_DEFINITIONS, f"{node_id} is still not in the palette"
        entry = NODE_DEFINITIONS[node_id]
        assert entry["outputs"], f"{node_id} declares no output"
