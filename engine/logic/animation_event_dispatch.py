"""Phase 6B.3: Animation Event Dispatch for Logic Graphs

Provides registration/dispatch mechanism for animation events from Animator
to Logic Graph runtimes via LogicEventBus with owner-based routing.
"""

from __future__ import annotations
from typing import Any, Callable, Optional


# Global registry of animation event handlers
_animation_event_handlers: list[Callable[[Any, str, str, int, float], None]] = []


def register_animation_event_handler(
    callback: Callable[[Any, str, str, int, float], None]
) -> None:
    """Register a handler to receive animation events.

    Callback signature: callback(owner_object, animation_name, event_name, frame_index, elapsed_time)

    Parameters
    ----------
    callback : Callable
        Called when animation event occurs.
        - owner_object: GameObject that owns the Animator
        - animation_name: Name of the animation clip
        - event_name: Name of the animation event
        - frame_index: Frame index where event occurred
        - elapsed_time: Elapsed time in animation clip
    """
    if callback not in _animation_event_handlers:
        _animation_event_handlers.append(callback)


def unregister_animation_event_handler(
    callback: Callable[[Any, str, str, int, float], None]
) -> None:
    """Unregister an animation event handler."""
    if callback in _animation_event_handlers:
        _animation_event_handlers.remove(callback)


def dispatch_animation_event(
    owner_object: Any,
    animation_name: str,
    event_name: str,
    frame_index: int,
    elapsed_time: float,
) -> None:
    """Dispatch animation event to all registered handlers."""
    for handler in list(_animation_event_handlers):
        try:
            handler(owner_object, animation_name, event_name, frame_index, elapsed_time)
        except Exception:
            pass


def dispatch_animation_finished(
    owner_object: Any,
    animation_name: str,
    elapsed_time: float,
) -> None:
    """Dispatch animation finished event (special case)."""
    for handler in list(_animation_event_handlers):
        try:
            # Use special event name "finished"
            handler(owner_object, animation_name, "finished", -1, elapsed_time)
        except Exception:
            pass
