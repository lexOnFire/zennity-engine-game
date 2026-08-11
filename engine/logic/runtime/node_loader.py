"""The one catalogue of shipping runtime node modules, and the one loader.

PHASE 9.5B Stage 2.

There used to be two independent ways to get runtime node implementations into
a process:

* ``engine/logic/runtime/nodes/__init__.py`` imported 13 of the 23 shipping
  modules, as a side effect of importing ``LogicGraphRuntime``;
* ``LogicProvider.boot()`` imported a *different* set of 22 modules.

Whichever ran last decided what the process could execute, so the editor and the
viewport could disagree about which nodes existed.  Both now defer to this
module; neither keeps a list.

This lives inside the runtime package rather than beside ``node_system`` on
purpose: the project exporter copies ``engine/logic/runtime`` wholesale into a
standalone game, so the canonical list travels with it and an exported game
loads exactly the modules the editor does.  Every import here is relative for
the same reason -- the exported tree is re-rooted under ``zennity_runtime``.
"""

from __future__ import annotations

import sys
import threading
from importlib import import_module
from pathlib import Path

#: The shipping runtime node modules, in load order.  This is the ONLY list.
#: A module on disk that is missing from this tuple is a CI failure, see
#: ``tools/audit_node_system.py``.
RUNTIME_NODE_MODULES: tuple[str, ...] = (
    "actions_nodes",
    "animation_nodes",
    "audio_advanced_nodes",
    "camera_nodes",
    "components_nodes",
    "dialog_nodes",
    "dynamic_ui_nodes",
    "event_nodes",
    "flow_nodes",
    "input_advanced_nodes",
    "math_nodes",
    "misc_nodes",
    "movement_nodes",
    "particle_nodes",
    "pathfinding_nodes",
    "physics_nodes",
    "prefab_nodes",
    "save_load_nodes",
    "scene_nodes",
    "state_machine_nodes",
    "string_nodes",
    "ui_binding_nodes",
    "ui_nodes",
)

_NODES_PACKAGE = f"{__package__}.nodes"

_LOAD_LOCK = threading.RLock()
_LOADED = False
_LOAD_FAILURES: dict[str, str] = {}


def load_runtime_node_modules(*, force: bool = False) -> tuple[str, ...]:
    """Import every shipping runtime node module exactly once per process.

    Executors and evaluators register themselves through the ``@registry``
    decorators at import time, so importing *is* the registration.  Repeating it
    would be harmless -- the decorator rebinds the same key to the same function
    -- but this short-circuits anyway so a second ``boot()`` does no work.

    The result does not depend on who calls first: the set is fixed by
    :data:`RUNTIME_NODE_MODULES`.
    """
    global _LOADED
    if _LOADED and not force:
        return RUNTIME_NODE_MODULES
    with _LOAD_LOCK:
        if _LOADED and not force:
            return RUNTIME_NODE_MODULES
        _LOAD_FAILURES.clear()
        for module_name in RUNTIME_NODE_MODULES:
            try:
                import_module(f"{_NODES_PACKAGE}.{module_name}")
            except Exception as exc:  # pragma: no cover - surfaced via status
                _LOAD_FAILURES[module_name] = f"{type(exc).__name__}: {exc}"
        _LOADED = True
        _record_runtime_owners()
    return RUNTIME_NODE_MODULES


def _record_runtime_owners() -> None:
    """Attribute each executor/evaluator to the module that defined it.

    Best effort: the definition registry is not part of the exported runtime's
    critical path, so a standalone game that lacks it still loads its nodes.
    """
    try:
        from ..node_definitions.registry import get_registry
    except Exception:  # pragma: no cover - exported runtime without the catalogue
        return
    from .registry import registry as handler_registry

    definition_registry = get_registry()
    for handlers in (handler_registry.executors, handler_registry.evaluators):
        for node_id, func in handlers.items():
            module_name = getattr(func, "__module__", "")
            if module_name.startswith(_NODES_PACKAGE):
                definition_registry.set_runtime_owner(node_id, module_name)


def load_failures() -> dict[str, str]:
    """Modules that were declared but failed to import, with the reason."""
    return dict(_LOAD_FAILURES)


def loaded_runtime_node_modules() -> tuple[str, ...]:
    """Runtime node modules currently present in ``sys.modules``."""
    prefix = f"{_NODES_PACKAGE}."
    return tuple(
        sorted(
            name[len(prefix) :]
            for name in sys.modules
            if name.startswith(prefix) and "." not in name[len(prefix) :]
        )
    )


def runtime_node_modules_on_disk() -> tuple[str, ...]:
    """Runtime node modules that exist as files, whether declared or not."""
    directory = Path(__file__).resolve().parent / "nodes"
    return tuple(sorted(p.stem for p in directory.glob("*.py") if p.stem != "__init__"))


def reset_runtime_loader_for_tests() -> None:
    """Allow a test to re-run the loader from a clean flag."""
    global _LOADED
    with _LOAD_LOCK:
        _LOADED = False
        _LOAD_FAILURES.clear()


__all__ = [
    "RUNTIME_NODE_MODULES",
    "load_runtime_node_modules",
    "load_failures",
    "loaded_runtime_node_modules",
    "runtime_node_modules_on_disk",
    "reset_runtime_loader_for_tests",
]
