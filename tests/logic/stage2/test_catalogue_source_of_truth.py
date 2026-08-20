"""There is exactly one mutable definition store."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from engine.logic.graph_asset import NODE_DEFINITIONS, NODE_PORT_DEFINITIONS
from engine.logic.node_definitions.catalogue import (
    definitions_view,
    ensure_catalogue_loaded,
    port_schema_view,
)
from engine.logic.node_definitions.registry import get_registry

from ._probe import POST_BASELINE_DEFINITIONS


def test_node_definitions_is_a_read_only_view():
    with pytest.raises(TypeError):
        NODE_DEFINITIONS["injected_node"] = {}  # type: ignore[index]


def test_node_port_definitions_is_a_read_only_view():
    with pytest.raises(TypeError):
        NODE_PORT_DEFINITIONS["injected_node"] = {}  # type: ignore[index]


def test_views_are_backed_by_the_registry_not_by_copies():
    ensure_catalogue_loaded()
    registry = get_registry()
    assert isinstance(registry.definitions_view(), MappingProxyType)
    assert isinstance(registry.port_schema_view(), MappingProxyType)
    assert dict(definitions_view()) == dict(registry.definitions_view())
    assert dict(port_schema_view()) == dict(registry.port_schema_view())


def test_registry_is_populated():
    """The registry used to exist but stay empty -- the catalogue bypassed it."""
    ensure_catalogue_loaded()
    registry = get_registry()
    assert len(registry.definitions_view()) > 100
    assert len(registry.port_schema_view()) > 100


def test_every_definition_keeps_the_baseline_identity(baseline):
    """Stage 2 must not change which nodes the editor offers.

    Losing a node is always a regression. Gaining one is not -- the palette has
    grown deliberately since the snapshot -- so additions are checked against
    the declared list rather than forbidden outright, and the snapshot stays a
    faithful record of commit 477feee.
    """
    recorded = set(baseline["definition_ids"])
    current = set(NODE_DEFINITIONS)

    assert not recorded - current, (
        f"the palette lost node types: {sorted(recorded - current)}. Stage 2 "
        "must not remove nodes the editor already offered."
    )
    assert current - recorded == set(POST_BASELINE_DEFINITIONS), (
        "the palette gained node types nobody declared: "
        f"{sorted((current - recorded) - POST_BASELINE_DEFINITIONS)}. Add them to "
        "POST_BASELINE_DEFINITIONS with the commit that introduced them."
    )


def test_building_the_catalogue_twice_is_stable():
    from engine.logic.node_definitions.catalogue import reset_catalogue_for_tests

    before = {k: dict(v) for k, v in definitions_view().items()}
    before_schema = {k: dict(v) for k, v in port_schema_view().items()}
    reset_catalogue_for_tests()
    ensure_catalogue_loaded()
    assert {k: dict(v) for k, v in definitions_view().items()} == before
    assert {k: dict(v) for k, v in port_schema_view().items()} == before_schema
