"""
tests/core/test_event_bus.py
────────────────────────────────────────────────────────────────
Commit 4: valida o contrato público do EventBus.
EventBus usa estado de classe (útil no runtime), então cada teste
chama EventBus.clear() para garantir isolamento.
"""
from __future__ import annotations

import pytest
from engine.event_bus import EventBus


@pytest.fixture(autouse=True)
def clean_bus():
    EventBus.clear()
    yield
    EventBus.clear()


# ===========================================================================
# 1. subscribe / emit
# ===========================================================================

class TestSubscribeEmit:
    def test_listener_called_on_emit(self):
        received = []
        EventBus.subscribe("x", lambda v: received.append(v))
        EventBus.emit("x", v=42)
        assert received == [42]

    def test_listener_receives_kwargs(self):
        received = {}
        def handler(**kw): received.update(kw)
        EventBus.subscribe("ev", handler)
        EventBus.emit("ev", a=1, b=2)
        assert received == {"a": 1, "b": 2}

    def test_no_listeners_emit_is_safe(self):
        EventBus.emit("no_such_event", value=99)  # não deve lançar

    def test_duplicate_subscribe_ignored(self):
        calls = []
        cb = lambda: calls.append(1)
        EventBus.subscribe("dup", cb)
        EventBus.subscribe("dup", cb)
        EventBus.emit("dup")
        assert len(calls) == 1

    def test_multiple_listeners_all_called(self):
        results = []
        EventBus.subscribe("multi", lambda: results.append("a"))
        EventBus.subscribe("multi", lambda: results.append("b"))
        EventBus.subscribe("multi", lambda: results.append("c"))
        EventBus.emit("multi")
        assert sorted(results) == ["a", "b", "c"]

    def test_error_in_listener_does_not_stop_others(self):
        results = []
        def bad(): raise ValueError("boom")
        EventBus.subscribe("err", bad)
        EventBus.subscribe("err", lambda: results.append("ok"))
        EventBus.emit("err")  # não deve lançar
        assert results == ["ok"]


# ===========================================================================
# 2. unsubscribe
# ===========================================================================

class TestUnsubscribe:
    def test_unsubscribed_listener_not_called(self):
        calls = []
        cb = lambda: calls.append(1)
        EventBus.subscribe("u", cb)
        EventBus.unsubscribe("u", cb)
        EventBus.emit("u")
        assert calls == []

    def test_unsubscribe_nonexistent_is_safe(self):
        EventBus.unsubscribe("ghost", lambda: None)  # não deve lançar

    def test_unsubscribe_only_target_listener(self):
        calls = []
        cb_a = lambda: calls.append("a")
        cb_b = lambda: calls.append("b")
        EventBus.subscribe("t", cb_a)
        EventBus.subscribe("t", cb_b)
        EventBus.unsubscribe("t", cb_a)
        EventBus.emit("t")
        assert calls == ["b"]


# ===========================================================================
# 3. once
# ===========================================================================

class TestOnce:
    def test_once_called_on_first_emit(self):
        calls = []
        EventBus.once("o", lambda: calls.append(1))
        EventBus.emit("o")
        assert calls == [1]

    def test_once_not_called_on_second_emit(self):
        calls = []
        EventBus.once("o", lambda: calls.append(1))
        EventBus.emit("o")
        EventBus.emit("o")
        assert len(calls) == 1

    def test_once_removed_after_fire(self):
        EventBus.once("o", lambda: None)
        EventBus.emit("o")
        assert EventBus.listener_count("o") == 0

    def test_once_and_regular_coexist(self):
        regular = []
        once_calls = []
        EventBus.subscribe("mix", lambda: regular.append(1))
        EventBus.once("mix", lambda: once_calls.append(1))
        EventBus.emit("mix")
        EventBus.emit("mix")
        assert len(regular) == 2
        assert len(once_calls) == 1


# ===========================================================================
# 4. emit_deferred / flush
# ===========================================================================

class TestDeferred:
    def test_deferred_not_called_before_flush(self):
        calls = []
        EventBus.subscribe("d", lambda: calls.append(1))
        EventBus.emit_deferred("d")
        assert calls == []

    def test_deferred_called_after_flush(self):
        calls = []
        EventBus.subscribe("d", lambda: calls.append(1))
        EventBus.emit_deferred("d")
        EventBus.flush()
        assert calls == [1]

    def test_flush_processes_in_fifo_order(self):
        order = []
        EventBus.subscribe("seq", lambda v: order.append(v))
        EventBus.emit_deferred("seq", v=1)
        EventBus.emit_deferred("seq", v=2)
        EventBus.emit_deferred("seq", v=3)
        EventBus.flush()
        assert order == [1, 2, 3]

    def test_flush_empties_queue(self):
        EventBus.emit_deferred("d")
        EventBus.emit_deferred("d")
        EventBus.flush()
        assert EventBus.pending_count() == 0

    def test_pending_count_increases_with_deferred(self):
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        assert EventBus.pending_count() == 2


# ===========================================================================
# 5. clear
# ===========================================================================

class TestClear:
    def test_clear_event_removes_its_listeners(self):
        EventBus.subscribe("c", lambda: None)
        EventBus.clear("c")
        assert EventBus.listener_count("c") == 0

    def test_clear_event_preserves_other_events(self):
        calls = []
        EventBus.subscribe("keep", lambda: calls.append(1))
        EventBus.subscribe("remove", lambda: None)
        EventBus.clear("remove")
        EventBus.emit("keep")
        assert calls == [1]

    def test_clear_all_removes_everything(self):
        EventBus.subscribe("a", lambda: None)
        EventBus.subscribe("b", lambda: None)
        EventBus.emit_deferred("a")
        EventBus.clear()
        assert EventBus.listener_count("a") == 0
        assert EventBus.listener_count("b") == 0
        assert EventBus.pending_count() == 0


# ===========================================================================
# 6. Inspecão
# ===========================================================================

class TestInspection:
    def test_listener_count_zero_initially(self):
        assert EventBus.listener_count("new_event") == 0

    def test_listener_count_increments(self):
        EventBus.subscribe("e", lambda: None)
        EventBus.subscribe("e", lambda: None)
        assert EventBus.listener_count("e") == 2

    def test_has_listeners_false_when_empty(self):
        assert EventBus.has_listeners("ghost") is False

    def test_has_listeners_true_when_subscribed(self):
        EventBus.subscribe("h", lambda: None)
        assert EventBus.has_listeners("h") is True


# ===========================================================================
# 7. Alias publish() (retrocompat)
# ===========================================================================

class TestPublishAlias:
    def test_publish_triggers_listener(self):
        calls = []
        bus = EventBus()  # instância
        EventBus.subscribe("p", lambda v: calls.append(v))
        bus.publish("p", v=7)
        assert calls == [7]
