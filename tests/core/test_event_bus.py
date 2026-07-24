"""
tests/core/test_event_bus.py
─────────────────────────────────────────────────────────────────
Testes unitários de engine/event_bus.py.

Estratégia:
  - Sem pygame, sem engine/__init__.py: EventBus é puro Python.
  - autouse fixture reseta o estado global de classe antes de cada teste.
  - Nenhum teste depende da ordem de execução.
"""
from __future__ import annotations

from collections import defaultdict, deque
from unittest.mock import MagicMock, call

import pytest

from engine.event_bus import EventBus


@pytest.fixture(autouse=True)
def reset_bus():
    EventBus._listeners = defaultdict(list)
    EventBus._once      = defaultdict(list)
    EventBus._queue     = deque()
    yield
    EventBus._listeners = defaultdict(list)
    EventBus._once      = defaultdict(list)
    EventBus._queue     = deque()


# ─────────────────────────────────────────────────────────────────
class TestSubscribe:
    def test_subscribe_adds_listener(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        assert EventBus.listener_count("ev") == 1

    def test_subscribe_duplicate_ignored(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.subscribe("ev", cb)
        assert EventBus.listener_count("ev") == 1

    def test_subscribe_multiple_listeners(self):
        a, b = MagicMock(), MagicMock()
        EventBus.subscribe("ev", a)
        EventBus.subscribe("ev", b)
        assert EventBus.listener_count("ev") == 2

    def test_subscribe_different_events_independent(self):
        EventBus.subscribe("ev.a", MagicMock())
        EventBus.subscribe("ev.b", MagicMock())
        assert EventBus.listener_count("ev.a") == 1
        assert EventBus.listener_count("ev.b") == 1

    def test_has_listeners_true_after_subscribe(self):
        EventBus.subscribe("ev", MagicMock())
        assert EventBus.has_listeners("ev") is True

    def test_has_listeners_false_for_unknown_event(self):
        assert EventBus.has_listeners("nope") is False


# ─────────────────────────────────────────────────────────────────
class TestUnsubscribe:
    def test_unsubscribe_removes_listener(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.unsubscribe("ev", cb)
        assert EventBus.listener_count("ev") == 0

    def test_unsubscribe_nonexistent_no_error(self):
        EventBus.unsubscribe("ev", MagicMock())

    def test_unsubscribe_unknown_event_no_error(self):
        EventBus.unsubscribe("ghost", MagicMock())

    def test_unsubscribe_one_of_many(self):
        a, b = MagicMock(), MagicMock()
        EventBus.subscribe("ev", a)
        EventBus.subscribe("ev", b)
        EventBus.unsubscribe("ev", a)
        assert EventBus.listener_count("ev") == 1
        EventBus.emit("ev")
        b.assert_called_once()
        a.assert_not_called()

    def test_unsubscribe_does_not_affect_other_events(self):
        cb = MagicMock()
        EventBus.subscribe("a", cb)
        EventBus.subscribe("b", cb)
        EventBus.unsubscribe("a", cb)
        assert EventBus.listener_count("b") == 1


# ─────────────────────────────────────────────────────────────────
class TestEmit:
    def test_emit_calls_listener(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit("ev")
        cb.assert_called_once_with()

    def test_emit_passes_kwargs(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit("ev", x=1, y=2)
        cb.assert_called_once_with(x=1, y=2)

    def test_emit_calls_all_listeners(self):
        a, b = MagicMock(), MagicMock()
        EventBus.subscribe("ev", a)
        EventBus.subscribe("ev", b)
        EventBus.emit("ev")
        a.assert_called_once()
        b.assert_called_once()

    def test_emit_unknown_event_no_error(self):
        EventBus.emit("ghost")

    def test_emit_exception_in_listener_does_not_stop_others(self):
        bad = MagicMock(side_effect=RuntimeError("boom"))
        good = MagicMock()
        EventBus.subscribe("ev", bad)
        EventBus.subscribe("ev", good)
        EventBus.emit("ev")
        good.assert_called_once()

    def test_emit_multiple_times(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit("ev")
        EventBus.emit("ev")
        assert cb.call_count == 2

    def test_emit_does_not_affect_other_events(self):
        a, b = MagicMock(), MagicMock()
        EventBus.subscribe("ev.a", a)
        EventBus.subscribe("ev.b", b)
        EventBus.emit("ev.a")
        b.assert_not_called()


# ─────────────────────────────────────────────────────────────────
class TestOnce:
    def test_once_called_on_first_emit(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.emit("ev")
        cb.assert_called_once()

    def test_once_not_called_on_second_emit(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.emit("ev")
        EventBus.emit("ev")
        assert cb.call_count == 1

    def test_once_removed_after_call(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.emit("ev")
        assert EventBus.listener_count("ev") == 0

    def test_once_receives_kwargs(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.emit("ev", val=42)
        cb.assert_called_once_with(val=42)

    def test_once_and_regular_together(self):
        permanent = MagicMock()
        one_shot  = MagicMock()
        EventBus.subscribe("ev", permanent)
        EventBus.once("ev", one_shot)
        EventBus.emit("ev")
        EventBus.emit("ev")
        assert permanent.call_count == 2
        assert one_shot.call_count  == 1

    def test_once_unsubscribe_before_emit(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.unsubscribe("ev", cb)
        EventBus.emit("ev")
        cb.assert_not_called()


# ─────────────────────────────────────────────────────────────────
class TestEmitDeferred:
    def test_emit_deferred_does_not_call_immediately(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit_deferred("ev")
        cb.assert_not_called()

    def test_emit_deferred_increments_pending_count(self):
        EventBus.emit_deferred("ev")
        assert EventBus.pending_count() == 1

    def test_emit_deferred_multiple_increments_count(self):
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        assert EventBus.pending_count() == 2

    def test_flush_dispatches_deferred(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit_deferred("ev", x=7)
        EventBus.flush()
        cb.assert_called_once_with(x=7)

    def test_flush_clears_queue(self):
        EventBus.emit_deferred("ev")
        EventBus.flush()
        assert EventBus.pending_count() == 0

    def test_flush_dispatches_in_order(self):
        order = []
        EventBus.subscribe("a", lambda: order.append("a"))
        EventBus.subscribe("b", lambda: order.append("b"))
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        EventBus.flush()
        assert order == ["a", "b"]

    def test_flush_empty_queue_no_error(self):
        EventBus.flush()

    def test_flush_does_not_double_dispatch(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit_deferred("ev")
        EventBus.flush()
        EventBus.flush()
        cb.assert_called_once()


# ─────────────────────────────────────────────────────────────────
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
        assert EventBus.pending_count()     == 0

    def test_clear_unknown_event_no_error(self):
        EventBus.clear("ghost")

    def test_clear_also_removes_once_listeners(self):
        cb = MagicMock()
        EventBus.once("ev", cb)
        EventBus.clear("ev")
        EventBus.emit("ev")
        cb.assert_not_called()


# ─────────────────────────────────────────────────────────────────
class TestInspection:
    def test_listener_count_zero_for_new_event(self):
        assert EventBus.listener_count("new") == 0

    def test_listener_count_correct_after_subscribe(self):
        EventBus.subscribe("ev", MagicMock())
        EventBus.subscribe("ev", MagicMock())
        assert EventBus.listener_count("ev") == 2

    def test_pending_count_zero_initially(self):
        assert EventBus.pending_count() == 0

    def test_pending_count_after_emit_deferred(self):
        EventBus.emit_deferred("a")
        EventBus.emit_deferred("b")
        EventBus.emit_deferred("c")
        assert EventBus.pending_count() == 3


# ─────────────────────────────────────────────────────────────────
class TestInstanceAlias:
    """Instâncias devem delegar para o estado global (retrocompat)."""

    def test_publish_calls_listener(self):
        cb  = MagicMock()
        bus = EventBus()
        EventBus.subscribe("ev", cb)
        bus.publish("ev", val=99)
        cb.assert_called_once_with(val=99)

    def test_has_subscribers_true(self):
        bus = EventBus()
        EventBus.subscribe("ev", MagicMock())
        assert bus.has_subscribers("ev") is True

    def test_has_subscribers_false(self):
        assert EventBus().has_subscribers("ghost") is False

    def test_subscribers_count(self):
        EventBus.subscribe("ev", MagicMock())
        EventBus.subscribe("ev", MagicMock())
        assert EventBus().subscribers_count("ev") == 2

    def test_unsubscribe_all_clears_event(self):
        EventBus.subscribe("ev", MagicMock())
        EventBus().unsubscribe_all("ev")
        assert EventBus.listener_count("ev") == 0


# ─────────────────────────────────────────────────────────────────
class TestEdgeCases:
    def test_listener_subscribes_during_emit(self):
        """Listener adicionado durante emit não é chamado no mesmo ciclo."""
        late = MagicMock()
        def spawner():
            EventBus.subscribe("ev", late)
        EventBus.subscribe("ev", spawner)
        EventBus.emit("ev")
        late.assert_not_called()
        EventBus.emit("ev")
        late.assert_called_once()

    def test_listener_unsubscribes_self_during_emit(self):
        """Listener pode se remover durante emissão sem causar erro."""
        cb = MagicMock()
        def self_remove():
            EventBus.unsubscribe("ev", self_remove)
        EventBus.subscribe("ev", self_remove)
        EventBus.subscribe("ev", cb)
        EventBus.emit("ev")
        cb.assert_called_once()

    def test_emit_with_no_kwargs(self):
        cb = MagicMock()
        EventBus.subscribe("ping", cb)
        EventBus.emit("ping")
        cb.assert_called_once_with()

    def test_multiple_deferred_same_event(self):
        cb = MagicMock()
        EventBus.subscribe("ev", cb)
        EventBus.emit_deferred("ev", n=1)
        EventBus.emit_deferred("ev", n=2)
        EventBus.flush()
        assert cb.call_args_list == [call(n=1), call(n=2)]
