"""Runtime coverage must mean what ``ExecutionModel`` says it means.

PHASE 9 recovery item 11.

``classify_runtime_coverage`` decided coverage with::

    has_runtime = node_id in executors or node_id in evaluators

checked *before* the model was consulted. That is not a definition of coverage,
it is a definition of *something exists*. An ACTION node declares flow pins and
only an executor can return them, so an evaluator satisfied the check while the
node's flow stayed unbacked -- and the model, which the whole classifier was
built around, never got a say.

Item 10's mutation test exposed it: dropping ``find_nearest_object``'s executor
left the node "backed" because its evaluator remained.

Applying the model strictly found exactly two nodes hiding behind it, both real:

* ``find_tag`` -- flow ``in``/``next`` plus an ``object`` output, evaluator only;
* ``get_progress_bar_value`` -- flow ``in``/``next`` plus a ``value`` output,
  evaluator only.

Neither was visibly broken, which is why they survived: ``_execute`` returns
``["next"]`` when no executor is registered, and ``next`` is exactly what both
declare, so the flow continued by coincidence. Both executors exist on lineages
that are not ancestors of this branch and were restored from there.

The rule is structural. No node id appears in it, so a node added tomorrow is
judged by the contract it declares.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from engine.logic.contracts import ExecutionModel
from engine.logic.node_definitions import definitions_view
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
from engine.logic.node_definitions.registry import get_registry
from engine.logic.node_system import (
    _runtime_required,
    classify_runtime_coverage,
    load_runtime_node_modules,
)
from engine.logic.runtime.registry import registry

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


def _model(node_id: str) -> str:
    return get_registry().execution_model(node_id)


# ---------------------------------------------------------------------------
# 1-3. The rule each model imposes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model,expected", [
    (ExecutionModel.ACTION.value, "executors"),
    (ExecutionModel.TERMINAL.value, "executors"),
    (ExecutionModel.PURE_DATA.value, "evaluators"),
    (ExecutionModel.EVENT_SOURCE.value, ""),
])
def test_each_model_requires_the_registry_that_can_serve_it(model: str, expected: str):
    assert _runtime_required(model) == expected


def test_an_action_is_not_covered_by_an_evaluator():
    """The bug itself: flow ports can only be returned by an executor."""
    assert _runtime_required(ExecutionModel.ACTION.value) != "evaluators"


def test_a_pure_data_node_needs_no_executor():
    for node_id in definitions_view():
        if _model(node_id) == ExecutionModel.PURE_DATA.value:
            assert node_id in registry.evaluators, node_id
    assert classify_runtime_coverage()["missing_runtime"] == []


def test_event_sources_stay_structural():
    """They are dispatched by the frame loop, and none needs an executor."""
    coverage = classify_runtime_coverage()
    assert coverage["event_source_without_executor"]
    for node_id in coverage["event_source_without_executor"]:
        assert _model(node_id) == ExecutionModel.EVENT_SOURCE.value


# ---------------------------------------------------------------------------
# 4. No allow-list anywhere in the rule
# ---------------------------------------------------------------------------

def test_the_rule_names_no_node_id():
    """An allow-list would let a node be excused by name instead of contract."""
    source = (REPO_ROOT / "engine" / "logic" / "node_system.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    known = set(definitions_view())
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in ("_runtime_required", "classify_runtime_coverage"):
            continue
        literals = {
            child.value for child in ast.walk(node)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        }
        assert not literals & known, (
            f"{node.name} names specific nodes: {sorted(literals & known)}"
        )


# ---------------------------------------------------------------------------
# 5-6. Declared still beats derived, and coverage uses the canonical model
# ---------------------------------------------------------------------------

def test_declared_execution_model_still_wins_over_derived():
    from engine.logic.contracts import resolve_execution_model

    # restart_scene has a flow output and is TERMINAL by declaration.
    assert resolve_execution_model(
        "terminal", [("in", "flow")], [("next", "flow")]
    ) == ExecutionModel.TERMINAL.value
    assert resolve_execution_model(
        None, [("in", "flow")], [("next", "flow")]
    ) == ExecutionModel.ACTION.value


def test_coverage_reads_the_canonical_model_not_the_pins():
    """A TERMINAL node keeps its executor requirement despite its pins."""
    terminals = [
        node_id for node_id in definitions_view()
        if _model(node_id) == ExecutionModel.TERMINAL.value
    ]
    assert terminals
    for node_id in terminals:
        assert node_id in registry.executors, node_id


def test_the_classification_loses_no_node():
    coverage = classify_runtime_coverage()
    assert sum(len(group) for group in coverage.values()) == len(definitions_view())


# ---------------------------------------------------------------------------
# 7-9. Mutation: the gate must fail for the right reason
# ---------------------------------------------------------------------------

def test_an_artificial_evaluator_cannot_mask_a_missing_executor(monkeypatch):
    """The exact shape of the bug item 11 fixes."""
    node_id = "move_by"
    assert _model(node_id) == ExecutionModel.ACTION.value

    executors = dict(registry.executors)
    executors.pop(node_id)
    evaluators = dict(registry.evaluators)
    evaluators[node_id] = lambda *a, **k: None
    monkeypatch.setattr(registry, "executors", executors)
    monkeypatch.setattr(registry, "evaluators", evaluators)

    assert node_id in classify_runtime_coverage()["missing_runtime"]


def test_removing_an_action_executor_makes_the_gate_fail(monkeypatch):
    executors = dict(registry.executors)
    executors.pop("move_by")
    monkeypatch.setattr(registry, "executors", executors)

    from tools.audit_node_system import runtime_coverage_failures

    assert any("move_by" in failure for failure in runtime_coverage_failures())


def test_removing_a_pure_data_evaluator_makes_the_gate_fail(monkeypatch):
    node_id = next(
        n for n in sorted(definitions_view())
        if _model(n) == ExecutionModel.PURE_DATA.value and n in registry.evaluators
    )
    evaluators = dict(registry.evaluators)
    evaluators.pop(node_id)
    monkeypatch.setattr(registry, "evaluators", evaluators)

    assert node_id in classify_runtime_coverage()["missing_runtime"]


def test_the_audit_gate_and_the_classifier_share_one_source(monkeypatch):
    """Two rules would drift; the gate must read the classification."""
    from tools import audit_node_system

    monkeypatch.setattr(
        audit_node_system, "runtime_coverage_failures",
        audit_node_system.runtime_coverage_failures,
    )
    source = (REPO_ROOT / "tools" / "audit_node_system.py").read_text(encoding="utf-8")
    assert "classify_runtime_coverage" in source
    assert "in handler_registry.executors" not in source


# ---------------------------------------------------------------------------
# 10-12. The catalogue as committed
# ---------------------------------------------------------------------------

def test_the_catalogue_holds_no_unexpected_gap():
    assert classify_runtime_coverage()["missing_runtime"] == []


def test_every_action_and_terminal_node_has_an_executor():
    unbacked = sorted(
        node_id for node_id, definition in definitions_view().items()
        if not definition.get("deprecated", False)
        and _model(node_id) in (ExecutionModel.ACTION.value, ExecutionModel.TERMINAL.value)
        and node_id not in registry.executors
    )
    assert unbacked == [], unbacked


@pytest.mark.parametrize("node_id", ("find_tag", "get_progress_bar_value"))
def test_the_two_nodes_have_exactly_what_their_model_demands(node_id: str):
    assert _model(node_id) == ExecutionModel.ACTION.value
    assert node_id in registry.executors
    assert node_id in registry.evaluators, "the data output still needs one"


@pytest.mark.parametrize("node_id", ("find_tag", "get_progress_bar_value"))
def test_their_executors_return_only_declared_ports(node_id: str):
    from engine.logic.graph_asset import declared_flow_outputs
    from tools.audit_node_system import returned_flow_ports

    returned = returned_flow_ports(registry.executors[node_id])
    assert returned <= set(declared_flow_outputs(node_id))
    assert returned, "an executor returning nothing would stop the flow"


def test_find_tag_resolves_and_continues():
    from engine.logic.graph_asset import normalize_logic_graph
    from engine.logic.runtime.core import LogicGraphRuntime

    class _Game:
        def __init__(self):
            self.asked: list[str] = []

        def find(self, tag):
            self.asked.append(tag)
            return f"<{tag}>"

    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "FindTag",
        "nodes": [{"id": "n", "type": "find_tag", "position": [0.0, 0.0],
                   "properties": {"tag": "Enemy"}}],
        "edges": [],
    })
    runtime = LogicGraphRuntime(graph)
    game = _Game()
    assert registry.executors["find_tag"](runtime, graph["nodes"][0], game, 1 / 60) == ["next"]
    assert game.asked == ["Enemy"]
    assert runtime.values.get(("n", "object")) == "<Enemy>"


# ---------------------------------------------------------------------------
# Recorded, not fixed
# ---------------------------------------------------------------------------

def test_the_progress_bar_declaration_still_shadows_its_contract():
    """A debt with a name and a bound, deliberately left by item 11.

    ``dynamic_ui_nodes`` declares ``exec_success`` / ``exec_not_found`` /
    ``exec_failure``; the effective contract, the restored executor and the one
    shipping asset all speak ``next``. Nothing ever returned the three branches.
    Removing them is an authoring-contract decision, and removing ``next``
    instead would orphan the edge ``comidaLogic.zlogic`` already has.
    """
    import engine.logic.node_definitions.dynamic_ui_nodes as declarations
    from engine.logic.graph_asset import declared_flow_outputs

    declared = {
        pin.id
        for pin in declarations.GetProgressBarValueNode.__node_definition__.outputs
    }
    assert {"exec_success", "exec_not_found", "exec_failure"} <= declared
    assert declared_flow_outputs("get_progress_bar_value") == ("next",)
