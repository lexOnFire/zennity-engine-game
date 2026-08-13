"""The Logic Graph node system -- one catalogue, one loader, one status API.

PHASE 9.5B Stage 2.

Before this module there were two independent ways to get runtime node
implementations into the process:

* ``engine/logic/runtime/nodes/__init__.py`` imported 13 of the 23 shipping
  modules, and ran as a side effect of importing ``LogicGraphRuntime``;
* ``LogicProvider.boot()`` imported a *different* set of 22 modules and then
  re-registered ~100 node definitions by hand.

Whichever ran last decided what the process could execute, so the editor and
the viewport could disagree about which nodes existed.  This module replaces
both with a single declared catalogue (:data:`RUNTIME_NODE_MODULES`) and a
single idempotent loader (:func:`load_runtime_node_modules`), both of which
live in :mod:`engine.logic.runtime.node_loader` so that they travel with the
exported standalone runtime.  This module adds the catalogue-aware layer on
top: ownership metadata, contract validation and the status snapshot.

Nothing here imports Qt, pygame or the editor: the status API is safe to call
from a CI gate, from a headless probe and from the viewport subprocess alike.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from .node_definitions.catalogue import (
    DYNAMIC_PORT_NODES,
    all_aliases,
    canonical_node_id,
    definitions_view,
    ensure_catalogue_loaded,
    port_schema_view,
)
from . import node_definitions as _node_definitions_pkg  # noqa: F401
from .contracts import ExecutionModel
from .node_definitions import catalogue as _catalogue
from .node_definitions.registry import get_registry
from .runtime.node_loader import (
    RUNTIME_NODE_MODULES,
    load_failures,
    load_runtime_node_modules,
    loaded_runtime_node_modules,
    reset_runtime_loader_for_tests,
    runtime_node_modules_on_disk,
)

# ---------------------------------------------------------------------------
# Owner metadata / diagnostics
# ---------------------------------------------------------------------------


#: Node ids that two shipping modules have both claimed since before Stage 2.
#: Load order is deterministic, so the winner is stable and unchanged; these are
#: recorded rather than resolved because picking the other implementation would
#: change gameplay.  The CI gate fails on any duplicate NOT listed here.
KNOWN_DUPLICATE_OWNERS: frozenset[str] = frozenset({
    "executor:play_animation",   # animation_nodes wins over actions_nodes
    "executor:stop_animation",   # animation_nodes wins over actions_nodes
    "executor:load_game",        # scene_nodes wins over save_load_nodes
    "executor:has_save",         # scene_nodes wins over save_load_nodes
})


def _aliases_for(node_id: str) -> tuple[str, ...]:
    return all_aliases().get(node_id, ())


def _migration_ids_for(node_id: str) -> tuple[str, ...]:
    """Pre-1.0 visual-script types that migrate onto ``node_id``.

    Reported apart from ``aliases`` because it is a different mechanism: these
    ids are rewritten when a legacy-format document is loaded, and they are not
    resolvable by ``resolve_node_id``. Some of the map's targets do not exist as
    definitions at all -- the migration degrades on purpose.
    """
    try:
        from .legacy_visual_script import LEGACY_NODE_TYPES
    except Exception:  # pragma: no cover - the migration module is optional
        return ()
    return tuple(sorted(
        source for source, target in LEGACY_NODE_TYPES.items()
        if target == node_id and source not in _catalogue.NODE_ID_ALIASES
    ))


def describe_node(node_id: str) -> Mapping[str, Any]:
    """Read-only description of where a node comes from and what it is.

    Answers, for a single node id: which module declared its definition, which
    module implements it at runtime, its execution model, and the legacy ids
    that normalize onto it.
    """
    ensure_catalogue_loaded()
    load_runtime_node_modules()
    from .runtime.registry import registry as handler_registry

    registry = get_registry()
    definition = registry.definitions_view().get(node_id)
    schema = port_schema_view().get(node_id)
    return MappingProxyType(
        {
            "id": node_id,
            "exists": definition is not None or schema is not None,
            "title": (definition or {}).get("title", node_id),
            "category": (definition or {}).get("category", ""),
            "definition_owner_module": registry.definition_owner(node_id),
            "runtime_owner_module": registry.runtime_owner(node_id),
            "execution_model": registry.execution_model(node_id),
            "deprecated": bool(definitions_view().get(node_id, {}).get("deprecated", False)),
            # Read through the module so the merged table built at catalogue
            # time is what answers, not the seed captured at import time.
            "dynamic_exec_prefixes": tuple(
                _catalogue.DYNAMIC_PORT_NODES.get(node_id, ())
            ),
            # ``aliases`` are node ids that resolve onto this one -- every entry
            # here satisfies resolve_node_id(alias) == node_id.
            "aliases": _aliases_for(node_id),
            # PHASE 9 recovery item 12: ids that reach this node only through
            # the pre-1.0 visual-script *migration*, which is a different
            # mechanism and used to be reported as if it were aliasing. Keeping
            # them under their own name loses no diagnostic and stops the two
            # from being confused -- that confusion is how ``variable.set``
            # looked handled while the resolver could not resolve it.
            "legacy_migration_ids": _migration_ids_for(node_id),
            "has_executor": node_id in handler_registry.executors,
            "has_evaluator": node_id in handler_registry.evaluators,
            "inputs": tuple(tuple(p) for p in (schema or {}).get("inputs", [])),
            "outputs": tuple(tuple(p) for p in (schema or {}).get("outputs", [])),
            "in_palette": node_id in registry.definitions_view(),
        }
    )


def validate_node_system() -> list[str]:
    """Return contract violations.  Empty list means the node system is sound.

    A violation is a structural inconsistency, not a missing implementation:
    nodes without executors are legal (pure data nodes are evaluated, event
    nodes are driven by the runtime).
    """
    ensure_catalogue_loaded()
    load_runtime_node_modules()
    from .runtime.registry import registry as handler_registry

    registry = get_registry()
    violations: list[str] = []

    for node_id in registry.schema_drift():
        violations.append(
            f"{node_id}: definition pins disagree with the port schema "
            "(an independent port table was re-introduced)"
        )

    declared = set(RUNTIME_NODE_MODULES)
    on_disk = set(runtime_node_modules_on_disk())
    for module_name in sorted(on_disk - declared):
        violations.append(
            f"runtime module '{module_name}' exists on disk but is missing from "
            "RUNTIME_NODE_MODULES"
        )
    for module_name in sorted(declared - on_disk):
        violations.append(
            f"runtime module '{module_name}' is declared in RUNTIME_NODE_MODULES "
            "but has no file on disk"
        )
    for module_name, error in sorted(load_failures().items()):
        violations.append(f"runtime module '{module_name}' failed to import: {error}")

    for key, owners in sorted(handler_registry.duplicate_owners().items()):
        if key in KNOWN_DUPLICATE_OWNERS:
            continue
        violations.append(f"{key}: claimed by multiple modules {owners}")

    schema = port_schema_view()
    for kind, handlers in (
        ("executor", handler_registry.executors),
        ("evaluator", handler_registry.evaluators),
    ):
        for node_id in sorted(handlers):
            if canonical_node_id(node_id) not in schema:
                violations.append(
                    f"{node_id}: has a runtime {kind} but no port contract in the catalogue"
                )

    return violations


def _runtime_required(model: str) -> str:
    """Which registry has to back a node with this execution model.

    PHASE 9 recovery item 11. ``executor or evaluator`` was not a definition of
    coverage, it was a definition of *something exists*: an ACTION declares flow
    pins, and only an executor can return them, so an evaluator satisfied the
    check while the node's flow was still unbacked.

    Structural on purpose -- the answer comes from the model, never from a node
    id, so a node added tomorrow is judged by the contract it declares.
    """
    if model == ExecutionModel.PURE_DATA.value:
        return "evaluators"
    if model == ExecutionModel.EVENT_SOURCE.value:
        # The frame loop dispatches these; demanding an executor would need the
        # drifting list of event ids that execution_model exists to abolish.
        return ""
    # ACTION and TERMINAL both continue (or deliberately stop) flow, and both
    # do it by returning ports from an executor.
    return "executors"


def classify_runtime_coverage() -> dict[str, list[str]]:
    """Group palette nodes by whether the runtime backs them, using their model.

    PHASE 9 recovery item 3, corrected by item 11. "Definition with no executor"
    is not one situation:

    * EVENT_SOURCE legitimately has none -- the frame loop dispatches it;
    * PURE_DATA is resolved by an evaluator;
    * DEPRECATED is a decision already recorded on the definition;
    * ACTION and TERMINAL need an executor, and an evaluator is not a
      substitute: their flow ports can only be returned by one.

    Classification is by declared/derived model and by the deprecated flag. No
    node id appears anywhere in this function on purpose.
    """
    ensure_catalogue_loaded()
    load_runtime_node_modules()
    from .runtime.registry import registry as handler_registry

    registry = get_registry()
    definitions = definitions_view()
    grouped: dict[str, list[str]] = {
        "backed": [], "event_source_without_executor": [],
        "deprecated_without_runtime": [], "missing_runtime": [],
    }
    for node_id in sorted(definitions):
        model = registry.execution_model(node_id)
        required = _runtime_required(model)
        has_runtime = not required or node_id in getattr(handler_registry, required)
        if has_runtime:
            if required:
                grouped["backed"].append(node_id)
            else:
                grouped["event_source_without_executor"].append(node_id)
            continue
        if definitions[node_id].get("deprecated"):
            grouped["deprecated_without_runtime"].append(node_id)
        else:
            grouped["missing_runtime"].append(node_id)
    return grouped


def get_node_system_status() -> Mapping[str, Any]:
    """Full, Qt-free snapshot of the node system for diagnostics and CI."""
    ensure_catalogue_loaded()
    load_runtime_node_modules()
    from .runtime.registry import registry as handler_registry

    registry = get_registry()
    definitions = registry.definitions_view()
    schema = port_schema_view()

    duplicate_owners = handler_registry.duplicate_owners()

    return MappingProxyType(
        {
            "definitions": len(definitions),
            "port_schema": len(schema),
            "executors": len(handler_registry.executors),
            "evaluators": len(handler_registry.evaluators),
            "definition_ids": tuple(sorted(definitions)),
            "port_schema_ids": tuple(sorted(schema)),
            "executor_ids": tuple(sorted(handler_registry.executors)),
            "evaluator_ids": tuple(sorted(handler_registry.evaluators)),
            "runtime_modules_declared": RUNTIME_NODE_MODULES,
            "runtime_modules_on_disk": runtime_node_modules_on_disk(),
            "runtime_modules_loaded": loaded_runtime_node_modules(),
            "runtime_module_load_failures": MappingProxyType(load_failures()),
            "duplicate_owners": MappingProxyType(duplicate_owners),
            "contract_violations": tuple(validate_node_system()),
            "schema_drift": tuple(registry.schema_drift()),
            "aliases": MappingProxyType(
                {
                    node_id: _aliases_for(node_id)
                    for node_id in sorted(definitions)
                    if _aliases_for(node_id)
                }
            ),
            "runtime_coverage": MappingProxyType(
                {k: tuple(v) for k, v in classify_runtime_coverage().items()}
            ),
            "execution_models": MappingProxyType(
                {node_id: registry.execution_model(node_id) for node_id in sorted(schema)}
            ),
        }
    )


__all__ = [
    "RUNTIME_NODE_MODULES",
    "load_runtime_node_modules",
    "loaded_runtime_node_modules",
    "runtime_node_modules_on_disk",
    "reset_runtime_loader_for_tests",
    "describe_node",
    "validate_node_system",
    "get_node_system_status",
]
