"""One authority decides what a node id resolves to.

PHASE 9 recovery item 12.

``all_aliases()`` used to merge two tables and report 43 aliases, of which
**32 could not be resolved by ``resolve_node_id``**. A diagnostic asserting
something no other subsystem honoured is how ``variable.set`` hid: reported as a
known legacy id, invisible to the resolver, so a saved graph carrying it went
nowhere on the paths that do not migrate.

Item 8 fixed that one id. This item fixes the class: whatever the engine reports
as an alias must resolve, and the audit checks the report against the resolver
rather than trusting it.

The two tables are deliberately **not** merged, because they do not describe the
same thing:

* ``NODE_ID_ALIASES`` -- which ``.zlogic`` node id is an alias of which. Eleven
  entries, every target a real definition. This is the authority.
* ``LEGACY_NODE_TYPES`` -- the migration map for pre-1.0 visual-script
  documents. Thirty-four entries, **five of whose targets are node ids that do
  not exist**; the migration degrades on purpose. Membership in it is also what
  ``is_legacy_visual_script`` uses to recognise the format, so folding it in
  would make any ``.zlogic`` holding an alias look like a legacy visual script.

Node aliases and port aliases stay separate systems, and this file asserts that
too: an id is not a port name, and resolving a node id must not need the port
module.
"""

from __future__ import annotations

import pathlib

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    load_logic_graph,
    normalize_logic_graph,
    save_logic_graph,
)
from engine.logic.node_definitions.catalogue import (
    NODE_ID_ALIASES,
    all_aliases,
    ensure_catalogue_loaded,
    resolve_node_id,
    validate_node_id_aliases,
)
from engine.logic.node_system import load_runtime_node_modules
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.runtime.registry import registry

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", autouse=True)
def _loaded():
    ensure_catalogue_loaded()
    load_runtime_node_modules()


def _reported() -> list[tuple[str, str]]:
    return [(source, canonical) for canonical, sources in all_aliases().items()
            for source in sources]


# ---------------------------------------------------------------------------
# The class of bug, stated as a property
# ---------------------------------------------------------------------------

def test_every_reported_alias_resolves_to_what_is_reported():
    """The invariant ``variable.set`` violated, as a property rather than a case."""
    disagreeing = [
        (source, canonical, resolve_node_id(source))
        for source, canonical in _reported()
        if resolve_node_id(source) != canonical
    ]
    assert disagreeing == [], disagreeing


def test_the_report_and_the_table_hold_the_same_pairs():
    """One authority, two views of it -- never two sources."""
    assert sorted(_reported()) == sorted(NODE_ID_ALIASES.items())


def test_no_alias_source_is_left_unresolvable():
    for source in NODE_ID_ALIASES:
        assert resolve_node_id(source) != source, source


def test_the_migration_map_is_not_folded_into_the_alias_table():
    """Merging them would import five targets that do not exist.

    ``LEGACY_NODE_TYPES`` maps a different file format and degrades on purpose;
    it is not an authority on ``.zlogic`` node ids.
    """
    from engine.logic.legacy_visual_script import LEGACY_NODE_TYPES

    dangling = sorted(
        target for target in set(LEGACY_NODE_TYPES.values())
        if target not in NODE_DEFINITIONS
    )
    assert dangling, "if the migration map ever became clean, revisit the split"
    for target in dangling:
        assert target not in set(NODE_ID_ALIASES.values()), (
            f"{target} has no definition and must not be an alias target"
        )


def test_all_aliases_no_longer_reads_the_migration_map():
    """Read the executable statements, not the prose.

    A substring scan over the source matches this function's own docstring,
    which explains at length why the migration map is excluded -- the same trap
    that produced a self-satisfying assertion twice earlier in this phase.
    """
    import ast

    tree = ast.parse(
        (REPO_ROOT / "engine" / "logic" / "node_definitions" / "catalogue.py")
        .read_text(encoding="utf-8")
    )
    function = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "all_aliases"
    )
    names = {
        node.id for node in ast.walk(function) if isinstance(node, ast.Name)
    } | {
        alias.name for node in ast.walk(function)
        if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names
    }
    assert "LEGACY_NODE_TYPES" not in names
    assert "NODE_ID_ALIASES" in names


# ---------------------------------------------------------------------------
# Structural health of the table
# ---------------------------------------------------------------------------

def test_the_alias_table_is_structurally_sound():
    assert validate_node_id_aliases(set(NODE_DEFINITIONS)) == []


def test_no_alias_target_is_missing():
    for source, target in NODE_ID_ALIASES.items():
        assert target in NODE_DEFINITIONS, f"{source} -> {target}"


def test_no_alias_is_itself_a_definition():
    for source in NODE_ID_ALIASES:
        assert source not in NODE_DEFINITIONS, source
        assert source not in NODE_PORT_DEFINITIONS, source


def test_no_two_sources_claim_conflicting_targets():
    """A dict cannot hold two targets for one key -- prove the file agrees."""
    source = (
        REPO_ROOT / "engine" / "logic" / "node_definitions" / "catalogue.py"
    ).read_text(encoding="utf-8")
    block = source.split("NODE_ID_ALIASES: Mapping[str, str] = MappingProxyType({")[1]
    block = block.split("})")[0]
    keys = [
        line.split(":")[0].strip().strip('"\'')
        for line in block.splitlines()
        if ":" in line and not line.strip().startswith("#")
    ]
    assert len(keys) == len(set(keys)), "a duplicate key would silently win"


@pytest.mark.parametrize("node_id", sorted(NODE_ID_ALIASES) + sorted(NODE_DEFINITIONS)[:5])
def test_resolution_is_idempotent(node_id: str):
    once = resolve_node_id(node_id)
    assert resolve_node_id(once) == once


def test_an_unknown_id_is_returned_unchanged():
    """Existing engine policy, not a new one."""
    assert resolve_node_id("no_such_node_id") == "no_such_node_id"


# ---------------------------------------------------------------------------
# Node aliases are not port aliases
# ---------------------------------------------------------------------------

def test_no_alias_names_a_port():
    port_names = {
        name
        for ports in NODE_PORT_DEFINITIONS.values()
        for side in ("inputs", "outputs")
        for name, _kind in ports.get(side, ())
    }
    overlap = sorted(set(NODE_ID_ALIASES) & port_names)
    assert overlap == [], overlap


def test_resolving_a_node_id_does_not_need_the_port_module():
    source = (
        REPO_ROOT / "engine" / "logic" / "node_definitions" / "catalogue.py"
    ).read_text(encoding="utf-8")
    block = source.split("def resolve_node_id(")[1].split("\ndef ")[0]
    assert "port_aliases" not in block


# ---------------------------------------------------------------------------
# Every subsystem agrees
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("alias,canonical", sorted(NODE_ID_ALIASES.items()))
def test_the_normalizer_agrees_with_the_resolver(alias: str, canonical: str):
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Aliased",
        "nodes": [{"id": "n", "type": alias, "position": [0.0, 0.0]}],
        "edges": [],
    })
    assert graph["nodes"][0]["type"] == canonical


@pytest.mark.parametrize("alias", sorted(NODE_ID_ALIASES))
def test_no_alias_reaches_the_palette(alias: str):
    assert alias not in NODE_DEFINITIONS


def test_the_audit_consumes_the_same_source():
    from tools.audit_node_system import alias_failures

    assert alias_failures() == []
    source = (REPO_ROOT / "tools" / "audit_node_system.py").read_text(encoding="utf-8")
    assert "all_aliases" in source, "the gate must read the canonical report"


def test_aliases_do_not_create_duplicate_definitions():
    from engine.logic.node_definitions.registry import get_registry

    conflicts = [c for c in get_registry().definition_conflicts() if c[0] in NODE_ID_ALIASES]
    assert conflicts == [], conflicts


def test_import_order_does_not_change_resolution():
    """Resolution must not depend on which module happened to load first."""
    before = dict(NODE_ID_ALIASES)
    load_runtime_node_modules()
    ensure_catalogue_loaded()
    assert dict(NODE_ID_ALIASES) == before


# ---------------------------------------------------------------------------
# The real path: a saved alias reaches the canonical runtime
# ---------------------------------------------------------------------------

def test_a_saved_alias_loads_normalizes_and_runs_as_the_canonical_node(tmp_path):
    """The regression ``variable.set`` was, walked end to end."""
    destination = tmp_path / "Legacy.zlogic"
    destination.write_text(
        '{"format": "zennity.logic_graph", "version": 1, "name": "Legacy", '
        '"nodes": [{"id": "n", "type": "variable.set", "position": [0.0, 0.0], '
        '"properties": {"name": "hp", "value": 42, "scope": "object"}}], "edges": []}',
        encoding="utf-8",
    )
    graph = normalize_logic_graph(load_logic_graph(destination))
    assert graph["nodes"][0]["type"] == "set_variable"

    class _Game:
        def __init__(self):
            self.variables: dict = {}

        def set_variable(self, name, value):
            self.variables[name] = value

    runtime = LogicGraphRuntime(graph)
    game = _Game()
    registry.executors["set_variable"](runtime, graph["nodes"][0], game, 1 / 60)
    assert game.variables == {"hp": 42}


@pytest.mark.parametrize("alias", ("variable.set", "variables.set"))
def test_the_variable_set_regression_specifically(alias: str):
    """The id that cost an item to find, pinned by name as well as by property."""
    assert resolve_node_id(alias) == "set_variable"
    assert alias not in NODE_DEFINITIONS


def test_saving_a_loaded_alias_writes_the_canonical_id(tmp_path):
    """Save canonicalization: present, and asserted rather than assumed."""
    graph = normalize_logic_graph({
        "format": "zennity.logic_graph", "version": 1, "name": "Canonical",
        "nodes": [{"id": "n", "type": "variable.set", "position": [0.0, 0.0]}],
        "edges": [],
    })
    destination = tmp_path / "canonical.zlogic"
    save_logic_graph(destination, graph)
    written = load_logic_graph(destination)
    assert written["nodes"][0]["type"] == "set_variable"


# ---------------------------------------------------------------------------
# Mutation: the gates must fail for the right reason
# ---------------------------------------------------------------------------

def test_a_broken_target_is_detected():
    from engine.logic.node_definitions import catalogue

    broken = dict(NODE_ID_ALIASES)
    broken["some.legacy"] = "node_that_does_not_exist"
    problems = _with_alias_table(catalogue, broken, lambda: validate_node_id_aliases(
        set(NODE_DEFINITIONS)
    ))
    assert any("has no definition" in problem for problem in problems)


def test_a_cycle_is_detected():
    from engine.logic.node_definitions import catalogue

    cyclic = {"alpha.node": "beta.node", "beta.node": "alpha.node"}
    problems = _with_alias_table(catalogue, cyclic, lambda: validate_node_id_aliases(None))
    assert any("chain" in problem or "cycle" in problem for problem in problems)


def test_a_self_alias_is_detected():
    from engine.logic.node_definitions import catalogue

    problems = _with_alias_table(
        catalogue, {"loop.node": "loop.node"}, lambda: validate_node_id_aliases(None)
    )
    assert any("self-alias" in problem for problem in problems)


def _with_alias_table(module, table, call):
    """Swap the table, run, and always put the original back.

    The catalogue is a process singleton, so a leaked mutation would poison
    every test that runs afterwards.
    """
    original = module.NODE_ID_ALIASES
    module.NODE_ID_ALIASES = table
    try:
        return call()
    finally:
        module.NODE_ID_ALIASES = original


def test_the_singleton_survived_the_mutations():
    """Run last-ish: prove the swaps above restored the real table."""
    assert validate_node_id_aliases(set(NODE_DEFINITIONS)) == []
    assert dict(all_aliases()) and sorted(_reported()) == sorted(NODE_ID_ALIASES.items())
