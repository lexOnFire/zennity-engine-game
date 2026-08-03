"""
tests/core/test_time.py
────────────────────────────────────────────────────────────────
Commit 13: suite completa do Time.

Grupos:
  TestDefaults    (6)  — estado inicial
  TestTick        (7)  — frame, delta, raw_delta, retorno de tick()
  TestDtCap       (3)  — capping de delta, raw_delta livre
  TestScale       (5)  — scaled_delta com vários fatores, delta imune
  TestPaused      (5)  — scaled=0, elapsed congela, delta normal, retomar
  TestElapsed     (4)  — acumula, usa scale, não acumula pausado
  TestSlowMo      (3)  — slow-motion (scale<1) e fast-forward (scale>1)
  TestAliases     (3)  — fps, dt, fps_target
  TestCurrent     (3)  — current(), RuntimeError sem init, registra na criação
  TestRepr        (4)  — frame, scale, paused, elapsed no repr

Total esperado: 43 testes.

Todos os testes mockam pygame.time.Clock para rodar headless.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ───────────────────────────────────────────────────────────────────
@pytest.fixture
def make_time():
    """Factory que cria Time com Clock mockado."""
    def _factory(tick_ms: int = 16, target_fps: int = 60, dt_cap: float = 0.1):
        from engine.time import Time
        with patch("engine.time.pygame.time.Clock") as MockClock:
            clock_inst = MagicMock()
            clock_inst.tick.return_value = tick_ms
            clock_inst.get_fps.return_value = float(1000 / tick_ms) if tick_ms else 0.0
            MockClock.return_value = clock_inst
            t = Time(target_fps=target_fps, dt_cap=dt_cap)
            t._clock = clock_inst
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

    def test_tick_updates_fps_actual(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()
        assert t.fps_actual > 0

    def test_clock_receives_target_fps(self, make_time):
        t = make_time(tick_ms=16, target_fps=30)
        t.tick()
        t._clock.tick.assert_called_once_with(30)


# ===========================================================================
# 3. dt_cap
# ===========================================================================

class TestDtCap:
    def test_delta_capped(self, make_time):
        t = make_time(tick_ms=500, dt_cap=0.1)
        t.tick()
        assert t.delta == pytest.approx(0.1)

    def test_raw_delta_not_capped(self, make_time):
        t = make_time(tick_ms=500, dt_cap=0.1)
        t.tick()
        assert t.raw_delta == pytest.approx(0.5)

    def test_delta_within_cap_unchanged(self, make_time):
        t = make_time(tick_ms=8, dt_cap=0.1)
        t.tick()
        assert t.delta == pytest.approx(0.008)

    def test_custom_cap_is_stored_and_applied(self, make_time):
        t = make_time(tick_ms=200, dt_cap=0.05)
        t.tick()
        assert t.dt_cap == pytest.approx(0.05)
        assert t.delta == pytest.approx(0.05)

    def test_delta_exactly_at_cap_is_unchanged(self, make_time):
        t = make_time(tick_ms=50, dt_cap=0.05)
        t.tick()
        assert t.raw_delta == pytest.approx(0.05)
        assert t.delta == pytest.approx(0.05)


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
        t = make_time(tick_ms=16)
        t.scale = 99.0
        t.tick()
        assert t.delta == pytest.approx(0.016)

    def test_scale_change_mid_run(self, make_time):
        """Mudar scale entre frames afeta apenas os frames seguintes."""
        t = make_time(tick_ms=16)
        t.tick()  # scale=1.0 → elapsed=0.016
        t.scale = 2.0
        t.tick()  # scale=2.0 → scaled_delta=0.032
        assert t.elapsed == pytest.approx(0.016 + 0.032)


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
        t = make_time(tick_ms=16)
        t.paused = True
        t.tick()
        assert t.delta == pytest.approx(0.016)

    def test_unpause_resumes_elapsed(self, make_time):
        t = make_time(tick_ms=16)
        t.paused = True
        t.tick()          # não acumula
        t.paused = False
        t.tick()          # acumula 0.016
        assert t.elapsed == pytest.approx(0.016)

    def test_paused_still_increments_frame(self, make_time):
        """Frame counter não para quando pausado."""
        t = make_time(tick_ms=16)
        t.paused = True
        t.tick()
        t.tick()
        assert t.frame == 2


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

    def test_elapsed_not_accumulated_when_paused(self, make_time):
        t = make_time(tick_ms=16)
        t.tick()          # +0.016
        t.paused = True
        t.tick()          # +0
        assert t.elapsed == pytest.approx(0.016)

    def test_elapsed_increases_monotonically(self, make_time):
        t = make_time(tick_ms=16)
        prev = 0.0
        for _ in range(10):
            t.tick()
            assert t.elapsed >= prev
            prev = t.elapsed

    def test_zero_duration_frame_does_not_change_elapsed(self, make_time):
        t = make_time(tick_ms=0)
        t.tick()
        assert t.elapsed == pytest.approx(0.0)


# ===========================================================================
# 7. Slow-mo / fast-forward
# ===========================================================================

class TestSlowMo:
    def test_slow_motion_half_speed(self, make_time):
        t = make_time(tick_ms=16)
        t.scale = 0.5
        for _ in range(4):
            t.tick()
        # 4 frames × 0.016 × 0.5 = 0.032
        assert t.elapsed == pytest.approx(0.032)

    def test_fast_forward_double_speed(self, make_time):
        t = make_time(tick_ms=16)
        t.scale = 2.0
        for _ in range(4):
            t.tick()
        # 4 frames × 0.016 × 2.0 = 0.128
        assert t.elapsed == pytest.approx(0.128)

    def test_scale_ten_x(self, make_time):
        t = make_time(tick_ms=16)
        t.scale = 10.0
        t.tick()
        assert t.scaled_delta == pytest.approx(0.16)


# ===========================================================================
# 8. Aliases
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

    def test_fps_target_default(self, make_time):
        t = make_time(target_fps=60)
        assert t.fps_target == 60


# ===========================================================================
# 9. current()
# ===========================================================================

class TestCurrent:
    def test_current_returns_instance(self, make_time):
        from engine.time import Time
        t = make_time()
        assert Time.current() is t

    def test_current_raises_before_init(self):
        from engine.time import Time
        Time._current = None
        with pytest.raises(RuntimeError):
            Time.current()

    def test_new_instance_replaces_current(self, make_time):
        """A instância mais recente é sempre a ativa."""
        from engine.time import Time
        make_time()  # instância 1
        t2 = make_time()  # instância 2
        assert Time.current() is t2

    def test_current_exposes_latest_delta(self, make_time):
        from engine.time import Time
        t = make_time(tick_ms=16)
        t.tick()
        assert Time.current().delta == pytest.approx(0.016)


# ===========================================================================
# 10. __repr__
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
