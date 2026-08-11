"""Stopping a Logic Graph runtime must release every registration it made.

PHASE 9.5B Stage 3.

Before this stage ``LogicGraphRuntime`` subscribed to the module-global
``UIEventDispatcher`` with a closure over ``self`` and never removed it.  The
runtime therefore stayed reachable forever, which also meant ``__del__`` never
ran and its physics/animation handlers were never unregistered.  Five Play
cycles left five live runtimes; twenty left twenty.
"""

from __future__ import annotations

import gc
import weakref

import pytest

from engine.logic.animation_event_dispatch import _animation_event_handlers
from engine.logic.physics_event_dispatch import _physics_event_handlers
from engine.logic.runtime import LogicGraphRuntime
from engine.runtime.ui_event_dispatcher import get_ui_event_dispatcher

GRAPH = {
    "format": "zennity.logic_graph",
    "version": 1,
    "name": "HandlerCleanup",
    "target": {"type": "name", "value": "Player"},
    "nodes": [{"id": "n_update", "type": "event_update", "position": [0.0, 0.0]}],
    "edges": [],
}


@pytest.fixture
def dispatcher():
    """A dispatcher with no leftovers from other tests, restored afterwards."""
    instance = get_ui_event_dispatcher()
    saved = {key: list(value) for key, value in instance._subscribers.items()}
    instance.clear()
    yield instance
    instance.clear()
    instance._subscribers.update(saved)


def _handler_counts(dispatcher) -> tuple[int, int, int]:
    return (
        dispatcher.subscriber_count(),
        len(_physics_event_handlers),
        len(_animation_event_handlers),
    )


def test_stop_releases_every_registration(dispatcher):
    baseline = _handler_counts(dispatcher)

    runtime = LogicGraphRuntime(GRAPH)
    assert _handler_counts(dispatcher) != baseline, "the runtime registered nothing"

    runtime.stop()
    assert _handler_counts(dispatcher) == baseline


def test_stop_is_idempotent(dispatcher):
    baseline = _handler_counts(dispatcher)
    runtime = LogicGraphRuntime(GRAPH)
    runtime.stop()
    runtime.stop()
    runtime.stop()
    assert _handler_counts(dispatcher) == baseline


def test_handlers_do_not_accumulate_across_cycles(dispatcher):
    baseline = _handler_counts(dispatcher)
    for _ in range(20):
        runtime = LogicGraphRuntime(GRAPH)
        runtime.stop()
    assert _handler_counts(dispatcher) == baseline, (
        "handler counts grew with the number of Play cycles"
    )


def test_a_stopped_runtime_is_collectable(dispatcher):
    """weakref is the detector here; cleanup itself must not need the collector."""
    references = []
    for _ in range(5):
        runtime = LogicGraphRuntime(GRAPH)
        references.append(weakref.ref(runtime))
        runtime.stop()
        del runtime

    gc.collect()
    alive = [reference for reference in references if reference() is not None]
    assert not alive, f"{len(alive)} of 5 stopped runtimes are still reachable"


def test_stop_releases_the_game_reference(dispatcher):
    """A stopped runtime must not pin the previous session's game object."""

    class _Game:
        def __getattr__(self, name):
            return lambda *args, **kwargs: 0.0

    runtime = LogicGraphRuntime(GRAPH)
    game = _Game()
    game_reference = weakref.ref(game)
    runtime.update(game, 1.0 / 60.0)
    runtime.stop()
    del game

    gc.collect()
    assert game_reference() is None, "the stopped runtime still holds the game object"


def test_dispatcher_unsubscribe_is_safe_for_unknown_callbacks(dispatcher):
    assert dispatcher.unsubscribe("ui.button_clicked", lambda payload: None) is False
    assert dispatcher.unsubscribe("nonexistent.event", lambda payload: None) is False
