"""
tests/test_event_bus.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/event_bus.py (EventBus).

Estratégia de isolamento:
  - EventBus usa apenas estado de classe (sem pygame, sem SDL).
  - Fixture `bus` chama EventBus.clear() antes e depois de cada teste,
    garantindo isolação total entre testes sem recriar o objeto.
  - Callbacks são MagicMock ou funções simples que appendam em lista.
  - Testa tanto a API classmethod quanto a API de instância (retrocompat).
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from engine.event_bus import EventBus


# ── fixture de isolamento ────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def bus():
    """Limpa o estado global antes e depois de cada teste."""
    EventBus.clear()
    yield
    EventBus.clear()


# ── TestSubscribe ───────────────────────────────────────────────────────────────
class TestSubscribe:
    def test_subscribe_adds_listener(self):
        cb = MagicMock()
        EventBus.subscribe("test", cb)
        assert EventBus.listener_count("test") == 1

    def test_subscribe_multiple_callbacks(self):
        EventBus.subscribe("test", MagicMock())
        EventBus.subscribe("test", MagicMock())
        assert EventBus.listener_count("test") == 2

    def test_subscribe_ignores_duplicate(self):
        cb = MagicMock()
        EventBus.subscribe("test", cb)
        EventBus.subscribe("test", cb)
        assert EventBus.listener_count("test") == 1

    def test_subscribe_different_events_independent(self):
        EventBus.subscribe("a", MagicMock())
        EventBus.subscribe("b", MagicMock())
        assert EventBus.listener_count("a") == 1
        assert EventBus.listener_count("b") == 1

    def test_has_listeners_true_after_subscribe(self):
        EventBus.subscribe("ev", MagicMock())
        assert EventBus.has_listeners("ev") is True

    def test_has_listeners_false_on_unknown_event(self):
        assert EventBus.has_listeners("unknown") is False

    def test_listener_count_zero_on_empty(self):
        assert EventBus.listener_count("nada") == 0


# ── TestUnsubscribe ────────────────────────────────────────────────────────────
class TestUnsubscribe:
    def test_unsubscribe_removes_listener(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.unsubscribe("ev", cb)
        assert EventBus.listener_count("ev") == 0

    def test_unsubscribe_only_removes_target(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.subscribe("ev", cb1)
        EventBus.subscribe("ev", cb2)
        EventBus.unsubscribe("ev", cb1)
        assert EventBus.listener_count("ev") == 1

    def test_unsubscribe_unknown_event_no_crash(self):
        EventBus.unsubscribe("nada", MagicMock())  # não deve lançar

    def test_unsubscribe_callback_not_subscribed_no_crash(self):
        EventBus.subscribe("ev", MagicMock())
        EventBus.unsubscribe("ev", MagicMock())  # outro cb

    def test_unsubscribe_prevents_callback_being_called(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.unsubscribe("ev", cb)
        EventBus.emit("ev")
        cb.assert_not_called()


# ── TestEmit ──────────────────────────────────────────────────────────────────
class TestEmit:
    def test_emit_calls_subscriber(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit("ev")
        cb.assert_called_once()

    def test_emit_passes_kwargs(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit("ev", x=1, y=2)
        cb.assert_called_once_with(x=1, y=2)

    def test_emit_calls_all_subscribers(self):
        cb1, cb2, cb3 = MagicMock(), MagicMock(), MagicMock()
        for c in (cb1, cb2, cb3):
            EventBus.subscribe("ev", c)
        EventBus.emit("ev")
        for c in (cb1, cb2, cb3):
            c.assert_called_once()

    def test_emit_unknown_event_no_crash(self):
        EventBus.emit("nada")  # nenhum listener

    def test_emit_exception_in_listener_does_not_stop_others(self):
        results = []
        def bad(): raise RuntimeError("ops")
        def good(): results.append(1)
        EventBus.subscribe("ev", bad)
        EventBus.subscribe("ev", good)
        EventBus.emit("ev")
        assert results == [1]

    def test_emit_multiple_times(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit("ev")
        EventBus.emit("ev")
        assert cb.call_count == 2

    def test_emit_does_not_cross_events(self):
        cb_a, cb_b = MagicMock(), MagicMock()
        EventBus.subscribe("a", cb_a)
        EventBus.subscribe("b", cb_b)
        EventBus.emit("a")
        cb_a.assert_called_once()
        cb_b.assert_not_called()

    def test_emit_snapshot_safe_during_unsubscribe(self):
        """Listener que se desinscreve durante emit não quebra a iteração."""
        results = []
        def self_removing():
            EventBus.unsubscribe("ev", self_removing)
            results.append("ok")
        EventBus.subscribe("ev", self_removing)
        EventBus.emit("ev")  # não deve lançar
        assert results == ["ok"]


# ── TestOnce ───────────────────────────────────────────────────────────────────
class TestOnce:
    def test_once_fires_on_first_emit(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.emit("ev")
        cb.assert_called_once()

    def test_once_does_not_fire_on_second_emit(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.emit("ev")
        EventBus.emit("ev")
        assert cb.call_count == 1

    def test_once_removed_from_listeners_after_fire(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.emit("ev")
        assert EventBus.listener_count("ev") == 0

    def test_once_passes_kwargs(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.emit("ev", score=99)
        cb.assert_called_once_with(score=99)

    def test_once_alongside_regular_subscriber(self):
        """once remove a si mesmo mas não o subscriber permanente."""
        perm = MagicMock()
        temp = MagicMock()
        EventBus.subscribe("ev", perm)
        EventBus.once("ev", temp)
        EventBus.emit("ev")
        EventBus.emit("ev")
        assert perm.call_count == 2
        assert temp.call_count == 1

    def test_once_multiple_callbacks_each_fires_once(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.once("ev", cb1)
        EventBus.once("ev", cb2)
        EventBus.emit("ev")
        EventBus.emit("ev")
        assert cb1.call_count == 1
        assert cb2.call_count == 1


# ── TestEmitDeferred ───────────────────────────────────────────────────────────
class TestEmitDeferred:
    def test_deferred_not_called_before_flush(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit_deferred("ev")
        cb.assert_not_called()

    def test_deferred_called_after_flush(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit_deferred("ev")
        EventBus.flush()
        cb.assert_called_once()

    def test_deferred_passes_kwargs_after_flush(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit_deferred("ev", hp=50, pos=(1, 2))
        EventBus.flush()
        cb.assert_called_once_with(hp=50, pos=(1, 2))

    def test_pending_count_increases_with_deferred(self):
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        assert EventBus.pending_count() == 2

    def test_pending_count_zero_after_flush(self):
        EventBus.emit_deferred("ev")
        EventBus.flush()
        assert EventBus.pending_count() == 0

    def test_multiple_deferred_dispatched_in_order(self):
        order = []
        EventBus.subscribe("a", lambda: order.append("a"))
        EventBus.subscribe("b", lambda: order.append("b"))
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        EventBus.flush()
        assert order == ["a", "b"]

    def test_flush_empty_queue_no_crash(self):
        EventBus.flush()  # sem nada na fila

    def test_flush_processes_only_queued_at_call_time(self):
        """Evento emitido por um listener durante flush() não é processado
        neste flush (evita loop infinito)."""
        count = [0]
        def add_more():
            count[0] += 1
            if count[0] < 5:
                EventBus.emit_deferred("ev")  # tenta re-enfileirar
        EventBus.subscribe("ev", add_more)
        EventBus.emit_deferred("ev")
        EventBus.flush()  # deve processar apenas 1
        assert count[0] == 1


# ── TestClear ───────────────────────────────────────────────────────────────────
class TestClear:
    def test_clear_event_removes_listeners(self):
        EventBus.subscribe("ev", MagicMock())
        EventBus.clear("ev")
        assert EventBus.listener_count("ev") == 0

    def test_clear_event_does_not_affect_others(self):
        EventBus.subscribe("a", MagicMock())
        EventBus.subscribe("b", MagicMock())
        EventBus.clear("a")
        assert EventBus.listener_count("b") == 1

    def test_clear_all_removes_everything(self):
        EventBus.subscribe("a", MagicMock())
        EventBus.subscribe("b", MagicMock())
        EventBus.emit_deferred("c")
        EventBus.clear()
        assert EventBus.listener_count("a") == 0
        assert EventBus.listener_count("b") == 0
        assert EventBus.pending_count() == 0

    def test_clear_unknown_event_no_crash(self):
        EventBus.clear("nada")

    def test_clear_prevents_emit_from_calling_listener(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.clear("ev")
        EventBus.emit("ev")
        cb.assert_not_called()


# ── TestRetrocompatInstance ───────────────────────────────────────────────────────
class TestRetrocompatInstance:
    def test_publish_calls_listener(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        eb = EventBus()
        eb.publish("ev", score=10)
        cb.assert_called_once_with(score=10)

    def test_has_subscribers_true(self):
        EventBus.subscribe("ev", MagicMock())
        assert EventBus().has_subscribers("ev") is True

    def test_has_subscribers_false(self):
        assert EventBus().has_subscribers("vazio") is False

    def test_subscribers_count_via_instance(self):
        EventBus.subscribe("ev", MagicMock())
        EventBus.subscribe("ev", MagicMock())
        assert EventBus().subscribers_count("ev") == 2

    def test_unsubscribe_all_via_instance(self):
        EventBus.subscribe("ev", MagicMock())
        EventBus().unsubscribe_all("ev")
        assert EventBus.listener_count("ev") == 0

    def test_instance_shares_global_state(self):
        """Instâncias diferentes compartilham o mesmo barramento global."""
        cb = MagicMock()
        eb1, eb2 = EventBus(), EventBus()
        EventBus.subscribe("ev", cb)
        eb2.publish("ev")
        cb.assert_called_once()


# ── TestEdgeCases ─────────────────────────────────────────────────────────────────
class TestEdgeCases:
    def test_subscribe_lambda(self):
        results = []
        EventBus.subscribe("ev", lambda x: results.append(x))
        EventBus.emit("ev", x=42)
        assert results == [42]

    def test_emit_with_no_kwargs(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit("ev")
        cb.assert_called_once_with()

    def test_event_name_with_dots(self):
        cb = MagicMock()
        EventBus.subscribe("player.death", cb)
        EventBus.emit("player.death", killer="spike")
        cb.assert_called_once_with(killer="spike")

    def test_event_name_case_sensitive(self):
        cb1, cb2 = MagicMock(), MagicMock()
        EventBus.subscribe("Ev", cb1)
        EventBus.subscribe("ev", cb2)
        EventBus.emit("ev")
        cb1.assert_not_called()
        cb2.assert_called_once()

    def test_many_events_independent(self):
        callbacks = {f"ev{i}": MagicMock() for i in range(10)}
        for name, cb in callbacks.items():
            EventBus.subscribe(name, cb)
        EventBus.emit("ev5")
        for name, cb in callbacks.items():
            if name == "ev5":
                cb.assert_called_once()
            else:
                cb.assert_not_called()

    def test_deferred_then_clear_all_drops_queue(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit_deferred("ev")
        EventBus.clear()  # limpa fila
        EventBus.flush()  # nada para despachar
        cb.assert_not_called()
