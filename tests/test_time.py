"""
tests/test_time.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/time.py (Time).

Estratégia de isolamento:
  - pygame.time.Clock é stubado: `tick()` retorna um valor controlado
    em milissegundos, `get_fps()` retorna um float configurável.
  - `Time._current` é limpo antes/depois de cada teste para não
    vazar estado entre testes.
  - Nenhum loop da Application é executado; `time.tick()` é chamado
    diretamente com o valor de ms injetado via `_clock.tick.return_value`.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────

class _FakeClock:
    """Clock fictício: tick() retorna ms configurável, get_fps() também."""
    _fake = True

    def __init__(self):
        self.tick = MagicMock(return_value=16)      # ~60 fps
        self.get_fps = MagicMock(return_value=60.0)


def _ensure_pygame_time_stub():
    """
    Garante um pygame.time.Clock fake e controlável.

    O pytest coleta vários módulos no mesmo processo. Se outro teste importar
    o pygame real antes deste arquivo, pygame.time.Clock será uma classe nativa
    sem `.return_value`, quebrando a preparação do teste. Por isso a substituição
    é feita sempre, preservando o módulo pygame existente quando ele já existe.
    """
    if "pygame" not in sys.modules:
        pg = ModuleType("pygame")
        sys.modules["pygame"] = pg
    else:
        pg = sys.modules["pygame"]

    time_mod = getattr(pg, "time", None)
    if time_mod is None:
        time_mod = ModuleType("pygame.time")
        pg.time = time_mod

    time_mod.Clock = _FakeClock
    sys.modules["pygame.time"] = time_mod
    return pg


_pg = _ensure_pygame_time_stub()

from engine.time import Time  # noqa: E402


# ── fixture ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_current():
    Time._current = None
    yield
    Time._current = None


@pytest.fixture()
def t():
    """Time com FakeClock pronto para tick()."""
    return Time(target_fps=60, dt_cap=0.1)


# ── helpers ────────────────────────────────────────────────────────────────
def _tick(t: Time, ms: int, fps: float = 60.0) -> float:
    """Injeta ms no clock e executa um tick."""
    t._clock.tick.return_value = ms
    t._clock.get_fps.return_value = fps
    return t.tick()


# ── TestInit ─────────────────────────────────────────────────────────────────
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


# ── TestTick ─────────────────────────────────────────────────────────────────
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


# ── TestScaledDelta ──────────────────────────────────────────────────────────────
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


# ── TestElapsed ────────────────────────────────────────────────────────────────
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
        assert t.elapsed == pytest.approx(0.016)  # só o primeiro frame

    def test_elapsed_uses_scale(self, t):
        t.scale = 0.5
        _tick(t, 16)
        _tick(t, 16)
        assert t.elapsed == pytest.approx(0.016)  # 2 * 0.016 * 0.5

    def test_elapsed_zero_with_zero_ms(self, t):
        _tick(t, 0)
        assert t.elapsed == pytest.approx(0.0)
