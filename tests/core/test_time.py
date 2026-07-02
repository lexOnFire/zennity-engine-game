"""
tests/core/test_time.py
────────────────────────────────────────────────────────────────
Commit 8: valida o contrato público de Time.
Todos os testes mockam pygame.time.Clock para rodar headless.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixture: cria Time com clock mockado
# ---------------------------------------------------------------------------

@pytest.fixture
def make_time():
    """Retorna uma factory que cria Time com Clock mockado."""
    def _factory(tick_ms: int = 16, target_fps: int = 60, dt_cap: float = 0.1):
        from engine.core import Time
        with patch("engine.time.pygame.time.Clock") as MockClock:
            clock_inst = MagicMock()
            clock_inst.tick.return_value = tick_ms
            clock_inst.get_fps.return_value = float(1000 / tick_ms)
            MockClock.return_value = clock_inst
            t = Time(target_fps=target_fps, dt_cap=dt_cap)
            t._clock = clock_inst  # garante que o mock está em uso
        return t
    return _factory


# ===========================================================================
# 1. Defaults
# ===========================================================================

class TestDefaults:
    def test_frame_zero(self, make_time):
        t = make_time()
        assert t.frame == 0

    def test_elapsed_zero(self, make_time):
        t = make_time()
        assert t.elapsed == pytest.approx(0.0)

    def test_scale_one(self, make_time):
        t = make_time()
        assert t.scale == pytest.approx(1.0)

    def test_paused_false(self, make_time):
        t = make_time()
        assert t.paused is False

    def test_delta_zero(self, make_time):
        t = make_time()
        assert t.delta == pytest.approx(0.0)

    def test_fps_target_set(self, make_time):
        t = make_time(target_fps=30)
        assert t.fps_target == 30


# ===========================================================================
# 2. tick() — frame e delta
# ===========================================================================

class TestTick:
    def test_tick_increments_frame(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        assert t.frame == 1

    def test_tick_multiple_frames(self, make_time):
        t = make_time(tick_ms=16)
        for _ in range(5):
            t.tick()
        assert t.frame == 5

    def test_tick_sets_delta(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        assert t.delta == pytest.approx(0.016)

    def test_tick_sets_raw_delta(self, make_time):
        t = make_time(tick_ms=33)
        t.tick()
        assert t.raw_delta == pytest.approx(0.033)

    def test_tick_returns_delta(self, make_time):
        t = make_time(tick_ms=16)
        returned = t.tick()
        assert returned == pytest.approx(t.delta)

    def test_tick_sets_scaled_delta_normal(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        assert t.scaled_delta == pytest.approx(0.016)  # scale=1.0


# ===========================================================================
# 3. dt_cap
# ===========================================================================

class TestDtCap:
    def test_delta_capped(self, make_time):
        """Frame muito lento (500ms): delta deve ser limitado ao dt_cap."""
        t = make_time(tick_ms=500, dt_cap=0.1)
        t.tick()
        assert t.delta == pytest.approx(0.1)

    def test_raw_delta_not_capped(self, make_time):
        """raw_delta nunca é limitado pelo dt_cap."""
        t = make_time(tick_ms=500, dt_cap=0.1)
        t.tick()
        assert t.raw_delta == pytest.approx(0.5)

    def test_delta_within_cap_unchanged(self, make_time):
        """Frame rápido: delta não deve ser alterado."""
        t = make_time(tick_ms=8, dt_cap=0.1)
        t.tick()
        assert t.delta == pytest.approx(0.008)


# ===========================================================================
# 4. scale
# ===========================================================================

class TestScale:
    def test_scaled_delta_with_half_speed(self, make_time):
        t = make_time(tick_ms=16)
        t.scale = 0.5
        t.tick()
        assert t.scaled_delta == pytest.approx(0.008)

    def test_scaled_delta_with_double_speed(self, make_time):
        t = make_time(tick_ms=16)
        t.scale = 2.0
        t.tick()
        assert t.scaled_delta == pytest.approx(0.032)

    def test_scale_zero_stops_scaled_delta(self, make_time):
        t = make_time(tick_ms=16)
        t.scale = 0.0
        t.tick()
        assert t.scaled_delta == pytest.approx(0.0)

    def test_delta_not_affected_by_scale(self, make_time):
        """delta (sem scale) nunca é afetado por t.scale."""
        t = make_time(tick_ms=16)
        t.scale = 99.0
        t.tick()
        assert t.delta == pytest.approx(0.016)


# ===========================================================================
# 5. paused
# ===========================================================================

class TestPaused:
    def test_paused_sets_scaled_delta_to_zero(self, make_time):
        t = make_time(tick_ms=16)
        t.paused = True
        t.tick()
        assert t.scaled_delta == pytest.approx(0.0)

    def test_paused_does_not_accumulate_elapsed(self, make_time):
        t = make_time(tick_ms=16)
        t.paused = True
        t.tick()
        t.tick()
        assert t.elapsed == pytest.approx(0.0)

    def test_paused_does_not_affect_delta(self, make_time):
        """delta continua sendo calculado mesmo pausado."""
        t = make_time(tick_ms=16)
        t.paused = True
        t.tick()
        assert t.delta == pytest.approx(0.016)

    def test_unpause_resumes_elapsed(self, make_time):
        t = make_time(tick_ms=16)
        t.paused = True
        t.tick()  # não acumula
        t.paused = False
        t.tick()  # acumula 0.016
        assert t.elapsed == pytest.approx(0.016)


# ===========================================================================
# 6. elapsed
# ===========================================================================

class TestElapsed:
    def test_elapsed_accumulates_scaled_delta(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        t.tick()
        assert t.elapsed == pytest.approx(0.032)

    def test_elapsed_uses_scale(self, make_time):
        t = make_time(tick_ms=16)
        t.scale = 2.0
        t.tick()  # scaled_delta = 0.032
        assert t.elapsed == pytest.approx(0.032)


# ===========================================================================
# 7. Aliases
# ===========================================================================

class TestAliases:
    def test_fps_property_alias(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        assert t.fps == t.fps_actual

    def test_dt_property_alias(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        assert t.dt == t.delta


# ===========================================================================
# 8. current()
# ===========================================================================

class TestCurrent:
    def test_current_returns_instance(self, make_time):
        from engine.core import Time
        t = make_time()
        assert Time.current() is t

    def test_current_raises_before_init(self):
        from engine.core import Time
        Time._current = None
        with pytest.raises(RuntimeError):
            Time.current()


# ===========================================================================
# 9. __repr__
# ===========================================================================

class TestRepr:
    def test_repr_contains_frame(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        assert "frame=1" in repr(t)

    def test_repr_contains_scale(self, make_time):
        t = make_time()
        t.scale = 0.5
        assert "scale=0.5" in repr(t)

    def test_repr_contains_paused(self, make_time):
        t = make_time()
        t.paused = True
        assert "paused=True" in repr(t)

    def test_repr_contains_elapsed(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        assert "elapsed=" in repr(t)
