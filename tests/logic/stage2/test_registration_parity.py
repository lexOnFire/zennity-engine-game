"""Booting LogicProvider must not change what the process can execute.

Before Stage 2 the provider imported a different set of runtime node modules
than ``import engine.logic.runtime`` did, and then registered ~100 definitions
by hand.  Whether a node existed therefore depended on which path ran.
"""

from __future__ import annotations

from ._probe import SNAPSHOT_SOURCE, run_in_fresh_process

BOOT_PROVIDER = """
from engine.core.context import EngineContext
from engine.logic.provider import LogicProvider

context = EngineContext.current()
if context is None:
    try:
        context = EngineContext()
    except Exception:
        context = None
if context is not None:
    LogicProvider().boot(context)
"""


def test_provider_and_non_provider_register_the_same_nodes():
    without = run_in_fresh_process(SNAPSHOT_SOURCE)
    with_provider = run_in_fresh_process(BOOT_PROVIDER + SNAPSHOT_SOURCE)

    for key in ("definitions", "port_schema", "executors", "evaluators", "modules"):
        assert without[key] == with_provider[key], (
            f"{key} differ between the non-provider and provider paths:\n"
            f"  only without provider: {sorted(set(without[key]) - set(with_provider[key]))}\n"
            f"  only with provider:    {sorted(set(with_provider[key]) - set(without[key]))}"
        )


def test_neither_path_reports_contract_violations():
    assert run_in_fresh_process(SNAPSHOT_SOURCE)["violations"] == []
    assert run_in_fresh_process(BOOT_PROVIDER + SNAPSHOT_SOURCE)["violations"] == []


def test_every_shipping_runtime_module_loads_without_a_provider(baseline):
    """The non-provider path used to load 13 of 23 modules."""
    snapshot = run_in_fresh_process(SNAPSHOT_SOURCE)
    assert len(snapshot["modules"]) == baseline["counts"]["runtime_modules_on_disk"]
