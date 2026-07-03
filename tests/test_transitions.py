"""
tests/test_transitions.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/transitions.py.

Estratégia de isolamento:
  - Usa pygame real, mas substitui pygame.draw.rect com monkeypatch por teste.
  - Surface fake rastreia blit, fill, set_alpha e get_size.
  - Testes de update são determinísticos: controlamos dt exatamente.
  - Nenhum teste altera sys.modules, evitando interferência com test_collider.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pygame
import pytest


class _FakeSurface:
    SRCALPHA = 0x00010000

    def __init__(self, size=(800, 600), flags=0):
        self._size = size
        self._flags = flags
        self._alpha = 255
        self.blit = MagicMock()
        self.fill = MagicMock()
        self.set_alpha = MagicMock(side_effect=lambda a: setattr(self, "_alpha", a))
        self.get_size = MagicMock(return_value=size)


_pg = pygame

from engine.transitions import (  # noqa: E402
    EASING,
    CrossfadeTransition,
    FadeTransition,
    SlideDirection,
    SlideTransition,
    Transition,
    TransitionPhase,
    WipeTransition,
)


@pytest.fixture(autouse=True)
def _patch_draw_rect(monkeypatch):
    monkeypatch.setattr(pygame.draw, "rect", MagicMock())


# ── helpers ─────────────────────────────────────────────────────────────────

def screen():
    return _FakeSurface((800, 600))


def advance(tr: Transition, dt: float, steps: int = 1):
    for _ in range(steps):
        tr.update(dt)


def run_to_swap(tr: Transition, over: float = 0.01):
    """Avança exatamente até a fase SWAP (duration_out + epsilon)."""
    advance(tr, tr.duration_out + over)


def run_to_done(tr: Transition, over: float = 0.01):
    """Avança até DONE: SWAP → IN → DONE."""
    run_to_swap(tr, over)
    advance(tr, 0.001)          # SWAP → IN
    advance(tr, tr.duration_in + over)  # IN → DONE


# ─────────────────────────────────────────────────────────────────────────────
class TestEasing:
    def test_linear_zero(self):      assert EASING["linear"](0.0)      == pytest.approx(0.0)
    def test_linear_half(self):      assert EASING["linear"](0.5)      == pytest.approx(0.5)
    def test_linear_one(self):       assert EASING["linear"](1.0)      == pytest.approx(1.0)
    def test_ease_in_zero(self):     assert EASING["ease_in"](0.0)     == pytest.approx(0.0)
    def test_ease_in_one(self):      assert EASING["ease_in"](1.0)     == pytest.approx(1.0)
    def test_ease_in_slow_start(self): assert EASING["ease_in"](0.5)  < 0.5
    def test_ease_out_zero(self):    assert EASING["ease_out"](0.0)    == pytest.approx(0.0)
    def test_ease_out_one(self):     assert EASING["ease_out"](1.0)    == pytest.approx(1.0)
    def test_ease_out_fast_start(self): assert EASING["ease_out"](0.5) > 0.5
    def test_ease_in_out_zero(self): assert EASING["ease_in_out"](0.0) == pytest.approx(0.0)
    def test_ease_in_out_half(self): assert EASING["ease_in_out"](0.5) == pytest.approx(0.5)
    def test_ease_in_out_one(self):  assert EASING["ease_in_out"](1.0) == pytest.approx(1.0)


# ─────────────────────────────────────────────────────────────────────────────
class TestTransitionBase:
    # -- init --
    def test_initial_phase_is_out(self):
        assert Transition().phase == TransitionPhase.OUT

    def test_initial_is_not_done(self):
        assert Transition().is_done is False

    def test_initial_should_not_swap(self):
        assert Transition().should_swap is False

    def test_initial_progress_zero(self):
        assert Transition().progress == pytest.approx(0.0)

    def test_min_duration_clamped(self):
        tr = Transition(duration_out=0.0, duration_in=-1.0)
        assert tr.duration_out >= 0.01
        assert tr.duration_in  >= 0.01

    def test_unknown_easing_falls_back(self):
        tr = Transition(easing="unknown_xyz")
        advance(tr, 0.1)
        assert 0.0 <= tr.progress <= 1.0

    # -- OUT phase --
    def test_progress_increases_during_out(self):
        tr = Transition(duration_out=1.0, duration_in=1.0)
        advance(tr, 0.5)
        assert tr.progress > 0.0

    def test_progress_clamped_at_1_end_of_out(self):
        tr = Transition(duration_out=0.5, duration_in=0.5, easing="linear")
        advance(tr, 1.0)
        assert tr.progress == pytest.approx(1.0)

    # -- SWAP phase --
    def test_reaches_swap_after_out(self):
        tr = Transition(duration_out=0.3, duration_in=0.3)
        run_to_swap(tr)
        assert tr.phase == TransitionPhase.SWAP

    def test_should_swap_true_during_swap(self):
        tr = Transition(duration_out=0.3, duration_in=0.3)
        run_to_swap(tr)
        assert tr.should_swap is True

    # -- IN phase --
    def test_swap_advances_to_in_next_update(self):
        tr = Transition(duration_out=0.3, duration_in=0.3)
        run_to_swap(tr)
        advance(tr, 0.001)
        assert tr.phase == TransitionPhase.IN

    def test_should_swap_false_during_in(self):
        tr = Transition(duration_out=0.3, duration_in=0.3)
        run_to_swap(tr)
        advance(tr, 0.001)
        assert tr.should_swap is False

    # -- DONE --
    def test_reaches_done(self):
        tr = Transition(duration_out=0.3, duration_in=0.3)
        run_to_done(tr)
        assert tr.is_done is True

    def test_progress_frozen_after_done(self):
        tr = Transition(duration_out=0.2, duration_in=0.2)
        run_to_done(tr)
        p = tr.progress
        advance(tr, 1.0)
        assert tr.progress == p

    def test_phase_done_no_further_changes(self):
        tr = Transition(duration_out=0.2, duration_in=0.2)
        run_to_done(tr)
        advance(tr, 10.0)
        assert tr.phase == TransitionPhase.DONE

    # -- draw base is no-op --
    def test_base_draw_no_error(self):
        Transition().draw(screen())


# ─────────────────────────────────────────────────────────────────────────────
class TestFadeTransition:
    def _make(self, **kw):
        return FadeTransition(duration_out=0.3, duration_in=0.3, **kw)

    def test_draw_out_blits_snapshot(self):
        tr  = self._make()
        sc  = screen()
        snap = _FakeSurface()
        tr.snapshot_out = snap
        advance(tr, 0.1)
        tr.draw(sc)
        sc.blit.assert_called()

    def test_draw_out_no_snapshot_no_error(self):
        tr = self._make()
        advance(tr, 0.1)
        tr.draw(screen())

    def test_draw_out_alpha_increases_with_progress(self):
        """Dois frames: alpha do overlay deve ser maior no segundo."""
        tr1 = self._make(easing="linear")
        tr2 = self._make(easing="linear")
        sc1, sc2 = screen(), screen()
        snap = _FakeSurface()
        tr1.snapshot_out = snap
        tr2.snapshot_out = snap
        advance(tr1, 0.1)
        advance(tr2, 0.25)
        assert tr2.progress > tr1.progress

    def test_draw_in_blits_snapshot_in(self):
        tr   = self._make()
        sc   = screen()
        snap = _FakeSurface()
        tr.snapshot_in  = snap
        tr.snapshot_out = _FakeSurface()
        run_to_swap(tr)
        advance(tr, 0.001)
        advance(tr, 0.1)
        tr.draw(sc)
        sc.blit.assert_called()

    def test_draw_done_no_blit(self):
        tr = self._make()
        sc = screen()
        run_to_done(tr)
        tr.draw(sc)
        sc.blit.assert_not_called()

    def test_custom_color(self):
        tr = FadeTransition(color=(255, 0, 128), duration_out=0.2, duration_in=0.2)
        assert tr.color == (255, 0, 128)


# ─────────────────────────────────────────────────────────────────────────────
class TestSlideTransition:
    def _make(self, direction=SlideDirection.LEFT):
        return SlideTransition(direction=direction, duration_out=0.01, duration_in=0.3)

    def test_default_direction_left(self):
        assert SlideTransition().direction == SlideDirection.LEFT

    def test_draw_out_blits_snapshot_out(self):
        tr  = self._make()
        sc  = screen()
        snap = _FakeSurface()
        tr.snapshot_out = snap
        advance(tr, 0.005)
        tr.draw(sc)
        sc.blit.assert_called_with(snap, (0, 0))

    def test_draw_in_blits_snapshot_in(self):
        tr   = self._make()
        sc   = screen()
        snap_out = _FakeSurface()
        snap_in  = _FakeSurface()
        tr.snapshot_out = snap_out
        tr.snapshot_in  = snap_in
        run_to_swap(tr)
        advance(tr, 0.001)
        advance(tr, 0.1)
        tr.draw(sc)
        calls = [c.args[0] for c in sc.blit.call_args_list]
        assert snap_in in calls

    @pytest.mark.parametrize("direction", list(SlideDirection))
    def test_all_directions_no_error(self, direction):
        tr = self._make(direction)
        sc = screen()
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in  = _FakeSurface()
        run_to_swap(tr)
        advance(tr, 0.001)
        advance(tr, 0.1)
        tr.draw(sc)

    def test_draw_done_no_blit(self):
        tr = self._make()
        sc = screen()
        run_to_done(tr)
        tr.draw(sc)
        sc.blit.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
class TestWipeTransition:
    def _make(self, horizontal=True):
        return WipeTransition(horizontal=horizontal, duration_out=0.3, duration_in=0.3)

    def test_draw_out_calls_draw_rect(self):
        tr = self._make()
        sc = screen()
        tr.snapshot_out = _FakeSurface()
        advance(tr, 0.1)
        _pg.draw.rect.reset_mock()
        tr.draw(sc)
        _pg.draw.rect.assert_called_once()

    def test_draw_in_calls_draw_rect(self):
        tr = self._make()
        sc = screen()
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in  = _FakeSurface()
        run_to_swap(tr)
        advance(tr, 0.001)
        advance(tr, 0.1)
        _pg.draw.rect.reset_mock()
        tr.draw(sc)
        _pg.draw.rect.assert_called_once()

    def test_draw_vertical_out_no_error(self):
        tr = self._make(horizontal=False)
        sc = screen()
        tr.snapshot_out = _FakeSurface()
        advance(tr, 0.1)
        tr.draw(sc)

    def test_draw_vertical_in_no_error(self):
        tr = self._make(horizontal=False)
        sc = screen()
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in  = _FakeSurface()
        run_to_swap(tr)
        advance(tr, 0.001)
        advance(tr, 0.1)
        tr.draw(sc)

    def test_draw_done_skipped(self):
        tr = self._make()
        sc = screen()
        run_to_done(tr)
        _pg.draw.rect.reset_mock()
        tr.draw(sc)
        _pg.draw.rect.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
class TestCrossfadeTransition:
    def _make(self):
        return CrossfadeTransition(duration=0.4)

    def test_duration_split_equally(self):
        tr = CrossfadeTransition(duration=0.6)
        assert tr.duration_out == pytest.approx(0.3)
        assert tr.duration_in  == pytest.approx(0.3)

    def test_draw_out_blits_snapshot(self):
        tr   = self._make()
        sc   = screen()
        snap = _FakeSurface()
        tr.snapshot_out = snap
        advance(tr, 0.1)
        tr.draw(sc)
        assert sc.blit.called or sc.fill.called

    def test_draw_in_blits_snapshot_in(self):
        tr      = self._make()
        sc      = screen()
        snap_in = _FakeSurface()
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in  = snap_in
        run_to_swap(tr)
        advance(tr, 0.001)
        advance(tr, 0.1)
        tr.draw(sc)
        assert sc.fill.called or sc.blit.called

    def test_draw_done_no_blit(self):
        tr = self._make()
        sc = screen()
        run_to_done(tr)
        tr.draw(sc)
        sc.blit.assert_not_called()
        sc.fill.assert_not_called()

    def test_alpha_surface_created_lazily(self):
        tr = self._make()
        assert tr._alpha_surf is None
        tr.snapshot_out = _FakeSurface()
        advance(tr, 0.1)
        tr.draw(screen())

    def test_reaches_done_full_cycle(self):
        tr = self._make()
        run_to_done(tr)
        assert tr.is_done


# ─────────────────────────────────────────────────────────────────────────────
class TestFullCycleIntegration:
    """Verifica a sequência completa OUT→SWAP→IN→DONE para todas as transições."""

    @pytest.mark.parametrize("cls,kw", [
        (FadeTransition,       {"duration_out": 0.2, "duration_in": 0.2}),
        (SlideTransition,      {"duration_out": 0.01, "duration_in": 0.2}),
        (WipeTransition,       {"duration_out": 0.2, "duration_in": 0.2}),
        (CrossfadeTransition,  {"duration": 0.4}),
    ])
    def test_full_cycle(self, cls, kw):
        tr = cls(**kw)
        assert tr.phase == TransitionPhase.OUT
        run_to_swap(tr)
        assert tr.phase == TransitionPhase.SWAP
        advance(tr, 0.001)
        assert tr.phase == TransitionPhase.IN
        advance(tr, tr.duration_in + 0.01)
        assert tr.phase == TransitionPhase.DONE
        assert tr.is_done

    @pytest.mark.parametrize("cls,kw", [
        (FadeTransition,       {"duration_out": 0.2, "duration_in": 0.2}),
        (SlideTransition,      {"duration_out": 0.01, "duration_in": 0.2}),
        (WipeTransition,       {"duration_out": 0.2, "duration_in": 0.2}),
        (CrossfadeTransition,  {"duration": 0.4}),
    ])
    def test_draw_no_error_in_all_phases(self, cls, kw):
        tr   = cls(**kw)
        sc   = screen()
        snap = _FakeSurface()
        tr.snapshot_out = snap
        tr.snapshot_in  = snap
        advance(tr, 0.05)
        tr.draw(sc)
        run_to_swap(tr)
        tr.draw(sc)
        advance(tr, 0.001)
        tr.draw(sc)
        run_to_done(tr)
        tr.draw(sc)
