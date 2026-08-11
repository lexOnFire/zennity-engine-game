"""Phase 9.5B — the dialogue -> LogicEventBus bridge.

History:
  * Phase 9.5A found `engine/dialogue/manager.py` calling a
    `LogicEventBus.get_instance()` that does not exist.  Every dialogue event
    raised AttributeError into a broad handler that only `print()`ed, so
    dialogue had never reached Logic Graphs and nothing reported it.
  * Stage 0 made that failure visible (logged with a traceback).
  * Stage 1 fixes it: the LogicEventBus is created per Play session by
    `ViewportRuntimeInitializer._create_logic_services` and injected into the
    DialogueManager.  No second event bus was introduced.

This file used to assert the defect was still present.  It now asserts the
bridge works.
"""
from __future__ import annotations

import pytest

from engine.dialogue.manager import DialogueManager
from engine.logic.event_bus import LogicEventBus


@pytest.fixture
def wired():
    manager = DialogueManager()
    bus = LogicEventBus()
    manager.bind_event_bus(bus)
    return manager, bus


# ------------------------------------------------------------------ the fix
def test_dialogue_event_reaches_the_logic_event_bus(wired):
    manager, bus = wired
    received = []
    bus.subscribe("dialogue:speech_started", received.append)

    manager._handle_dialogue_event(("npc_1", "s1"), "speech_started", {"text": "hi"})
    bus.dispatch()

    assert len(received) == 1
    payload = received[0].payload
    assert payload["owner_id"] == "npc_1"
    assert payload["session_id"] == "s1"
    assert payload["event_name"] == "speech_started"
    assert payload["payload"] == {"text": "hi"}


def test_owner_isolation_is_preserved(wired):
    """Two owners running the same dialogue must stay distinguishable."""
    manager, bus = wired
    received = []
    bus.subscribe("dialogue:choice_made", received.append)

    manager._handle_dialogue_event(("npc_a", "greet"), "choice_made", {"index": 0})
    manager._handle_dialogue_event(("npc_b", "greet"), "choice_made", {"index": 1})
    bus.dispatch()

    owners = [e.payload["owner_id"] for e in received]
    assert owners == ["npc_a", "npc_b"]


def test_no_second_event_bus_was_created():
    """The brief forbade inventing another bus; we use the real one."""
    manager = DialogueManager()
    bus = LogicEventBus()
    manager.bind_event_bus(bus)
    assert manager.event_bus is bus


def test_get_instance_was_not_reintroduced():
    """The fix must not resurrect the singleton that never existed."""
    assert not hasattr(LogicEventBus, "get_instance")


# -------------------------------------------------------------- lifecycle
def test_unbound_manager_drops_events_without_raising():
    """Editor preview / unit tests have no Play session bound."""
    manager = DialogueManager()
    assert manager.event_bus is None
    manager._handle_dialogue_event(("o", "s"), "any_event", None)  # must not raise


def test_reset_releases_the_bus(wired):
    """A stale session bus must not leak into the next Play."""
    manager, bus = wired
    manager.reset()
    assert manager.event_bus is None


def test_a_failing_bus_is_logged_and_does_not_propagate(tmp_path):
    from engine.diagnostics.logging_setup import (
        owned_handlers, setup_logging, teardown_logging)

    class BrokenBus:
        def emit(self, *_a, **_k):
            raise RuntimeError("bus exploded")

    teardown_logging()
    try:
        setup_logging(tmp_path, process_name="Test")
        manager = DialogueManager()
        manager.bind_event_bus(BrokenBus())
        manager._handle_dialogue_event(("o", "s"), "boom", None)  # must not raise

        for handler in owned_handlers():
            handler.flush()
        text = (tmp_path / "logs" / "zennity.log").read_text(encoding="utf-8")
        assert "bus exploded" in text
        assert "Traceback (most recent call last)" in text
    finally:
        teardown_logging()


def test_viewport_initializer_binds_the_bus():
    """The wiring that makes this work in a real Play session."""
    import pathlib

    src = (pathlib.Path(__file__).resolve().parents[2]
           / "editor" / "runtime" / "viewport_runtime_initializer.py"
           ).read_text(encoding="utf-8")
    assert "bind_event_bus(self.logic_event_bus)" in src
