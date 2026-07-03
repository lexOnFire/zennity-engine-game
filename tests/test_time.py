"""
tests/test_time.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/time.py (Time).

Estratégia de isolamento:
  - pygame.time.Clock é substituído por um fake usando monkeypatch.
  - O patch vale apenas durante cada teste e não polui outros módulos.
  - `Time._current` é limpo antes/depois de cada teste para não vazar estado.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pygame
import pytest

from engine.time import Time


class _FakeClock:
    """Clock fictício: tick() retorna ms configurável, get_fps() também."""

    def __init__(self):
        self.tick = MagicMock(return_value=16)
        self.get_fps = MagicMock(return_value=60.0)


@pytest.fixture(autouse=True)
def reset_current(monkeypatch):
    Time._current = None
    monkeypatch.setattr(pygame.time, "Clock", _FakeClock)
    yield
    Time._current = None


@pytest.fixture()
def t():
    """Time com FakeClock pronto para tick()."""
    return Time(target_fps=60, dt_cap=0.1)


def _tick(t: Time, ms: int, fps: float = 60.0) -> float:
    """Injeta ms no clock e executa um tick."""
    t._clock.tick.return_value = ms
    t._clock.get_fps.return_value = fps
    return t.tick()


class TestInit:
    def test_fps_target_stored(self):
        assert Time(target_fps=30).fps_target == 30

    def test_dt_cap_stored(self):
        assert Time(dt_cap=0.05).dt_cap == pytest.approx(0.05)

    def test_delta_zero(self, t):
        assert t.delta == pytest.approx(0.0)

    def test_scaled_delta_zero(self, t):
        assert t.scaled_delta == pytest.approx(0.0)

    def test_raw_delta_zero(self, t):
        assert t.raw_delta == pytest.approx(0.0)

    def test_elapsed_zero(self, t):
        assert t.elapsed == pytest.approx(0.0)

    def test_frame_zero(self, t):
        assert t.frame == 0

    def test_scale_one(self, t):
        assert t.scale == pytest.approx(1.0)

    def test_paused_false(self, t):
        assert t.paused is False

    def test_registers_as_current(self, t):
        assert Time._current is t

    def test_second_instance_overwrites_current(self, t):
        t2 = Time()
        assert Time._current is t2


class TestTick:
    def test_tick_returns_delta(self, t):
        dt = _tick(t, 16)
        assert dt == pytest.approx(0.016)

    def test_raw_delta_set(self, t):
        _tick(t, 50)
        assert t.raw_delta == pytest.approx(0.05)

    def test_delta_capped(self, t):
        """Frame de 500 ms é recortado para dt_cap=0.1."""
        _tick(t, 500)
        assert t.delta == pytest.approx(0.1)

    def test_raw_delta_not_capped(self, t):
        """raw_delta nunca é cortado pelo cap."""
        _tick(t, 500)
        assert t.raw_delta == pytest.approx(0.5)

    def test_delta_below_cap_not_changed(self, t):
        _tick(t, 16)
        assert t.delta == pytest.approx(0.016)

    def test_frame_increments(self, t):
        _tick(t, 16)
        _tick(t, 16)
        assert t.frame == 2

    def test_frame_starts_at_one_after_first_tick(self, t):
        _tick(t, 16)
        assert t.frame == 1

    def test_fps_actual_updated(self, t):
        _tick(t, 16, fps=58.3)
        assert t.fps_actual == pytest.approx(58.3)

    def test_fps_property_mirrors_fps_actual(self, t):
        _tick(t, 16, fps=55.0)
        assert t.fps == pytest.approx(55.0)

    def test_dt_property_mirrors_delta(self, t):
        _tick(t, 20)
        assert t.dt == pytest.approx(t.delta)

    def test_clock_tick_called_with_fps_target(self, t):
        t._clock.tick.return_value = 16
        t.tick()
        t._clock.tick.assert_called_with(t.fps_target)


class TestScaledDelta:
    def test_scaled_delta_normal(self, t):
        """scale=1.0 => scaled_delta == delta."""
        _tick(t, 16)
        assert t.scaled_delta == pytest.approx(t.delta)

    def test_scaled_delta_half_speed(self, t):
        t.scale = 0.5
        _tick(t, 16)
        assert t.scaled_delta == pytest.approx(0.016 * 0.5)

    def test_scaled_delta_double_speed(self, t):
        t.scale = 2.0
        _tick(t, 16)
        assert t.scaled_delta == pytest.approx(0.016 * 2.0)

    def test_scaled_delta_zero_when_paused(self, t):
        t.paused = True
        _tick(t, 16)
        assert t.scaled_delta == pytest.approx(0.0)

    def test_paused_does_not_affect_delta(self, t):
        t.paused = True
        _tick(t, 16)
        assert t.delta == pytest.approx(0.016)

    def test_scale_zero_gives_zero_scaled(self, t):
        t.scale = 0.0
        _tick(t, 16)
        assert t.scaled_delta == pytest.approx(0.0)


class TestElapsed:
    def test_elapsed_accumulates_scaled_delta(self, t):
        _tick(t, 16)
        _tick(t, 16)
        assert t.elapsed == pytest.approx(0.032)

    def test_elapsed_frozen_when_paused(self, t):
        _tick(t, 16)
        t.paused = True
        _tick(t, 16)
        _tick(t, 16)
        assert t.elapsed == pytest.approx(0.016)

    def test_elapsed_uses_scale(self, t):
        t.scale = 0.5
        _tick(t, 16)
        _tick(t, 16)
        assert t.elapsed == pytest.approx(0.016)

    def test_elapsed_zero_with_zero_ms(self, t):
        _tick(t, 0)
        assert t.elapsed == pytest.approx(0.0)
