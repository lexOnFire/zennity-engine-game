"""Phase 5B.2: Physics Event Dispatch for Logic Graphs

Provides registration/dispatch mechanism for physics events from PhysicsWorld
to Logic Graph runtimes.
"""

from __future__ import annotations
from typing import Any, Callable


# Global registry of physics event handlers
_physics_event_handlers: list[Callable[[Any, str, Any], None]] = []


def register_physics_event_handler(callback: Callable[[Any, str, Any], None]) -> None:
    """Register a handler to receive physics events (collision/trigger).

    Callback signature: callback(game_object, method_name, other_collider)
    where method_name is in ("on_collision_enter", "on_collision_exit", "on_trigger_enter", "on_trigger_exit")
    """
    if callback not in _physics_event_handlers:
        _physics_event_handlers.append(callback)


def unregister_physics_event_handler(callback: Callable[[Any, str, Any], None]) -> None:
    """Unregister a physics event handler."""
    if callback in _physics_event_handlers:
        _physics_event_handlers.remove(callback)


def dispatch_physics_event(game_object: Any, method_name: str, other_collider: Any) -> None:
    """Dispatch physics event to all registered handlers."""
    for handler in list(_physics_event_handlers):
        try:
            handler(game_object, method_name, other_collider)
        except Exception:
            pass
