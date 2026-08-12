"""The save/load nodes: one executor each, returning the ports they declare.

PHASE 9 recovery item 6.

``load_game`` and ``has_save`` each had two executors, and the broken one won by
load order. ``scene_nodes`` held stubs:

    @registry.register_executor(('game.has_save', 'has_save'))
    def execute_game_has_save(runtime, node, game, dt):
        return ["false"]

That is the whole implementation -- it never checked for a save, and ``false``
is not a port the node declares. The ``load_game`` stub ignored the declared
``slot_name`` property and read a ``slot`` of its own invention, so the slot an
author picked never reached the save system.

The real implementations in ``save_load_nodes`` were reachable only for
``save_game`` and ``delete_save``, and even those returned ``saved`` /
``deleted`` / ``failure`` where the contract declares ``exec_saved`` /
``exec_deleted`` / ``exec_failure``. An edge wired to the declared port was
never followed.

All four now return what they declare, and ``scene_nodes`` no longer competes.
"""

from __future__ import annotations

import ast
import inspect
import json
import textwrap
from pathlib import Path

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.node_definitions import definition_owner
from engine.logic.node_definitions.catalogue import NODE_ID_ALIASES, resolve_node_id
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.registry import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SAVE_LOAD_NODES = ("save_game", "load_game", "delete_save", "has_save")


@pytest.fixture(scope="module", autouse=True)
def runtime_loaded():
    load_runtime_node_modules()


def _returned_flow_ports(node_id: str) -> set[str]:
    """String literals returned inside a list, via AST so ternaries count."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(registry.executors[node_id])))
    ports: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Return) or not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        for element in ast.walk(node.value):
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                ports.add(element.value)
    return ports


def _declared_flow_outputs(node_id: str) -> set[str]:
    return {n for n, k in NODE_PORT_DEFINITIONS[node_id]["outputs"] if k in ("flow", "exec")}


# ---------------------------------------------------------------------------
# One owner, one executor
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_id", SAVE_LOAD_NODES)
def test_the_executor_lives_in_save_load_nodes(node_id: str):
    assert registry.executors[node_id].__module__ == (
        "engine.logic.runtime.nodes.save_load_nodes"
    )
    assert definition_owner(node_id) == "save_load_nodes"


@pytest.mark.parametrize("node_id", ("load_game", "has_save"))
def test_scene_nodes_no_longer_implements_it(node_id: str):
    import engine.logic.runtime.nodes.scene_nodes as scene_runtime

    source = Path(scene_runtime.__file__).read_text(encoding="utf-8")
    assert f"'{node_id}'" not in source and f'"{node_id}"' not in source


def test_no_save_load_node_has_two_executor_owners():
    duplicated = {
        key: owners for key, owners in registry.duplicate_owners().items()
        if any(key.endswith(f":{node_id}") for node_id in SAVE_LOAD_NODES)
    }
    assert not duplicated, duplicated


# ---------------------------------------------------------------------------
# Contract vs executor
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_id", SAVE_LOAD_NODES)
def test_the_executor_returns_only_declared_ports(node_id: str):
    returned = _returned_flow_ports(node_id)
    declared = _declared_flow_outputs(node_id)
    assert returned, f"{node_id}: no returned ports found; the scan is broken"
    assert returned <= declared, (
        f"{node_id} returns {sorted(returned - declared)}, which the contract does not "
        f"declare (declares {sorted(declared)}). An edge on the declared port would "
        "never be followed."
    )


@pytest.mark.parametrize("node_id,expected", [
    ("has_save", {"exec_exists", "exec_not_exists", "exec_failure"}),
    ("load_game", {"exec_loaded", "exec_no_save", "exec_failure"}),
    ("save_game", {"exec_saved", "exec_failure"}),
    ("delete_save", {"exec_deleted", "exec_failure"}),
])
def test_the_declared_outcomes_are_distinct_and_complete(node_id: str, expected: set):
    assert _declared_flow_outputs(node_id) == expected


@pytest.mark.parametrize("node_id", SAVE_LOAD_NODES)
def test_every_declared_outcome_is_reachable(node_id: str):
    """A declared branch nothing returns is a pin the author can never use."""
    unreachable = _declared_flow_outputs(node_id) - _returned_flow_ports(node_id)
    assert not unreachable, f"{node_id} declares {sorted(unreachable)} but never returns them"


# ---------------------------------------------------------------------------
# Runtime behaviour
# ---------------------------------------------------------------------------

class _Runtime:
    def __init__(self, slots=None):
        self.values = {}
        if slots is not None:
            self._save_slots = slots

    def _store(self, node_id, key, value):
        self.values[(node_id, key)] = value

    def _read_input(self, node_id, name, fallback, game, dt, seen):
        return fallback


class _Game:
    """No save_path, so the filesystem is never consulted."""


def _run(node_id: str, properties: dict, runtime) -> list[str]:
    node = {"id": "n", "type": node_id, "properties": properties}
    return registry.executors[node_id](runtime, node, _Game(), 1.0 / 60.0)


def test_has_save_takes_the_exists_branch():
    runtime = _Runtime({"autosave": {"variables": {}}})
    assert _run("has_save", {"slot_name": "autosave"}, runtime) == ["exec_exists"]


def test_has_save_takes_the_not_exists_branch():
    runtime = _Runtime({})
    assert _run("has_save", {"slot_name": "autosave"}, runtime) == ["exec_not_exists"]


def test_has_save_distinguishes_the_two_branches():
    """The stub returned one constant; these must differ by the actual state."""
    with_save = _run("has_save", {"slot_name": "s"}, _Runtime({"s": {}}))
    without = _run("has_save", {"slot_name": "s"}, _Runtime({}))
    assert with_save != without


def test_has_save_reads_the_slot_the_author_set():
    runtime = _Runtime({"autosave": {}})
    assert _run("has_save", {"slot_name": "other"}, runtime) == ["exec_not_exists"]
    assert _run("has_save", {"slot_name": "autosave"}, runtime) == ["exec_exists"]


def test_has_save_takes_the_failure_branch_on_error():
    class Broken(_Runtime):
        @property
        def _save_slots(self):
            raise RuntimeError("backend down")

    assert _run("has_save", {"slot_name": "autosave"}, Broken()) == ["exec_failure"]


def test_load_game_takes_the_loaded_branch():
    runtime = _Runtime({"autosave": {"variables": {"health": 50}}})
    assert _run("load_game", {"slot_name": "autosave"}, runtime) == ["exec_loaded"]
    assert runtime._variables["health"] == 50, "the save was not actually restored"


def test_load_game_takes_the_no_save_branch():
    assert _run("load_game", {"slot_name": "missing"}, _Runtime({})) == ["exec_no_save"]


def test_load_game_takes_the_failure_branch_on_error():
    class Broken(_Runtime):
        def _store(self, *args):
            raise RuntimeError("storage down")

    runtime = Broken({"autosave": {"variables": {}}})
    assert _run("load_game", {"slot_name": "autosave"}, runtime) == ["exec_failure"]


def test_save_and_load_round_trip_through_the_declared_ports():
    runtime = _Runtime({})
    runtime._variables = {"coins": 7}
    assert _run("save_game", {"slot_name": "slot1"}, runtime) == ["exec_saved"]

    runtime._variables = {}
    assert _run("load_game", {"slot_name": "slot1"}, runtime) == ["exec_loaded"]
    assert runtime._variables.get("coins") == 7


def test_delete_save_takes_the_deleted_branch():
    runtime = _Runtime({"slot1": {"variables": {}}})
    assert _run("delete_save", {"slot_name": "slot1"}, runtime) == ["exec_deleted"]


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("node_id", SAVE_LOAD_NODES)
def test_slot_name_is_the_only_slot_property(node_id: str):
    properties = NODE_DEFINITIONS[node_id]["properties"]
    assert "slot_name" in properties
    assert "slot" not in properties, (
        f"{node_id} exposes a dead 'slot' field beside slot_name; that name came "
        "from the removed stub executor"
    )


def test_a_graph_saved_with_slot_is_migrated():
    graph = {
        "format": "zennity.logic_graph", "version": 1, "name": "LegacySlot",
        "nodes": [{"id": "n", "type": "load_game", "position": [0.0, 0.0],
                   "properties": {"slot": "autosave"}}],
        "edges": [],
    }
    properties = normalize_logic_graph(graph)["nodes"][0]["properties"]
    assert properties["slot_name"] == "autosave"
    assert "slot" not in properties


# ---------------------------------------------------------------------------
# MainMenuLogic
# ---------------------------------------------------------------------------

MAIN_MENU = REPO_ROOT / "Assets" / "Logic" / "MainMenuLogic.zlogic"


@pytest.fixture(scope="module")
def main_menu():
    if not MAIN_MENU.is_file():
        pytest.skip("MainMenuLogic.zlogic is not in this checkout")
    return normalize_logic_graph(load_logic_graph(MAIN_MENU))


def test_the_legacy_input_port_resolves(main_menu):
    nodes = {str(n["id"]): n for n in main_menu["nodes"]}
    edges = [
        e for e in main_menu["edges"]
        if nodes[str(e["to_node"])]["type"] == "load_game"
    ]
    assert edges, "MainMenuLogic no longer wires load_game"
    for edge in edges:
        assert edge["to_port"] == "exec"


def test_has_save_next_resolves_to_exists_because_of_the_downstream(main_menu):
    """The asset says which branch was meant, so this is evidence, not a guess.

    check_save.next feeds ui.set_widget_enabled with
    {widget_name: "ContinueButton", enabled: true}. Continue is enabled when a
    save exists. The opposite reading -- enable Continue when there is nothing
    to continue -- is not a coherent design.
    """
    nodes = {str(n["id"]): n for n in main_menu["nodes"]}
    edges = [
        e for e in main_menu["edges"]
        if nodes[str(e["from_node"])]["type"] == "has_save"
    ]
    assert edges, "MainMenuLogic no longer wires has_save"
    for edge in edges:
        assert edge["from_port"] == "exec_exists"
        target = nodes[str(edge["to_node"])]
        assert target["type"] == "ui.set_widget_enabled"
        assert target["properties"].get("enabled") is True, (
            "the downstream no longer enables a widget; the justification for "
            "mapping next -> exec_exists must be re-checked"
        )


def test_main_menu_has_no_orphan_edges_left_on_the_save_nodes(main_menu):
    from engine.logic.graph_asset import node_port_definitions

    nodes = {str(n["id"]): n for n in main_menu["nodes"]}
    for edge in main_menu["edges"]:
        source, target = nodes[str(edge["from_node"])], nodes[str(edge["to_node"])]
        if source["type"] in SAVE_LOAD_NODES:
            assert str(edge["from_port"]) in {
                n for n, _k in node_port_definitions(source)["outputs"]
            }, edge
        if target["type"] in SAVE_LOAD_NODES:
            assert str(edge["to_port"]) in {
                n for n, _k in node_port_definitions(target)["inputs"]
            }, edge


# ---------------------------------------------------------------------------
# Node ids
# ---------------------------------------------------------------------------

def test_the_dotted_spellings_still_load():
    graph = {
        "format": "zennity.logic_graph", "version": 1, "name": "DottedIds",
        "nodes": [{"id": "a", "type": "game.load_game", "position": [0.0, 0.0]},
                  {"id": "b", "type": "game.has_save", "position": [1.0, 0.0]}],
        "edges": [],
    }
    types = [n["type"] for n in normalize_logic_graph(graph)["nodes"]]
    assert types == ["load_game", "has_save"]


@pytest.mark.parametrize("alias", ("game.load_game", "game.has_save"))
def test_the_dotted_spelling_is_an_alias_not_a_palette_entry(alias: str):
    assert alias in NODE_ID_ALIASES
    assert alias not in NODE_DEFINITIONS
    assert resolve_node_id(alias) in NODE_DEFINITIONS


def test_a_new_graph_saves_the_canonical_ids(tmp_path: Path):
    graph = {
        "format": "zennity.logic_graph", "version": 1, "name": "FreshSaveLoad",
        "nodes": [{"id": "a", "type": "has_save", "position": [0.0, 0.0]},
                  {"id": "b", "type": "load_game", "position": [1.0, 0.0]}],
        "edges": [{"from_node": "a", "from_port": "exec_exists",
                   "to_node": "b", "to_port": "exec", "kind": "flow"}],
    }
    destination = tmp_path / "FreshSaveLoad.zlogic"
    normalized = normalize_logic_graph(graph)
    save_logic_graph(destination, normalized)
    written = json.loads(destination.read_text(encoding="utf-8"))
    assert [n["type"] for n in written["nodes"]] == ["has_save", "load_game"]
    assert written["edges"][0]["from_port"] == "exec_exists"
    assert normalize_logic_graph(load_logic_graph(destination)) == normalized


# ---------------------------------------------------------------------------
# The wider class, recorded
# ---------------------------------------------------------------------------

BASELINE = json.loads(
    (REPO_ROOT / "tests" / "fixtures" / "stage2" / "executor_port_mismatch_baseline.json")
    .read_text(encoding="utf-8")
)


def _current_mismatches() -> dict[str, list[str]]:
    """Item 7 moved this scan into the canonical auditor.

    The local version here walked every string in the return statement, so an
    executor returning ``[sole_flow_output(node_type, default="next")]`` was
    reported as returning ``"next"``. One scan, in the tool that gates CI.
    """
    from tools.audit_node_system import executor_output_violations

    return executor_output_violations()


def test_no_new_executor_port_mismatch_appears():
    """45 nodes engine-wide return a port they do not declare -- systemic, recorded.

    Not a save/load problem: executors across the catalogue return the unprefixed
    spelling (success / failure / loaded) while their declaration uses exec_*.
    An edge wired to the declared port is never followed. Item 6 fixed the four
    save/load nodes; the rest are recorded so the class is visible and bounded.
    """
    new = set(_current_mismatches()) - set(BASELINE["nodes"])
    assert not new, f"these nodes started returning undeclared flow ports: {sorted(new)}"


def test_a_fixed_node_is_removed_from_the_baseline():
    """The baseline is a debt, not an exemption."""
    stale = set(BASELINE["nodes"]) - set(_current_mismatches())
    assert not stale, (
        f"{sorted(stale)} no longer mismatch; remove them from "
        "executor_port_mismatch_baseline.json"
    )


@pytest.mark.parametrize("node_id", SAVE_LOAD_NODES)
def test_the_save_load_nodes_are_not_in_the_baseline(node_id: str):
    assert node_id not in BASELINE["nodes"]
