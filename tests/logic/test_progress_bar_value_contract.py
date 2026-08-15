"""``get_progress_bar_value``: declaration, runtime and asset tell one story.

PHASE 9 recovery item 13.

Three designs had diverged, and the item's job was to find out which one the
node actually promises:

* the **declaration** in ``dynamic_ui_nodes`` offered ``exec_success`` /
  ``exec_not_found`` / ``exec_failure``;
* the **effective contract**, a ``_EXPLICIT_PORT_CONTRACTS`` entry shadowing it,
  offered a single ``next``, and that is what the restored executor returned;
* **PHASE 3C** wrote ``graph_migration.py``, whose ``IMPURE_TO_PURE_NODES``
  holds exactly this node and whose job is to strip its flow edges -- a design
  decision that the node should become PURE_DATA. That migration is never
  invoked anywhere in ``engine/`` or ``editor/``.

The measurement settled it. The executor returned ``["next"]`` in every case --
widget found, value zero, widget missing, widget malformed -- so ``next`` means
*continue whatever happened*, not *success*. Aliasing it onto ``exec_success``
would have been a lie, and the item's own brief forbids using a port alias to
hide a semantic difference.

The three outcomes were never fantasy either: the evaluator already raises and
swallows ``UIWidgetNotFoundError``, so the states were distinguishable all
along. And the sibling UI nodes ``bind_ui_to_variable`` and
``update_ui_binding`` declare the same four pins.

So the contract is the family's: ``next`` fires every time and keeps the one
shipping edge working, and the outcome branch fires beside it.
"""

from __future__ import annotations

import pathlib

import pytest

from engine.logic.contracts import ExecutionModel
from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    declared_flow_outputs,
    load_logic_graph,
    normalize_logic_graph,
    node_port_definitions,
    save_logic_graph,
)
from engine.logic.node_definitions import definition_owner
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded, resolve_node_id
from engine.logic.node_definitions.registry import get_registry
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.registry import registry

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
NODE = "get_progress_bar_value"
ASSET = REPO_ROOT / "Assets" / "Logic" / "comidaLogic.zlogic"
DT = 1.0 / 60.0


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


class _Game:
    def __init__(self, world: dict | None = None):
        self._world = world if world is not None else {}
        self.objects: dict = {}


def _bar(value):
    return {"canvas": {"ui": {"_widget_overrides": {"progress": {"value": value}}}}}


def _run(world, widget_name: str = "progress"):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "ProgressBar",
        "nodes": [{"id": "n", "type": NODE, "position": [0.0, 0.0],
                   "properties": {"widget_name": widget_name}}],
        "edges": [],
    })
    runtime = LogicGraphRuntime(graph)
    game = _Game(world)
    ports = registry.executors[NODE](runtime, graph["nodes"][0], game, DT)
    return ports, runtime.values.get(("n", "value"))


# ---------------------------------------------------------------------------
# 1-6. One owner, one contract
# ---------------------------------------------------------------------------

def test_there_is_one_definition_owner():
    assert definition_owner(NODE) == "dynamic_ui_nodes"


def test_the_execution_model_is_action():
    assert get_registry().execution_model(NODE) == ExecutionModel.ACTION.value


def test_both_halves_of_the_runtime_are_registered():
    assert NODE in registry.executors
    assert NODE in registry.evaluators


def test_the_shadowing_override_is_gone():
    """One source of truth: the declaration now reaches the editor unaltered."""
    from engine.logic.node_definitions.catalogue import _EXPLICIT_PORT_CONTRACTS

    assert NODE not in _EXPLICIT_PORT_CONTRACTS


def test_the_declaration_and_the_effective_contract_agree():
    assert [tuple(pin) for pin in NODE_DEFINITIONS[NODE]["outputs"]] == [
        tuple(pin) for pin in NODE_PORT_DEFINITIONS[NODE]["outputs"]
    ]


def test_the_flow_contract_matches_the_sibling_ui_nodes():
    """The convention this node was the only one outside of."""
    assert set(declared_flow_outputs(NODE)) == {
        "next", "exec_success", "exec_not_found", "exec_failure",
    }
    for sibling in ("bind_ui_to_variable", "update_ui_binding"):
        assert set(declared_flow_outputs(sibling)) == set(declared_flow_outputs(NODE))


def test_the_authorable_property_is_the_one_the_runtime_reads():
    assert set(NODE_DEFINITIONS[NODE].get("properties", {})) == {"widget_name"}


def test_the_palette_holds_exactly_one_entry():
    entries = [n for n in NODE_DEFINITIONS if resolve_node_id(n) == NODE]
    assert entries == [NODE]


# ---------------------------------------------------------------------------
# 7-11. Behaviour, measured
# ---------------------------------------------------------------------------

def test_a_found_widget_reports_success_and_the_value():
    ports, value = _run(_bar(75.0))
    assert ports == ["next", "exec_success"]
    assert value == pytest.approx(75.0)


def test_zero_is_a_value_not_an_absence():
    """The trap in every 'falsy means missing' implementation."""
    ports, value = _run(_bar(0.0))
    assert ports == ["next", "exec_success"]
    assert value == pytest.approx(0.0)


def test_a_missing_widget_reports_not_found():
    ports, value = _run({})
    assert ports == ["next", "exec_not_found"]
    assert value is None


def test_a_malformed_widget_reports_not_found():
    ports, _value = _run({"canvas": {"ui": {"_widget_overrides": {"progress": {}}}}})
    assert ports == ["next", "exec_not_found"]


def test_a_broken_read_reports_failure_not_absence(monkeypatch):
    """``exec_failure`` is a different thing from ``exec_not_found``."""
    def _explode(*_args, **_kwargs):
        raise RuntimeError("the UI service blew up")

    monkeypatch.setattr(
        "engine.logic.runtime.nodes.dynamic_ui_nodes.evaluate_get_progress_bar_value",
        _explode,
    )
    ports, _value = _run(_bar(10.0))
    assert ports == ["next", "exec_failure"]


def test_next_fires_on_every_outcome():
    """The reason ``next`` is its own pin and not an alias of success.

    It means *continue whatever happened*. ``comidaLogic.zlogic`` relies on
    that: event_update -> here -> set_hud, every frame.
    """
    for world in (_bar(75.0), _bar(0.0), {}):
        ports, _value = _run(world)
        assert ports[0] == "next", ports


def test_exactly_one_outcome_branch_fires_at_a_time():
    outcomes = {"exec_success", "exec_not_found", "exec_failure"}
    for world in (_bar(75.0), _bar(0.0), {}):
        ports, _value = _run(world)
        assert len(set(ports) & outcomes) == 1, ports


# ---------------------------------------------------------------------------
# 12. Executor and evaluator are one node, not two
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("world", [_bar(75.0), _bar(0.0), {}])
def test_executor_and_evaluator_agree_on_the_value(world):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Parity",
        "nodes": [{"id": "n", "type": NODE, "position": [0.0, 0.0],
                   "properties": {"widget_name": "progress"}}],
        "edges": [],
    })
    runtime = LogicGraphRuntime(graph)
    game = _Game(world)
    node = graph["nodes"][0]

    registry.executors[NODE](runtime, node, game, DT)
    from_executor = runtime.values.get(("n", "value"))
    from_evaluator = registry.evaluators[NODE](runtime, "n", "value", node, game, DT, set())
    assert from_executor == from_evaluator


# ---------------------------------------------------------------------------
# 13-14. Contract and implementation agree
# ---------------------------------------------------------------------------

def test_the_executor_returns_only_declared_ports():
    from tools.audit_node_system import returned_flow_ports

    assert returned_flow_ports(registry.executors[NODE]) <= set(declared_flow_outputs(NODE))


def test_every_declared_branch_is_reachable():
    from tools.audit_node_system import returned_flow_ports

    unreachable = set(declared_flow_outputs(NODE)) - returned_flow_ports(registry.executors[NODE])
    assert not unreachable, f"declared but never returned: {sorted(unreachable)}"


def test_the_audit_reports_no_undeclared_output():
    from tools.audit_node_system import executor_output_violations

    assert NODE not in executor_output_violations()


# ---------------------------------------------------------------------------
# 15-17. The shipping asset, unmodified
# ---------------------------------------------------------------------------

def test_the_shipping_asset_still_resolves_every_edge():
    graph = normalize_logic_graph(load_logic_graph(ASSET))
    nodes = {str(n["id"]): n for n in graph["nodes"]}
    instances = [n for n in nodes.values() if str(n["type"]) == NODE]
    assert instances, "comidaLogic.zlogic no longer holds the node this item is about"

    for edge in graph["edges"]:
        source = nodes.get(str(edge.get("from_node")))
        target = nodes.get(str(edge.get("to_node")))
        if source and str(source["type"]) == NODE:
            assert str(edge["from_port"]) in {
                name for name, _k in node_port_definitions(source)["outputs"]
            }, edge
        if target and str(target["type"]) == NODE:
            assert str(edge["to_port"]) in {
                name for name, _k in node_port_definitions(target)["inputs"]
            }, edge


def test_the_assets_next_edge_is_not_orphaned():
    graph = normalize_logic_graph(load_logic_graph(ASSET))
    nodes = {str(n["id"]): n for n in graph["nodes"]}
    outgoing = [
        edge for edge in graph["edges"]
        if str(nodes.get(str(edge.get("from_node")), {}).get("type")) == NODE
    ]
    assert [str(edge["from_port"]) for edge in outgoing] == ["next"]
    assert "next" in declared_flow_outputs(NODE)


def test_the_asset_flow_runs_end_to_end():
    """Load the real file, run it, and watch the flow reach the next node."""
    graph = normalize_logic_graph(load_logic_graph(ASSET))
    nodes = {str(n["id"]): n for n in graph["nodes"]}
    node = next(n for n in nodes.values() if str(n["type"]) == NODE)

    runtime = LogicGraphRuntime(graph)
    game = _Game(_bar(42.0))
    ports = registry.executors[NODE](runtime, node, game, DT)

    assert "next" in ports
    followed = {
        str(nodes[str(edge["to_node"])]["type"])
        for edge in graph["edges"]
        if str(edge.get("from_node")) == str(node["id"]) and str(edge["from_port"]) in ports
    }
    assert followed, "the asset's downstream node is no longer reachable"


def test_no_asset_was_modified():
    import subprocess

    changed = subprocess.run(
        ["git", "status", "--porcelain", "--", "Assets"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    unallowed = [l for l in changed.splitlines() if "EnemyAttackLogic.zlogic" not in l and "BossHealthLogic.zlogic" not in l and "LevelExitLogic.zlogic" not in l]
    assert not unallowed, unallowed


# ---------------------------------------------------------------------------
# 18-20. Round trip and separation of concerns
# ---------------------------------------------------------------------------

def test_normalization_is_idempotent():
    graph = normalize_logic_graph(load_logic_graph(ASSET))
    assert normalize_logic_graph(graph) == graph


def test_save_reopen_preserves_the_node_and_its_flow(tmp_path):
    graph = normalize_logic_graph(load_logic_graph(ASSET))
    destination = tmp_path / "comidaLogic.zlogic"
    save_logic_graph(destination, graph)
    assert normalize_logic_graph(load_logic_graph(destination)) == graph


def test_next_is_not_registered_as_a_port_alias_of_success():
    """The semantic lie this item refused to tell."""
    from engine.logic.port_aliases import NODE_SCOPED_OUTPUT_ALIASES

    assert NODE_SCOPED_OUTPUT_ALIASES.get(NODE, {}).get("next") != "exec_success"


def test_the_phase_3c_pure_migration_is_still_not_wired():
    """Recorded, not acted on: a third design exists and never ran.

    ``graph_migration.py`` declares this node in ``IMPURE_TO_PURE_NODES`` and
    would strip its flow edges. It is invoked nowhere in the engine or editor,
    and the one shipping asset uses the node as a flow step, so honouring it
    would change what that graph does. Asserted so that wiring it becomes a
    deliberate decision rather than a surprise.
    """
    from engine.logic.runtime.graph_migration import IMPURE_TO_PURE_NODES

    assert NODE in IMPURE_TO_PURE_NODES
    callers = [
        path for path in (REPO_ROOT / "engine").rglob("*.py")
        if path.name != "graph_migration.py"
        and "GraphMigration(" in path.read_text(encoding="utf-8")
    ]
    assert callers == [], f"the migration became live: {callers}"
