"""One execution-model vocabulary, declared beating derived.

PHASE 9 recovery item 3.

Two vocabularies existed side by side. The catalogue derived
``pure``/``event``/``terminal``/``branch``/``flow`` from a node's pins, while
the declarative modules declare ``action``/``event_source``/``pure_data``/
``terminal``. Nothing translated between them and **nothing read the declared
value at all**, so a node could declare ``pure_data``, be classified ``pure``,
and no code path would notice the disagreement.

The rule is now: a declaration is intent the pins cannot always carry, so it
wins; derivation is the fallback for everything undeclared. Classification is
structural -- there is no list of node ids anywhere, which is the entire point
of recording the model on the definition.
"""

from __future__ import annotations

import inspect
import re

import pytest

from engine.logic.contracts import (
    CANONICAL_MODELS,
    ExecutionModel,
    derive_execution_model,
    normalize_execution_model,
    resolve_execution_model,
)
from engine.logic.node_definitions import NODE_DEFINITIONS
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
from engine.logic.node_definitions.registry import get_registry
from engine.logic.node_system import classify_runtime_coverage, get_node_system_status


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

def test_the_canonical_vocabulary_is_exactly_four_values():
    assert CANONICAL_MODELS == {"action", "event_source", "pure_data", "terminal"}


def test_every_node_reports_a_canonical_model():
    status = get_node_system_status()
    outside = {
        node_id: model
        for node_id, model in status["execution_models"].items()
        if model not in CANONICAL_MODELS
    }
    assert not outside, f"models outside {sorted(CANONICAL_MODELS)}: {outside}"


@pytest.mark.parametrize("legacy,canonical", [
    ("event", "event_source"),
    ("pure", "pure_data"),
    ("flow", "action"),
    ("branch", "action"),
    ("terminal", "terminal"),
    ("action", "action"),
])
def test_the_old_spellings_normalize_onto_the_canonical_ones(legacy: str, canonical: str):
    assert normalize_execution_model(legacy) == canonical


def test_branch_is_not_a_model_of_its_own():
    """Branching is how an ACTION continues, not a kind of node."""
    assert "branch" not in CANONICAL_MODELS
    assert normalize_execution_model("branch") == ExecutionModel.ACTION.value


def test_an_unset_model_is_none_rather_than_a_default():
    """A default here would make every node look explicitly declared."""
    for value in (None, "", "   "):
        assert normalize_execution_model(value) is None


def test_normalization_is_idempotent():
    for value in list(CANONICAL_MODELS) + ["event", "pure", "flow", "branch"]:
        once = normalize_execution_model(value)
        assert normalize_execution_model(once) == once


# ---------------------------------------------------------------------------
# Declared beats derived
# ---------------------------------------------------------------------------

def test_a_declaration_wins_over_the_pins():
    """restart_scene keeps a flow output and is still TERMINAL."""
    inputs, outputs = [("in", "flow")], [("next", "flow")]
    assert derive_execution_model(inputs, outputs) is ExecutionModel.ACTION
    assert resolve_execution_model("terminal", inputs, outputs) == "terminal"


def test_derivation_is_used_only_when_nothing_is_declared():
    inputs, outputs = [("in", "flow")], [("next", "flow")]
    assert resolve_execution_model(None, inputs, outputs) == "action"
    assert resolve_execution_model("", inputs, outputs) == "action"


@pytest.mark.parametrize("inputs,outputs,expected", [
    ([], [], ExecutionModel.PURE_DATA),
    ([("a", "number")], [("value", "number")], ExecutionModel.PURE_DATA),
    ([], [("next", "flow")], ExecutionModel.EVENT_SOURCE),
    ([("in", "flow")], [], ExecutionModel.TERMINAL),
    ([("in", "flow")], [("next", "flow")], ExecutionModel.ACTION),
    ([("in", "flow")], [("true", "flow"), ("false", "flow")], ExecutionModel.ACTION),
    ([("exec", "exec")], [("next", "exec")], ExecutionModel.ACTION),
])
def test_the_structural_fallback(inputs, outputs, expected):
    assert derive_execution_model(inputs, outputs) is expected


def test_every_declared_model_survives_into_the_registry():
    ensure_catalogue_loaded()
    registry = get_registry()
    declared = {
        node_id: normalize_execution_model(definition.execution_model)
        for node_id, definition in registry.all_canonical().items()
        if getattr(definition, "execution_model", None)
    }
    assert declared, "no node declares a model; this check would be vacuous"
    for node_id, model in declared.items():
        assert registry.execution_model(node_id) == model, (
            f"{node_id} declares {model!r} but the catalogue resolved "
            f"{registry.execution_model(node_id)!r}"
        )


def test_the_declared_model_reaches_the_palette_entry():
    ensure_catalogue_loaded()
    registry = get_registry()
    for node_id, entry in NODE_DEFINITIONS.items():
        assert entry.get("execution_model") == registry.execution_model(node_id), node_id


# ---------------------------------------------------------------------------
# Structural classification, no allow-lists
# ---------------------------------------------------------------------------

def _executable_string_literals(module_or_function) -> set[str]:
    """String literals that are code, not documentation.

    Naming ``event_start`` in a comment or docstring as an *example* is useful;
    naming it in a comparison is the allow-list this item forbids. Only the
    latter is a finding, so docstrings are excluded rather than grepped over.
    """
    import ast
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(module_or_function)))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docstrings.add(doc)
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value not in docstrings
    }


def test_the_classifier_names_no_node_ids():
    """The whole point of recording the model is not needing a list of ids."""
    from engine.logic import contracts
    from engine.logic import node_system

    suspects = ("event_start", "event_update", "on_collision_enter", "animate_value",
                "wait_until_condition", "sequence", "restart_scene")
    for scope in (contracts, node_system.classify_runtime_coverage):
        literals = _executable_string_literals(scope)
        named = sorted(literals & set(suspects))
        assert not named, (
            f"{getattr(scope, '__name__', scope)} compares against node ids {named}; "
            "classification must be structural"
        )


def test_event_sources_are_valid_without_an_executor():
    """The frame loop dispatches them; demanding an executor needs an id list."""
    coverage = classify_runtime_coverage()
    assert coverage["event_source_without_executor"], (
        "no event source lacks an executor; this check would be vacuous"
    )
    registry = get_registry()
    for node_id in coverage["event_source_without_executor"]:
        assert registry.execution_model(node_id) == ExecutionModel.EVENT_SOURCE.value
        assert not NODE_DEFINITIONS[node_id]["inputs"], (
            f"{node_id} is classified EVENT_SOURCE but declares an input pin"
        )


def test_pure_data_nodes_have_no_flow_pins():
    ensure_catalogue_loaded()
    registry = get_registry()
    checked = 0
    for node_id, entry in NODE_DEFINITIONS.items():
        if registry.execution_model(node_id) != ExecutionModel.PURE_DATA.value:
            continue
        if getattr_declared(node_id):
            continue  # a declaration may classify against the pins on purpose
        flow = [p for p in entry["inputs"] + entry["outputs"] if str(p[1]) in ("flow", "exec")]
        assert not flow, f"{node_id} is PURE_DATA but has flow pins {flow}"
        checked += 1
    assert checked, "no derived pure-data node found; this check would be vacuous"


def getattr_declared(node_id: str) -> bool:
    """True when the node's model came from a declaration rather than the pins."""
    ensure_catalogue_loaded()
    definition = get_registry().all_canonical().get(node_id)
    return bool(getattr(definition, "execution_model", None))


def test_terminal_nodes_do_not_continue_unless_they_declare_it():
    ensure_catalogue_loaded()
    registry = get_registry()
    for node_id, entry in NODE_DEFINITIONS.items():
        if registry.execution_model(node_id) != ExecutionModel.TERMINAL.value:
            continue
        if getattr_declared(node_id):
            continue
        flow_out = [p for p in entry["outputs"] if str(p[1]) in ("flow", "exec")]
        assert not flow_out, f"{node_id} is derived TERMINAL but has flow outputs {flow_out}"


def test_action_nodes_have_an_entry_and_a_continuation():
    ensure_catalogue_loaded()
    registry = get_registry()
    checked = 0
    for node_id, entry in NODE_DEFINITIONS.items():
        if registry.execution_model(node_id) != ExecutionModel.ACTION.value:
            continue
        if getattr_declared(node_id):
            continue
        assert [p for p in entry["inputs"] if str(p[1]) in ("flow", "exec")], node_id
        assert [p for p in entry["outputs"] if str(p[1]) in ("flow", "exec")], node_id
        checked += 1
    assert checked > 50, checked


# ---------------------------------------------------------------------------
# Deprecated
# ---------------------------------------------------------------------------

def test_deprecated_nodes_are_recognised_by_the_flag():
    coverage = classify_runtime_coverage()
    assert coverage["deprecated_without_runtime"], "nothing is deprecated; check is vacuous"
    for node_id in coverage["deprecated_without_runtime"]:
        assert NODE_DEFINITIONS[node_id]["deprecated"] is True


def test_the_deprecated_nodes_really_have_no_runtime_and_no_users():
    """The evidence, revalidated rather than inherited."""
    import json
    from pathlib import Path

    from engine.logic.node_system import load_runtime_node_modules
    from engine.logic.runtime.registry import registry as handlers

    load_runtime_node_modules()
    repo_root = Path(__file__).resolve().parents[2]
    uses: dict[str, int] = {}
    for path in repo_root.rglob("*.zlogic"):
        if ".git" in path.parts:
            continue
        for node in json.loads(path.read_text(encoding="utf-8")).get("nodes", []):
            node_type = str(node.get("type", ""))
            uses[node_type] = uses.get(node_type, 0) + 1

    for node_id in classify_runtime_coverage()["deprecated_without_runtime"]:
        assert node_id not in handlers.executors, f"{node_id} has an executor after all"
        assert node_id not in handlers.evaluators, f"{node_id} has an evaluator after all"
        assert uses.get(node_id, 0) == 0, f"{node_id} is used by {uses[node_id]} saved node(s)"


def test_a_node_with_a_runtime_is_never_reported_as_missing():
    coverage = classify_runtime_coverage()
    overlap = set(coverage["backed"]) & set(coverage["missing_runtime"])
    assert not overlap, overlap
    everything = sum(len(group) for group in coverage.values())
    assert everything == len(NODE_DEFINITIONS), "the classification lost or duplicated a node"


def test_no_declared_node_is_left_without_a_runtime():
    """There is no longer any node declaring a contract nothing implements.

    This recorded two gaps when item 3 wrote it: ``find_nearest_object`` and
    ``get_object_name`` arrived with Stage 1's scene_nodes while their runtime
    stayed on the Stage 1 lineage, which is not an ancestor of this branch.
    Recovery item 10 restored both from that lineage -- the contracts were
    byte-identical, so nothing was invented -- and the set is now empty.

    Asserted as empty rather than deleted: a node added tomorrow with no runtime
    fails here, which is the whole reason the check existed.
    """
    assert classify_runtime_coverage()["missing_runtime"] == []
