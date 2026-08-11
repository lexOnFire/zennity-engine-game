"""The port schema is derived from the definitions, not maintained beside them."""

from __future__ import annotations

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    node_port_definitions,
)
from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
from engine.logic.node_definitions.registry import get_registry


def _pins(sequence):
    return [tuple(pin) for pin in sequence]


def test_no_schema_drift():
    """A definition's pins and its port schema entry are the same list."""
    ensure_catalogue_loaded()
    assert get_registry().schema_drift() == []


def test_every_definition_agrees_with_the_port_schema():
    for node_id, definition in NODE_DEFINITIONS.items():
        schema = NODE_PORT_DEFINITIONS[node_id]
        assert _pins(definition["inputs"]) == _pins(schema["inputs"]), node_id
        assert _pins(definition["outputs"]) == _pins(schema["outputs"]), node_id


def test_pre_stage2_graph_contract_is_reproduced_exactly(baseline):
    """Every port contract that shipped before Stage 2 still resolves identically.

    This is the regression that matters: ``.zlogic`` assets and runtime
    executors speak these pin names, so deriving the schema is only correct if
    the derived result is byte-identical to what the hand-maintained table held.
    """
    for node_id, contract in baseline["port_schema"].items():
        assert node_id in NODE_PORT_DEFINITIONS, f"{node_id} lost its port contract"
        actual = NODE_PORT_DEFINITIONS[node_id]
        assert _pins(actual["inputs"]) == _pins(contract["inputs"]), node_id
        assert _pins(actual["outputs"]) == _pins(contract["outputs"]), node_id


def test_diverged_definitions_were_realigned_onto_the_graph_contract(baseline):
    """The 52 nodes whose definition disagreed with the schema now agree.

    They disagreed because the declarative NodeDefinition objects used
    ``exec``/``exec_done`` pins that no asset and no executor ever spoke, while
    graph_normalizer seeded node properties from those same pins.
    """
    diverged = baseline["diverged_node_ids"]
    assert diverged, "baseline fixture is missing the divergence record"
    for node_id in diverged:
        contract = baseline["port_schema"][node_id]
        assert _pins(NODE_DEFINITIONS[node_id]["inputs"]) == _pins(contract["inputs"]), node_id
        assert _pins(NODE_DEFINITIONS[node_id]["outputs"]) == _pins(contract["outputs"]), node_id


def test_node_port_definitions_helper_still_returns_mutable_copies():
    """Consumers mutate the result (dynamic pins); the view must not leak."""
    ports = node_port_definitions("sequence")
    ports["inputs"].append(("injected", "flow"))
    assert ("injected", "flow") not in NODE_PORT_DEFINITIONS["sequence"]["inputs"]


def test_dynamic_ports_still_expand_from_properties():
    node = {"type": "sequence", "properties": {"outputs": 4}}
    outputs = [pin for pin, _kind in node_port_definitions(node)["outputs"]]
    assert outputs == ["then_0", "then_1", "then_2", "then_3", "next"]
