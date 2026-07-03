"""
tests/core/test_event_bus.py
────────────────────────────────────────────────────────────────
Commit 4: suite completa do EventBus — 52 testes.

Estratégia de isolamento:
  - EventBus usa estado de CLASSE (_listeners, _once, _queue).
  - Fixture autouse chama EventBus.clear() antes e depois de cada teste,
    garantindo que nenhum estado vaze entre testes.
  - Nenhuma dependência de Pygame — sem patches extras necessários.

Grupos:
  TestSubscribe      (7)  — subscribe, duplicata, múltiplos, lambda
  TestEmit           (8)  — emit síncrono, kwargs, ordem, exceções
  TestUnsubscribe    (6)  — off/unsubscribe, inexistente, parcial, duplo
  TestOnce           (7)  — once, auto-remove, coexistência, unsub manual
  TestClear          (6)  — clear(event) e clear() global, fila, safe
  TestDeferred       (8)  — emit_deferred, flush, FIFO, once, kwargs
  TestInspection     (6)  — listener_count, has_listeners, pending_count
  TestRetrocompat    (4)  — publish(), has_subscribers(), unsubscribe_all()

Total: 52 testes.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from engine.core.event_bus import EventBus


# ---------------------------------------------------------------------------
# Fixture de isolamento
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_bus():
    """Limpa todo o estado global do EventBus antes e após cada teste."""
    EventBus.clear()
    yield
    EventBus.clear()


# ===========================================================================
# 1. subscribe()
# ===========================================================================

class TestSubscribe:
    def test_subscribe_registers_listener(self):
        cb = MagicMock()
        EventBus.subscribe("test.event", cb)
        assert EventBus.has_listeners("test.event")

    def test_subscribe_duplicate_ignored(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.subscribe("e", cb)
        assert EventBus.listener_count("e") == 1

    def test_subscribe_multiple_listeners(self):
        cb1, cb2, cb3 = MagicMock(), MagicMock(), MagicMock()
        EventBus.subscribe("e", cb1)
        EventBus.subscribe("e", cb2)
        EventBus.subscribe("e", cb3)
        assert EventBus.listener_count("e") == 3

    def test_subscribe_different_events_independent(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.subscribe("a", cb1)
        EventBus.subscribe("b", cb2)
        assert EventBus.listener_count("a") == 1
        assert EventBus.listener_count("b") == 1

    def test_subscribe_does_not_call_listener(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        cb.assert_not_called()

    def test_subscribe_unknown_event_creates_entry(self):
        cb = MagicMock()
        EventBus.subscribe("novo.evento", cb)
        assert EventBus.listener_count("novo.evento") == 1

    def test_subscribe_lambda_receives_kwargs(self):
        results = []
        EventBus.subscribe("e", lambda x: results.append(x))
        EventBus.emit("e", x=42)
        assert results == [42]


# ===========================================================================
# 2. emit() — síncrono
# ===========================================================================

class TestEmit:
    def test_emit_calls_listener(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.emit("e")
        cb.assert_called_once()

    def test_emit_passes_kwargs(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.emit("e", x=1, y=2)
        cb.assert_called_once_with(x=1, y=2)

    def test_emit_calls_all_listeners(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.subscribe("e", cb1)
        EventBus.subscribe("e", cb2)
        EventBus.emit("e")
        cb1.assert_called_once()
        cb2.assert_called_once()

    def test_emit_preserves_subscription_order(self):
        order = []
        EventBus.subscribe("e", lambda: order.append(1))
        EventBus.subscribe("e", lambda: order.append(2))
        EventBus.subscribe("e", lambda: order.append(3))
        EventBus.emit("e")
        assert order == [1, 2, 3]

    def test_emit_no_listeners_is_safe(self):
        EventBus.emit("evento.inexistente")  # não deve lançar

    def test_emit_does_not_affect_other_events(self):
        cb_a, cb_b = MagicMock(), MagicMock()
        EventBus.subscribe("a", cb_a)
        EventBus.subscribe("b", cb_b)
        EventBus.emit("a")
        cb_b.assert_not_called()

    def test_emit_exception_does_not_stop_others(self):
        """Exceção em um listener não interrompe os demais."""
        def bad(): raise RuntimeError("boom")
        cb_after = MagicMock()
        EventBus.subscribe("e", bad)
        EventBus.subscribe("e", cb_after)
        EventBus.emit("e")  # não deve lançar
        cb_after.assert_called_once()

    def test_emit_multiple_times_calls_listener_each_time(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.emit("e")
        EventBus.emit("e")
        EventBus.emit("e")
        assert cb.call_count == 3


# ===========================================================================
# 3. unsubscribe()
# ===========================================================================

class TestUnsubscribe:
    def test_unsubscribe_removes_listener(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.unsubscribe("e", cb)
        EventBus.emit("e")
        cb.assert_not_called()

    def test_unsubscribe_unknown_event_is_safe(self):
        EventBus.unsubscribe("nao.existe", MagicMock())

    def test_unsubscribe_unknown_callback_is_safe(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.subscribe("e", cb1)
        EventBus.unsubscribe("e", cb2)  # cb2 nunca foi inscrito

    def test_unsubscribe_only_target_listener(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.subscribe("e", cb1)
        EventBus.subscribe("e", cb2)
        EventBus.unsubscribe("e", cb1)
        EventBus.emit("e")
        cb1.assert_not_called()
        cb2.assert_called_once()

    def test_unsubscribe_all_then_no_listeners(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.subscribe("e", cb1)
        EventBus.subscribe("e", cb2)
        EventBus.unsubscribe("e", cb1)
        EventBus.unsubscribe("e", cb2)
        assert EventBus.listener_count("e") == 0

    def test_unsubscribe_twice_is_safe(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.unsubscribe("e", cb)
        EventBus.unsubscribe("e", cb)  # segunda chamada não deve lançar


# ===========================================================================
# 4. once()
# ===========================================================================

class TestOnce:
    def test_once_fires_on_first_emit(self):
        cb = MagicMock()
        EventBus.once("e", cb)
        EventBus.emit("e")
        cb.assert_called_once()

    def test_once_not_fired_on_second_emit(self):
        cb = MagicMock()
        EventBus.once("e", cb)
        EventBus.emit("e")
        EventBus.emit("e")
        assert cb.call_count == 1

    def test_once_auto_removed_after_fire(self):
        EventBus.once("e", MagicMock())
        EventBus.emit("e")
        assert EventBus.listener_count("e") == 0

    def test_once_coexists_with_regular_subscriber(self):
        cb_once = MagicMock()
        cb_perm = MagicMock()
        EventBus.once("e", cb_once)
        EventBus.subscribe("e", cb_perm)
        EventBus.emit("e")
        EventBus.emit("e")
        assert cb_once.call_count == 1
        assert cb_perm.call_count == 2

    def test_once_receives_kwargs(self):
        cb = MagicMock()
        EventBus.once("e", cb)
        EventBus.emit("e", score=100)
        cb.assert_called_once_with(score=100)

    def test_multiple_once_listeners_each_fire_once(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.once("e", cb1)
        EventBus.once("e", cb2)
        EventBus.emit("e")
        EventBus.emit("e")
        assert cb1.call_count == 1
        assert cb2.call_count == 1

    def test_once_unsubscribe_before_emit(self):
        cb = MagicMock()
        EventBus.once("e", cb)
        EventBus.unsubscribe("e", cb)
        EventBus.emit("e")
        cb.assert_not_called()


# ===========================================================================
# 5. clear()
# ===========================================================================

class TestClear:
    def test_clear_event_removes_listeners(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.clear("e")
        EventBus.emit("e")
        cb.assert_not_called()

    def test_clear_event_count_zero(self):
        EventBus.subscribe("e", MagicMock())
        EventBus.clear("e")
        assert EventBus.listener_count("e") == 0

    def test_clear_event_does_not_affect_other_events(self):
        cb_a, cb_b = MagicMock(), MagicMock()
        EventBus.subscribe("a", cb_a)
        EventBus.subscribe("b", cb_b)
        EventBus.clear("a")
        EventBus.emit("b")
        cb_b.assert_called_once()

    def test_clear_all_removes_all_listeners(self):
        EventBus.subscribe("a", MagicMock())
        EventBus.subscribe("b", MagicMock())
        EventBus.clear()
        assert EventBus.listener_count("a") == 0
        assert EventBus.listener_count("b") == 0

    def test_clear_all_empties_deferred_queue(self):
        EventBus.emit_deferred("e", x=1)
        EventBus.emit_deferred("e", x=2)
        EventBus.clear()
        assert EventBus.pending_count() == 0

    def test_clear_unknown_event_is_safe(self):
        EventBus.clear("evento.que.nao.existe")


# ===========================================================================
# 6. emit_deferred() + flush()
# ===========================================================================

class TestDeferred:
    def test_deferred_not_dispatched_immediately(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.emit_deferred("e")
        cb.assert_not_called()

    def test_flush_dispatches_deferred(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.emit_deferred("e")
        EventBus.flush()
        cb.assert_called_once()

    def test_flush_passes_kwargs(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        EventBus.emit_deferred("e", valor=99)
        EventBus.flush()
        cb.assert_called_once_with(valor=99)

    def test_flush_processes_fifo_order(self):
        order = []
        EventBus.subscribe("e", lambda n: order.append(n))
        EventBus.emit_deferred("e", n=1)
        EventBus.emit_deferred("e", n=2)
        EventBus.emit_deferred("e", n=3)
        EventBus.flush()
        assert order == [1, 2, 3]

    def test_flush_empties_queue(self):
        EventBus.emit_deferred("e")
        EventBus.flush()
        assert EventBus.pending_count() == 0

    def test_flush_empty_queue_is_safe(self):
        EventBus.flush()

    def test_multiple_deferred_different_events(self):
        cb_a, cb_b = MagicMock(), MagicMock()
        EventBus.subscribe("a", cb_a)
        EventBus.subscribe("b", cb_b)
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        EventBus.flush()
        cb_a.assert_called_once()
        cb_b.assert_called_once()

    def test_deferred_respects_once(self):
        cb = MagicMock()
        EventBus.once("e", cb)
        EventBus.emit_deferred("e")
        EventBus.emit_deferred("e")
        EventBus.flush()
        assert cb.call_count == 1


# ===========================================================================
# 7. Inspecão
# ===========================================================================

class TestInspection:
    def test_listener_count_zero_for_unknown_event(self):
        assert EventBus.listener_count("nao.existe") == 0

    def test_listener_count_increments(self):
        EventBus.subscribe("e", MagicMock())
        EventBus.subscribe("e", MagicMock())
        assert EventBus.listener_count("e") == 2

    def test_has_listeners_false_when_empty(self):
        assert EventBus.has_listeners("e") is False

    def test_has_listeners_true_after_subscribe(self):
        EventBus.subscribe("e", MagicMock())
        assert EventBus.has_listeners("e") is True

    def test_pending_count_zero_initially(self):
        assert EventBus.pending_count() == 0

    def test_pending_count_increments_with_deferred(self):
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        assert EventBus.pending_count() == 2


# ===========================================================================
# 8. Retrocompatibilidade (instanciamento + publish)
# ===========================================================================

class TestRetrocompat:
    def test_instance_publish_calls_emit(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        bus = EventBus()
        bus.publish("e", x=7)
        cb.assert_called_once_with(x=7)

    def test_instance_has_subscribers(self):
        bus = EventBus()
        EventBus.subscribe("e", MagicMock())
        assert bus.has_subscribers("e") is True

    def test_instance_subscribers_count(self):
        bus = EventBus()
        EventBus.subscribe("e", MagicMock())
        EventBus.subscribe("e", MagicMock())
        assert bus.subscribers_count("e") == 2

    def test_unsubscribe_all_via_instance(self):
        cb = MagicMock()
        EventBus.subscribe("e", cb)
        bus = EventBus()
        bus.unsubscribe_all("e")
        EventBus.emit("e")
        cb.assert_not_called()
