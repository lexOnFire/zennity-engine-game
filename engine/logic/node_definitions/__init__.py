"""Node definition metadata for the Logic Graph editor.

PHASE 9.5B Stage 2 -- this package no longer owns a mutable dictionary.

``NODE_DEFINITIONS`` used to be an independent dict built here and then further
mutated by :mod:`engine.logic.graph_asset`, in parallel with a second
hand-maintained table (``NODE_PORT_DEFINITIONS``).  The two drifted apart for 52
node types, which is how nodes ended up seeded with properties their executors
never read.

The catalogue is now built once, into
:class:`~engine.logic.node_definitions.registry.NodeDefinitionRegistry`, by
:mod:`engine.logic.node_definitions.catalogue`.  What follows is a read-only
view over that store.

This package still shadows the legacy sibling module
``engine/logic/node_definitions.py``; Python resolves the package first, which
is why the legacy module is dead code.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .catalogue import (
    DECLARATIVE_DEFINITION_MODULES,
    DECLARATIVE_IMPORT_FAILURES,
    DYNAMIC_PORT_NODES,
    _migrate_category,
    definitions_view,
    ensure_catalogue_loaded,
    port_schema_view,
    reset_catalogue_for_tests,
)
from .registry import DuplicateNodeDefinitionError, get_registry


def definition_owner(node_id: str) -> str | None:
    """Which declarative module declared ``node_id``."""
    ensure_catalogue_loaded()
    return get_registry().definition_owner(node_id)


def duplicate_definition_conflicts() -> list[tuple[str, str, str]]:
    """Recorded (node_id, first_owner, second_owner) clashes."""
    ensure_catalogue_loaded()
    return get_registry().definition_conflicts()


def assert_no_duplicate_definitions() -> None:
    """Raise :class:`DuplicateNodeDefinitionError` if any id has two owners."""
    ensure_catalogue_loaded()
    get_registry().assert_no_duplicate_definitions()


class _NodeDefinitionsView(Mapping):
    """COMPATIBILITY VIEW -- DO NOT EDIT.

    Derived from ``NodeDefinitionRegistry``.  Reads build the catalogue on
    first access; writes are rejected.  Mutate the seeds in
    :mod:`engine.logic.node_definitions.catalogue` instead.
    """

    __slots__ = ()

    def _store(self) -> Mapping[str, dict[str, Any]]:
        return definitions_view()

    def __getitem__(self, key: str) -> dict[str, Any]:
        return self._store()[key]

    def __iter__(self):
        return iter(self._store())

    def __len__(self) -> int:
        return len(self._store())

    def __contains__(self, key: object) -> bool:
        return key in self._store()

    def __repr__(self) -> str:
        return f"<NODE_DEFINITIONS view: {len(self)} nodes (read-only)>"


#: COMPATIBILITY VIEW -- DO NOT EDIT.  Generated from NodeDefinitionRegistry.
NODE_DEFINITIONS: Mapping[str, dict[str, Any]] = _NodeDefinitionsView()

__all__ = [
    "NODE_DEFINITIONS",
    "DECLARATIVE_DEFINITION_MODULES",
    "DECLARATIVE_IMPORT_FAILURES",
    "DuplicateNodeDefinitionError",
    "definition_owner",
    "duplicate_definition_conflicts",
    "assert_no_duplicate_definitions",
    "DYNAMIC_PORT_NODES",
    "definitions_view",
    "port_schema_view",
    "ensure_catalogue_loaded",
    "reset_catalogue_for_tests",
]
