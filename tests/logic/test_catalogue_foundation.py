"""The node catalogue's foundation: discovery, ownership, and the read-only view.

PHASE 9 recovery item 1.

Three properties are pinned here, each because it failed silently before:

* **Discovery.** The declarative modules were a hand-written tuple. A module
  could be added to the package and simply not exist as far as the palette was
  concerned -- no error, because nothing compared the tuple to the directory.
  Stage 1's ``math_nodes``, ``logic_nodes`` and ``scene_nodes`` were exactly
  that: present on disk, absent from the catalogue.
* **Ownership.** Two modules declaring one id used to be last-write-wins, which
  is how ``play_animation`` existed twice with incompatible port contracts --
  the palette showing one, the MetadataManager holding the other.
* **The compatibility view.** ``NODE_DEFINITIONS`` is derived. If it accepts
  writes it becomes a second source of truth again.

The discovery gate is deliberately generic: it compares the catalogue against
what is on disk *now*, so a module added tomorrow is covered without editing
this file. Named assertions for the Stage 1 modules exist as well, but they are
the illustration, not the gate.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.logic.node_definitions import (
    DECLARATIVE_DEFINITION_MODULES,
    DECLARATIVE_IMPORT_FAILURES,
    NODE_DEFINITIONS,
    DuplicateNodeDefinitionError,
    assert_no_duplicate_definitions,
    definition_owner,
    duplicate_definition_conflicts,
    ensure_catalogue_loaded,
)
from engine.logic.node_definitions.catalogue import (
    _discover_declarative_modules,
    reset_discovery_cache_for_tests,
)
from engine.logic.node_definitions.registry import NodeDefinitionRegistry, get_registry

PACKAGE_DIR = Path(__file__).resolve().parents[2] / "engine" / "logic" / "node_definitions"


def _modules_on_disk() -> set[str]:
    return {
        path.stem for path in PACKAGE_DIR.glob("*_nodes.py")
        if not path.stem.startswith("_")
    }


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def test_every_declarative_module_on_disk_is_discovered():
    """The generic gate. Add a *_nodes.py and it is in the catalogue, or this fails."""
    missing = _modules_on_disk() - set(DECLARATIVE_DEFINITION_MODULES)
    assert not missing, (
        f"declarative modules on disk that the catalogue ignores: {sorted(missing)}"
    )


def test_discovery_declares_no_module_that_does_not_exist():
    phantom = set(DECLARATIVE_DEFINITION_MODULES) - _modules_on_disk()
    assert not phantom, f"catalogue declares modules that are not on disk: {sorted(phantom)}"


def test_no_declarative_module_failed_to_import():
    """An import failure is recorded, never swallowed -- and must be empty here."""
    assert DECLARATIVE_IMPORT_FAILURES == {}, (
        f"declarative modules failed to import: {DECLARATIVE_IMPORT_FAILURES}. "
        "Each one takes its whole domain out of the palette."
    )


def test_discovery_is_deterministic():
    reset_discovery_cache_for_tests()
    first = _discover_declarative_modules()
    reset_discovery_cache_for_tests()
    second = _discover_declarative_modules()
    assert first == second
    assert list(first) == sorted(first), "discovery order depends on the filesystem"


def test_discovery_is_idempotent_and_cached():
    first = _discover_declarative_modules()
    assert _discover_declarative_modules() is first, "discovery is not cached per process"


def test_there_are_more_than_a_handful_of_modules():
    """Guards against a discovery bug that silently finds nothing."""
    assert len(DECLARATIVE_DEFINITION_MODULES) >= 20, DECLARATIVE_DEFINITION_MODULES


# ---------------------------------------------------------------------------
# Stage 1 modules -- the illustration, not the gate
# ---------------------------------------------------------------------------

STAGE1_MODULES = ("math_nodes", "logic_nodes", "scene_nodes")

#: A sample of what those modules bring. Not exhaustive on purpose.
STAGE1_NODES = {
    "absolute_number": "math_nodes",
    "clamp_number": "math_nodes",
    "random_number": "math_nodes",
    "multiply_number": "math_nodes",
    "and": "logic_nodes",
    "or": "logic_nodes",
    "not": "logic_nodes",
    "delta_time": "logic_nodes",
    "to_text": "logic_nodes",
    "join_text": "logic_nodes",
    "get_position": "scene_nodes",
}


@pytest.mark.parametrize("module_name", STAGE1_MODULES)
def test_the_stage1_module_is_present_and_loaded(module_name: str):
    assert (PACKAGE_DIR / f"{module_name}.py").is_file(), "the module is not on disk"
    assert module_name in DECLARATIVE_DEFINITION_MODULES


@pytest.mark.parametrize("node_id,owner", sorted(STAGE1_NODES.items()))
def test_the_stage1_node_reached_the_catalogue(node_id: str, owner: str):
    assert node_id in NODE_DEFINITIONS, f"{node_id} is missing from the palette"
    assert definition_owner(node_id) == owner


# ---------------------------------------------------------------------------
# Ownership and duplicates
# ---------------------------------------------------------------------------

def test_the_real_catalogue_has_no_unscheduled_duplicate_ids():
    """PHASE 9 recovery item 4.1 changed what this can honestly assert.

    It used to read ``duplicate_definition_conflicts() == []`` and pass -- while
    play_animation and stop_animation were each declared twice. The harvest
    collapsed the claims into a dict before the registry saw them, so the list
    was empty because nothing was ever recorded, not because nothing was wrong.

    The claims now reach the registry, so the real duplicates are visible. They
    are recorded in KNOWN_DUPLICATE_DEFINITIONS and resolved in item 4.2;
    anything else still raises. See tests/logic/test_duplicate_definition_detection.py
    for the proof that a new duplicate fails the real build.
    """
    from engine.logic.node_definitions import KNOWN_DUPLICATE_DEFINITIONS

    recorded = {node_id for node_id, _first, _second in duplicate_definition_conflicts()}
    assert recorded == set(KNOWN_DUPLICATE_DEFINITIONS)
    assert_no_duplicate_definitions()  # must not raise for the scheduled ones


def test_every_declarative_node_has_exactly_one_owner():
    ensure_catalogue_loaded()
    for node_id in get_registry().all_canonical():
        owner = definition_owner(node_id)
        assert isinstance(owner, str) and owner, f"{node_id} has no owning module"


def test_a_duplicate_id_fails_loudly():
    registry = NodeDefinitionRegistry()
    registry.set_definition_owner("probe_node", "module_a")
    registry.set_definition_owner("probe_node", "module_b")

    assert registry.definition_conflicts() == [("probe_node", "module_a", "module_b")]
    with pytest.raises(DuplicateNodeDefinitionError) as excinfo:
        registry.assert_no_duplicate_definitions()

    message = str(excinfo.value)
    for fragment in ("probe_node", "module_a", "module_b"):
        assert fragment in message, f"the error does not name {fragment}"


def test_the_first_claim_is_not_overwritten():
    """Last-write-wins is the bug; the loser must not become the owner."""
    registry = NodeDefinitionRegistry()
    registry.set_definition_owner("probe_node", "module_a")
    registry.set_definition_owner("probe_node", "module_b")
    assert registry.definition_owner("probe_node") == "module_a"


@pytest.mark.parametrize("first,second", [("module_a", "module_b"), ("module_b", "module_a")])
def test_neither_module_wins_by_loading_first(first: str, second: str):
    registry = NodeDefinitionRegistry()
    registry.set_definition_owner("probe_node", first)
    registry.set_definition_owner("probe_node", second)
    assert registry.definition_conflicts() == [("probe_node", first, second)]
    with pytest.raises(DuplicateNodeDefinitionError):
        registry.assert_no_duplicate_definitions()


def test_the_same_module_reclaiming_its_own_id_is_a_no_op():
    """Discovery and catalogue builds are idempotent and re-run in tests."""
    registry = NodeDefinitionRegistry()
    for _ in range(3):
        registry.set_definition_owner("probe_node", "module_a")
    assert registry.definition_conflicts() == []
    assert registry.definition_owner("probe_node") == "module_a"
    registry.assert_no_duplicate_definitions()  # must not raise


def test_ownership_lives_only_in_the_registry():
    """No parallel _DEFINITION_OWNERS / _DEFINITION_CONFLICTS globals."""
    import engine.logic.node_definitions as package
    import engine.logic.node_definitions.catalogue as catalogue

    for module in (package, catalogue):
        for name in ("_DEFINITION_OWNERS", "_DEFINITION_CONFLICTS"):
            assert not hasattr(module, name), (
                f"{module.__name__}.{name} is a second source of truth for ownership"
            )


# ---------------------------------------------------------------------------
# Compatibility view
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("operation", ["setitem", "delitem", "update", "pop", "clear"])
def test_the_compatibility_view_rejects_writes(operation: str):
    actions = {
        "setitem": lambda: NODE_DEFINITIONS.__setitem__("injected", {}),
        "delitem": lambda: NODE_DEFINITIONS.__delitem__("add_number"),
        "update": lambda: NODE_DEFINITIONS.update({"injected": {}}),
        "pop": lambda: NODE_DEFINITIONS.pop("add_number"),
        "clear": lambda: NODE_DEFINITIONS.clear(),
    }
    with pytest.raises((TypeError, AttributeError)):
        actions[operation]()
    assert "injected" not in NODE_DEFINITIONS


def test_the_compatibility_view_reads_the_registry():
    ensure_catalogue_loaded()
    assert dict(NODE_DEFINITIONS) == dict(get_registry().definitions_view())
