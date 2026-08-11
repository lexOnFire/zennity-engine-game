"""The status and describe APIs answer ownership questions without Qt."""

from __future__ import annotations

from engine.logic.node_system import (
    RUNTIME_NODE_MODULES,
    describe_node,
    get_node_system_status,
    runtime_node_modules_on_disk,
    validate_node_system,
)


def test_status_has_no_contract_violations():
    assert list(get_node_system_status()["contract_violations"]) == []
    assert validate_node_system() == []


def test_every_module_on_disk_is_declared():
    assert sorted(runtime_node_modules_on_disk()) == sorted(RUNTIME_NODE_MODULES)


def test_status_reports_the_full_shape():
    status = get_node_system_status()
    for key in (
        "definitions",
        "port_schema",
        "executors",
        "evaluators",
        "runtime_modules_loaded",
        "duplicate_owners",
        "contract_violations",
        "schema_drift",
        "aliases",
        "execution_models",
    ):
        assert key in status, key
    assert status["runtime_module_load_failures"] == {}


def test_status_is_importable_without_qt():
    """A viewport subprocess and a CI gate both need this to be Qt-free."""
    import sys

    import engine.logic.node_system  # noqa: F401

    assert not any(name.startswith("PySide6") for name in sys.modules), (
        "importing the node system pulled in Qt"
    )


def test_describe_node_answers_ownership():
    described = describe_node("move_by")
    assert described["exists"]
    assert described["execution_model"] == "flow"
    assert described["runtime_owner_module"] == "engine.logic.runtime.nodes.movement_nodes"
    assert described["has_executor"]
    assert ("in", "flow") in described["inputs"]


def test_describe_node_reports_execution_models():
    assert describe_node("event_update")["execution_model"] == "event"
    assert describe_node("if_else")["execution_model"] == "branch"
    assert describe_node("add_number")["execution_model"] == "pure"
    assert describe_node("destroy_object")["execution_model"] == "terminal"


def test_describe_node_reports_aliases():
    assert "input.axis" in describe_node("input_axis")["aliases"]
    assert "variables.set" in describe_node("set_variable")["aliases"]


def test_aliases_do_not_create_definitions_or_palette_entries():
    from engine.logic.node_definitions.catalogue import RUNTIME_ID_ALIASES

    status = get_node_system_status()
    for alias in RUNTIME_ID_ALIASES:
        assert alias not in status["definition_ids"], f"alias {alias} leaked into the palette"
        assert alias not in status["port_schema_ids"], f"alias {alias} got its own contract"


def test_unknown_node_is_reported_as_missing():
    described = describe_node("definitely_not_a_node")
    assert not described["exists"]
