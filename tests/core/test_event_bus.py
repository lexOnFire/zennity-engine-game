"""
tests/core/test_event_bus.py
────────────────────────────────────────────────────────────────
Commit 18: suite completa do EventBus.

Grupos:
  TestSubscribe       (6)  — subscribe, duplicata, listener_count, has_listeners
  TestEmit            (6)  — despacho síncrono, kwargs, múltiplos, isolamento
  TestUnsubscribe     (4)  — remove listener, sem efeito se ausente, só o alvo
  TestOnce            (5)  — uma só chamada, auto-remove, coexistência, kwargs
  TestDeferred        (6)  — emit_deferred, flush, FIFO, fila limpa, pending_count
  TestClear           (5)  — clear(event), clear() total, limpa fila, safe
  TestInspect         (5)  — listener_count, has_listeners, pending_count
  TestPublishAlias    (3)  — retrocompat: publish(), has_subscribers(), subscribers_count()
  TestEdgeCases      (10)  — emit dentro de listener, once+unsub, flush vazio,
                            deferred após clear, emissão de evento desconhecido,
                            subscribe vazio após clear, double-flush, re-subscribe

Total esperado: 50 testes.
"""
from __future__ import annotations

import pytest
from engine.event_bus import EventBus


# ───────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def clean_bus():
    """Garante estado limpo antes e após cada teste."""
    EventBus.clear()
    yield
    EventBus.clear()


# ===========================================================================
# 1. Subscribe
# ===========================================================================

class TestSubscribe:
    def test_subscribe_adds_listener(self):
        cb = lambda: None
        EventBus.subscribe("evt", cb)
        assert EventBus.listener_count("evt") == 1

    def test_subscribe_ignores_duplicate(self):
        cb = lambda: None
        EventBus.subscribe("dup", cb)
        EventBus.subscribe("dup", cb)
        assert EventBus.listener_count("dup") == 1

    def test_subscribe_multiple_distinct_callbacks(self):
        EventBus.subscribe("evt", lambda: None)
        EventBus.subscribe("evt", lambda: None)
        assert EventBus.listener_count("evt") == 2

    def test_has_listeners_true_after_subscribe(self):
        EventBus.subscribe("evt", lambda: None)
        assert EventBus.has_listeners("evt") is True

    def test_has_listeners_false_when_empty(self):
        assert EventBus.has_listeners("nonexistent") is False

    def test_subscribe_independent_events(self):
        EventBus.subscribe("a", lambda: None)
        EventBus.subscribe("b", lambda: None)
        assert EventBus.listener_count("a") == 1
        assert EventBus.listener_count("b") == 1


# ===========================================================================
# 2. Emit (síncrono)
# ===========================================================================

class TestEmit:
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
        EventBus.emit("no_such_event", value=99)

    def test_duplicate_subscribe_fires_once(self):
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
        EventBus.emit("err")
        assert results == ["ok"]


# ===========================================================================
# 3. Unsubscribe
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
        EventBus.unsubscribe("ghost", lambda: None)

    def test_unsubscribe_only_target_listener(self):
        calls = []
        cb_a = lambda: calls.append("a")
        cb_b = lambda: calls.append("b")
        EventBus.subscribe("t", cb_a)
        EventBus.subscribe("t", cb_b)
        EventBus.unsubscribe("t", cb_a)
        EventBus.emit("t")
        assert calls == ["b"]

    def test_unsubscribe_reduces_count(self):
        cb = lambda: None
        EventBus.subscribe("evt", cb)
        EventBus.unsubscribe("evt", cb)
        assert EventBus.listener_count("evt") == 0


# ===========================================================================
# 4. Once
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

    def test_once_receives_kwargs(self):
        received = {}
        EventBus.once("evt", lambda v: received.update({"v": v}))
        EventBus.emit("evt", v=42)
        assert received == {"v": 42}


# ===========================================================================
# 5. Emit Deferred + Flush
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

    def test_pending_count_increments(self):
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        assert EventBus.pending_count() == 2

    def test_deferred_passes_kwargs(self):
        received = {}
        EventBus.subscribe("evt", lambda x: received.update({"x": x}))
        EventBus.emit_deferred("evt", x=99)
        EventBus.flush()
        assert received == {"x": 99}


# ===========================================================================
# 6. Clear
# ===========================================================================

class TestClear:
    def test_clear_event_removes_listeners(self):
        EventBus.subscribe("c", lambda: None)
        EventBus.clear("c")
        assert EventBus.listener_count("c") == 0

    def test_clear_event_preserves_others(self):
        calls = []
        EventBus.subscribe("keep", lambda: calls.append(1))
        EventBus.subscribe("remove", lambda: None)
        EventBus.clear("remove")
        EventBus.emit("keep")
        assert calls == [1]

    def test_clear_all_removes_all_events(self):
        EventBus.subscribe("a", lambda: None)
        EventBus.subscribe("b", lambda: None)
        EventBus.clear()
        assert EventBus.listener_count("a") == 0
        assert EventBus.listener_count("b") == 0

    def test_clear_all_empties_queue(self):
        EventBus.emit_deferred("evt")
        EventBus.clear()
        assert EventBus.pending_count() == 0

    def test_clear_nonexistent_event_is_safe(self):
        EventBus.clear("ghost.event")


# ===========================================================================
# 7. Inspeção
# ===========================================================================

class TestInspect:
    def test_listener_count_zero_initially(self):
        assert EventBus.listener_count("evt") == 0

    def test_listener_count_reflects_subscribes(self):
        EventBus.subscribe("evt", lambda: None)
        EventBus.subscribe("evt", lambda: None)
        assert EventBus.listener_count("evt") == 2

    def test_has_listeners_false_when_empty(self):
        assert EventBus.has_listeners("ghost") is False

    def test_has_listeners_true_when_subscribed(self):
        EventBus.subscribe("h", lambda: None)
        assert EventBus.has_listeners("h") is True

    def test_pending_count_zero_initially(self):
        assert EventBus.pending_count() == 0


# ===========================================================================
# 8. Aliases de instância (retrocompat)
# ===========================================================================

class TestPublishAlias:
    def test_publish_triggers_listener(self):
        calls = []
        bus = EventBus()
        EventBus.subscribe("p", lambda v: calls.append(v))
        bus.publish("p", v=7)
        assert calls == [7]

    def test_has_subscribers_delegates_to_has_listeners(self):
        EventBus.subscribe("evt", lambda: None)
        bus = EventBus()
        assert bus.has_subscribers("evt") is True

    def test_subscribers_count_delegates_to_listener_count(self):
        EventBus.subscribe("evt", lambda: None)
        EventBus.subscribe("evt", lambda: None)
        bus = EventBus()
        assert bus.subscribers_count("evt") == 2


# ===========================================================================
# 9. Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_emit_inside_listener_does_not_deadlock(self):
        """Emitir outro evento dentro de um listener não deve travar."""
        inner_calls = []
        EventBus.subscribe("inner", lambda: inner_calls.append(1))
        EventBus.subscribe("outer", lambda: EventBus.emit("inner"))
        EventBus.emit("outer")
        assert inner_calls == [1]

    def test_double_flush_is_safe(self):
        """Chamar flush() duas vezes seguidas não deve lançar."""
        EventBus.emit_deferred("x")
        EventBus.flush()
        EventBus.flush()  # fila já vazia

    def test_deferred_after_clear_not_dispatched(self):
        """Evento diferido cujo listener foi removido com clear() não chama callback."""
        calls = []
        EventBus.subscribe("gone", lambda: calls.append(1))
        EventBus.emit_deferred("gone")
        EventBus.clear("gone")  # remove listener antes do flush
        EventBus.flush()
        assert calls == []

    def test_re_subscribe_after_unsubscribe(self):
        """Listener removido pode ser re-registrado sem duplicação."""
        calls = []
        cb = lambda: calls.append(1)
        EventBus.subscribe("r", cb)
        EventBus.unsubscribe("r", cb)
        EventBus.subscribe("r", cb)
        EventBus.emit("r")
        assert calls == [1]

    def test_subscribe_after_clear_works(self):
        """Novo subscribe após clear() funciona normalmente."""
        EventBus.subscribe("c", lambda: None)
        EventBus.clear("c")
        calls = []
        EventBus.subscribe("c", lambda: calls.append(1))
        EventBus.emit("c")
        assert calls == [1]

    def test_listener_count_zero_after_clear_all(self):
        for i in range(5):
            EventBus.subscribe(f"evt{i}", lambda: None)
        EventBus.clear()
        for i in range(5):
            assert EventBus.listener_count(f"evt{i}") == 0

    def test_once_unsubscribed_manually_not_called(self):
        """once() pode ser cancelado com unsubscribe antes do emit."""
        calls = []
        cb = lambda: calls.append(1)
        EventBus.once("o", cb)
        EventBus.unsubscribe("o", cb)
        EventBus.emit("o")
        assert calls == []

    def test_many_listeners_all_receive_event(self):
        calls = []
        for i in range(20):
            EventBus.subscribe("big", lambda i=i: calls.append(i))
        EventBus.emit("big")
        assert len(calls) == 20

    def test_different_events_do_not_cross_fire(self):
        a_calls, b_calls = [], []
        EventBus.subscribe("a", lambda: a_calls.append(1))
        EventBus.subscribe("b", lambda: b_calls.append(1))
        EventBus.emit("a")
        assert a_calls == [1] and b_calls == []

    def test_flush_empty_queue_is_safe(self):
        EventBus.flush()  # nenhum evento diferido
