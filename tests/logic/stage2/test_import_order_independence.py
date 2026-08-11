"""Whichever module is imported first, the process ends up in the same state.

There used to be no answer to "which nodes exist?" -- only "which nodes exist
given what happened to get imported first".
"""

from __future__ import annotations

import pytest

from ._probe import SNAPSHOT_SOURCE, run_in_fresh_process

ORDERS = {
    "definitions_then_runtime": (
        "import engine.logic.node_definitions\n"
        "import engine.logic.runtime\n"
    ),
    "runtime_then_definitions": (
        "import engine.logic.runtime\n"
        "import engine.logic.node_definitions\n"
    ),
    "provider_then_runtime": (
        "import engine.logic.provider\n"
        "import engine.logic.runtime\n"
    ),
    "runtime_then_provider": (
        "import engine.logic.runtime\n"
        "import engine.logic.provider\n"
    ),
    "graph_asset_first": "import engine.logic.graph_asset\n",
    "node_system_first": "import engine.logic.node_system\n",
}


@pytest.mark.parametrize("name", sorted(ORDERS))
def test_import_order_produces_the_same_state(name):
    reference = run_in_fresh_process(ORDERS["definitions_then_runtime"] + SNAPSHOT_SOURCE)
    candidate = run_in_fresh_process(ORDERS[name] + SNAPSHOT_SOURCE)
    for key in ("definitions", "port_schema", "executors", "evaluators", "modules"):
        assert reference[key] == candidate[key], (
            f"import order '{name}' changed {key}; last write is winning somewhere"
        )
