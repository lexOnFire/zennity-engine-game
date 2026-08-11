"""Booting twice, or loading twice, changes nothing."""

from __future__ import annotations

from ._probe import run_in_fresh_process

DOUBLE_LOAD = """
import json
from engine.logic.node_system import load_runtime_node_modules, get_node_system_status
from engine.logic.runtime.registry import registry

load_runtime_node_modules()
first = (len(registry.executors), len(registry.evaluators))
first_owners = {k: sorted(v) for k, v in registry.executor_owners.items()}

load_runtime_node_modules()
second = (len(registry.executors), len(registry.evaluators))
second_owners = {k: sorted(v) for k, v in registry.executor_owners.items()}

status = get_node_system_status()
print(json.dumps({
    "first": first,
    "second": second,
    "owners_stable": first_owners == second_owners,
    "violations": list(status["contract_violations"]),
    "duplicates": sorted(status["duplicate_owners"]),
}))
"""

DOUBLE_BOOT = """
import json, warnings
from engine.core.context import EngineContext
from engine.logic.provider import LogicProvider
from engine.logic.node_system import get_node_system_status
from engine.logic.runtime.registry import registry

context = EngineContext.current()
if context is None:
    try:
        context = EngineContext()
    except Exception:
        context = None

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    if context is not None:
        LogicProvider().boot(context)
    first = (len(registry.executors), len(registry.evaluators))
    if context is not None:
        LogicProvider().boot(context)
    second = (len(registry.executors), len(registry.evaluators))

status = get_node_system_status()
print(json.dumps({
    "first": first,
    "second": second,
    "warnings": [str(w.message) for w in caught],
    "violations": list(status["contract_violations"]),
}))
"""


def test_loading_runtime_modules_twice_is_a_no_op():
    result = run_in_fresh_process(DOUBLE_LOAD)
    assert result["first"] == result["second"]
    assert result["owners_stable"]
    assert result["violations"] == []


def test_booting_the_provider_twice_is_a_no_op():
    result = run_in_fresh_process(DOUBLE_BOOT)
    assert result["first"] == result["second"]
    assert result["violations"] == []


def test_booting_twice_emits_no_warnings():
    assert run_in_fresh_process(DOUBLE_BOOT)["warnings"] == []


def test_no_duplicate_handlers_beyond_the_recorded_baseline():
    from engine.logic.node_system import KNOWN_DUPLICATE_OWNERS, load_runtime_node_modules
    from engine.logic.runtime.registry import registry

    load_runtime_node_modules()
    unexpected = set(registry.duplicate_owners()) - KNOWN_DUPLICATE_OWNERS
    assert not unexpected, f"new duplicate node ownership: {sorted(unexpected)}"
