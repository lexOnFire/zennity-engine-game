"""Boot-time validation of the node catalogue.

Phase 9.5B Stage 1, item 18.  The editor must not start silently on a corrupt
catalogue.  Severity policy:

    duplicate node id      -> hard failure (raises)
    contract violation     -> ERROR log, boot continues
    deprecated node/alias  -> WARNING log

Called from ``LogicProvider.boot``.  Cheap: it reads the already-built
catalogue and the already-populated registry, and does no imports of its own
beyond what boot has already loaded.
"""
from __future__ import annotations

from typing import Any

from engine.diagnostics import get_logger
from engine.logic.contracts import (
    DefinitionContract,
    ExecutionModel,
    RuntimeContract,
    Severity,
    summarise,
    validate_catalogue,
)

_log = get_logger("logic")


def _definition_contracts() -> dict[str, DefinitionContract]:
    from engine.logic.node_definitions import NODE_DEFINITIONS

    out: dict[str, DefinitionContract] = {}
    for node_id, entry in NODE_DEFINITIONS.items():
        raw_model = str(entry.get("execution_model", "action") or "action")
        try:
            model = ExecutionModel(raw_model)
        except ValueError:
            model = ExecutionModel.ACTION
        out[node_id] = DefinitionContract(
            node_id=node_id,
            inputs=_pins(entry, "inputs"),
            outputs=_pins(entry, "outputs"),
            properties=set((entry.get("properties") or {}).keys()),
            execution_model=model,
            deprecated=bool(entry.get("deprecated")),
            dynamic_prefixes=tuple(entry.get("dynamic_exec_prefixes") or ()),
        )
    return out


def _pins(entry: dict, key: str) -> list[tuple[str, str]]:
    pins: list[tuple[str, str]] = []
    for pin in entry.get(key, []) or []:
        if isinstance(pin, (tuple, list)) and len(pin) >= 2:
            pins.append((str(pin[0]), str(pin[1]).lower()))
        elif isinstance(pin, str):
            pins.append((pin, "any"))
    return pins


def _runtime_contracts() -> dict[str, RuntimeContract]:
    """What the live registry knows.

    Port-level usage (reads/stores/returns) is only recoverable by static
    analysis, which belongs to the audit tool -- at boot we can still catch the
    structural problems: handlers with no definition and definitions with no
    handler.
    """
    from engine.logic.runtime.registry import registry

    out: dict[str, RuntimeContract] = {}
    for node_id in set(registry.executors) | set(registry.evaluators):
        out[node_id] = RuntimeContract(
            node_id=node_id,
            has_executor=node_id in registry.executors,
            has_evaluator=node_id in registry.evaluators,
        )
    return out


def validate_catalogue_at_boot(*, strict: bool = False) -> list[Any]:
    """Validate the catalogue.  Returns the violations found.

    Raises ``DuplicateNodeDefinitionError`` on duplicate ids -- always, in every
    mode.  ``strict=True`` additionally turns any ERROR-severity violation into
    a raise (used by tests and CI, not by the shipping editor).
    """
    from engine.logic.node_definitions import assert_no_duplicate_definitions

    # Duplicate ids are never tolerable: two definitions of one node mean the
    # palette and the runtime can disagree about the same id.
    assert_no_duplicate_definitions()

    definitions = _definition_contracts()
    runtimes = _runtime_contracts()

    # Structural pass only: a full port-contract check needs static analysis.
    violations = [
        v for v in validate_catalogue(definitions, runtimes)
        if v.kind in {"NO_RUNTIME", "NO_DEFINITION", "ALIAS_WITHOUT_TARGET"}
    ]

    errors = [v for v in violations if v.severity is Severity.ERROR]
    warnings = [v for v in violations if v.severity is Severity.WARNING]

    for v in warnings:
        _log.warning("Node catalogue: %s", v)
    for v in errors:
        _log.error("Node catalogue: %s", v)

    if errors:
        _log.error(
            "Node catalogue validated with %d error(s): %s",
            len(errors), summarise(errors),
        )
        if strict:
            raise RuntimeError(
                "Node catalogue contract violations:\n  "
                + "\n  ".join(str(v) for v in errors)
            )
    else:
        _log.info(
            "Node catalogue validated: %d definitions, %d runtime handlers, no errors",
            len(definitions), len(runtimes),
        )
    return violations
