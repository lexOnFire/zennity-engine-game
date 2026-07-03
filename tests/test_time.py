"""
tests/test_time.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/time.py.

Estratégia de isolamento:
  - pygame.time.Clock é substituído por MagicMock de forma incondicional,
    mesmo quando o pygame real já foi importado por outro teste.
  - _clock.tick é configurado para retornar milissegundos fixos em cada teste
    (16 ms = ~60 fps) via return_value / side_effect.
  - Time._current é resetado para None antes e depois de cada teste
    pelo fixture autouse, garantindo isolamento de Time.current().
  - Nenhum loop real, nenhuma janela pygame.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# ── stub/patch pygame.time.Clock ─────────────────────────────────────────────
# Alguns testes importam pygame real antes deste módulo. Nesse cenário,
# pygame.time.Clock é uma classe nativa e não possui `.return_value`.
# Para manter este teste determinístico, garantimos sempre um Clock mockável.
if "pygame" not in sys.modules:
    _pg = ModuleType("pygame")
    sys.modules["pygame"] = _pg
else:
    _pg = sys.modules["pygame"]

_pg_time = getattr(_pg, "time", None)
if _pg_time is None:
    _pg_time = ModuleType("pygame.time")
    _pg.time = _pg_time
    sys.modules["pygame.time"] = _pg_time
else:
    sys.modules["pygame.time"] = _pg_time

_fake_clock = MagicMock()
_fake_clock.tick = MagicMock(return_value=16)
_fake_clock.get_fps = MagicMock(return_value=62.5)
_pg_time.Clock = MagicMock(return_value=_fake_clock)

from engine.time import Time  # noqa: E402


# ── fixture autouse ──────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def reset_time():
    Time._current = None
    _fake_clock.tick.reset_mock()
    _fake_clock.tick.return_value = 16
    _fake_clock.get_fps.reset_mock()
    _fake_clock.get_fps.return_value = 62.5
    yield
    Time._current = None


def _make_time(**kw) -> Time:
    """Cria uma instância de Time com defaults sensíveis para testes."""
    return Time(**kw)


# ────────────────────────────────────────────────────────────────────────────
class TestInit:
    def test_defaults_delta_zero(self):
        t = _make_time()
        assert t.delta == pytest.approx(0.0)

    def test_defaults_frame_zero(self):
        t = _make_time()
        assert t.frame == 0

    def test_defaults_elapsed_zero(self):
        t = _make_time()
        assert t.elapsed == pytest.approx(0.0)

    def test_defaults_scale_one(self):
        t = _make_time()
        assert t.scale == pytest.approx(1.0)

    def test_defaults_not_paused(self):
        t = _make_time()
        assert t.paused is False

    def test_defaults_target_fps(self):
        t = _make_time(target_fps=30)
        assert t.fps_target == 30

    def test_defaults_dt_cap(self):
        t = _make_time(dt_cap=0.05)
        assert t.dt_cap == pytest.approx(0.05)

    def test_registers_as_current(self):
        t = _make_time()
        assert Time._current is t

    def test_second_instance_replaces_current(self):
        _make_time()
        t2 = _make_time()
        assert Time._current is t2


# ────────────────────────────────────────────────────────────────────────────
class TestTick:
    def test_tick_increments_frame(self):
        t = _make_time()
        t.tick()
        assert t.frame == 1

    def test_tick_twice_increments_to_two(self):
        t = _make_time()
        t.tick(); t.tick()
        assert t.frame == 2

    def test_tick_sets_raw_delta(self):
        _fake_clock.tick.return_value = 20
        t = _make_time()
        t.tick()
        assert t.raw_delta == pytest.approx(0.020)

    def test_tick_sets_delta_capped(self):
        """raw_delta > dt_cap → delta é clamped ao cap."""
        _fake_clock.tick.return_value = 500
        t = _make_time(dt_cap=0.1)
        t.tick()
        assert t.delta == pytest.approx(0.1)

    def test_tick_delta_below_cap_not_capped(self):
        _fake_clock.tick.return_value = 16
        t = _make_time(dt_cap=0.1)
        t.tick()
        assert t.delta == pytest.approx(0.016)

    def test_tick_raw_delta_not_capped(self):
        """raw_delta nunca é clamped."""
        _fake_clock.tick.return_value = 500
        t = _make_time(dt_cap=0.1)
        t.tick()
        assert t.raw_delta == pytest.approx(0.5)

    def test_tick_returns_delta(self):
        _fake_clock.tick.return_value = 16
        t = _make_time()
        ret = t.tick()
        assert ret == pytest.approx(t.delta)

    def test_tick_updates_fps_actual(self):
        _fake_clock.get_fps.return_value = 59.9
        t = _make_time()
        t.tick()
        assert t.fps_actual == pytest.approx(59.9)

    def test_tick_calls_clock_tick_with_target_fps(self):
        t = _make_time(target_fps=30)
        t.tick()
        _fake_clock.tick.assert_called_with(30)


# ────────────────────────────────────────────────────────────────────────────
class TestScaledDelta:
    def test_scaled_delta_equals_delta_times_scale(self):
        _fake_clock.tick.return_value = 16
        t = _make_time()
        t.scale = 2.0
        t.tick()
        assert t.scaled_delta == pytest.approx(t.delta * 2.0)

    def test_scale_half_halves_scaled_delta(self):
        _fake_clock.tick.return_value = 16
        t = _make_time()
        t.scale = 0.5
        t.tick()
        assert t.scaled_delta == pytest.approx(t.delta * 0.5)

    def test_scale_zero_zeroes_scaled_delta(self):
        t = _make_time()
        t.scale = 0.0
        t.tick()
        assert t.scaled_delta == pytest.approx(0.0)
