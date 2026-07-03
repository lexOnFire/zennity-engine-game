"""Testes unitários de engine.transitions."""
from __future__ import annotations

from unittest.mock import MagicMock

import pygame
import pytest

from engine.transitions import (
    EASING,
    CrossfadeTransition,
    FadeTransition,
    SlideDirection,
    SlideTransition,
    Transition,
    TransitionPhase,
    WipeTransition,
)


class _FakeSurface:
    def __init__(self, size=(800, 600), flags=0):
        self._size = size
        self._flags = flags
        self.blit = MagicMock()
        self.fill = MagicMock()
        self.set_alpha = MagicMock()
        self.get_size = MagicMock(return_value=size)


def fake_screen() -> _FakeSurface:
    return _FakeSurface((800, 600))


def real_surface() -> pygame.Surface:
    return pygame.Surface((800, 600), pygame.SRCALPHA)


@pytest.fixture(autouse=True)
def _patch_draw_rect(monkeypatch):
    monkeypatch.setattr(pygame.draw, "rect", MagicMock())


def advance(tr: Transition, dt: float, steps: int = 1) -> None:
    for _ in range(steps):
        tr.update(dt)


def run_to_swap(tr: Transition, over: float = 0.01) -> None:
    advance(tr, tr.duration_out + over)


def run_to_done(tr: Transition, over: float = 0.01) -> None:
    run_to_swap(tr, over)
    advance(tr, 0.001)
    advance(tr, tr.duration_in + over)


class TestEasing:
    def test_linear(self):
        assert EASING["linear"](0.0) == pytest.approx(0.0)
        assert EASING["linear"](0.5) == pytest.approx(0.5)
        assert EASING["linear"](1.0) == pytest.approx(1.0)

    def test_ease_in(self):
        assert EASING["ease_in"](0.0) == pytest.approx(0.0)
        assert EASING["ease_in"](1.0) == pytest.approx(1.0)
        assert EASING["ease_in"](0.5) < 0.5

    def test_ease_out(self):
        assert EASING["ease_out"](0.0) == pytest.approx(0.0)
        assert EASING["ease_out"](1.0) == pytest.approx(1.0)
        assert EASING["ease_out"](0.5) > 0.5

    def test_ease_in_out(self):
        assert EASING["ease_in_out"](0.0) == pytest.approx(0.0)
        assert EASING["ease_in_out"](0.5) == pytest.approx(0.5)
        assert EASING["ease_in_out"](1.0) == pytest.approx(1.0)


class TestTransitionBase:
    def test_initial_state(self):
        tr = Transition()
        assert tr.phase == TransitionPhase.OUT
        assert tr.is_done is False
        assert tr.should_swap is False
        assert tr.progress == pytest.approx(0.0)

    def test_min_duration_clamped(self):
        tr = Transition(duration_out=0.0, duration_in=-1.0)
        assert tr.duration_out >= 0.01
        assert tr.duration_in >= 0.01

    def test_unknown_easing_falls_back(self):
        tr = Transition(easing="unknown_xyz")
        advance(tr, 0.1)
        assert 0.0 <= tr.progress <= 1.0

    def test_phase_flow(self):
        tr = Transition(duration_out=0.3, duration_in=0.3)
        run_to_swap(tr)
        assert tr.phase == TransitionPhase.SWAP
        assert tr.should_swap is True
        advance(tr, 0.001)
        assert tr.phase == TransitionPhase.IN
        assert tr.should_swap is False
        advance(tr, tr.duration_in + 0.01)
        assert tr.phase == TransitionPhase.DONE
        assert tr.is_done is True

    def test_done_does_not_change(self):
        tr = Transition(duration_out=0.2, duration_in=0.2)
        run_to_done(tr)
        progress = tr.progress
        advance(tr, 10.0)
        assert tr.phase == TransitionPhase.DONE
        assert tr.progress == progress

    def test_base_draw_no_error(self):
        Transition().draw(fake_screen())


class TestFadeTransition:
    def _make(self, **kwargs):
        return FadeTransition(duration_out=0.3, duration_in=0.3, **kwargs)

    def test_draw_out_blits_snapshot(self):
        tr = self._make()
        sc = fake_screen()
        tr.snapshot_out = _FakeSurface()
        advance(tr, 0.1)
        tr.draw(sc)
        sc.blit.assert_called()

    def test_draw_in_blits_snapshot(self):
        tr = self._make()
        sc = fake_screen()
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in = _FakeSurface()
        run_to_swap(tr)
        advance(tr, 0.1)
        tr.draw(sc)
        sc.blit.assert_called()

    def test_draw_done_no_blit(self):
        tr = self._make()
        sc = fake_screen()
        run_to_done(tr)
        tr.draw(sc)
        sc.blit.assert_not_called()

    def test_custom_color(self):
        assert FadeTransition(color=(255, 0, 128)).color == (255, 0, 128)


class TestSlideTransition:
    def _make(self, direction=SlideDirection.LEFT):
        return SlideTransition(direction=direction, duration_out=0.01, duration_in=0.3)

    def test_default_direction_left(self):
        assert SlideTransition().direction == SlideDirection.LEFT

    def test_draw_out_blits_snapshot_out(self):
        tr = self._make()
        sc = fake_screen()
        snap = _FakeSurface()
        tr.snapshot_out = snap
        advance(tr, 0.005)
        tr.draw(sc)
        sc.blit.assert_called_with(snap, (0, 0))

    def test_draw_in_blits_snapshot_in(self):
        tr = self._make()
        sc = fake_screen()
        snap_in = _FakeSurface()
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in = snap_in
        run_to_swap(tr)
        advance(tr, 0.1)
        tr.draw(sc)
        calls = [call.args[0] for call in sc.blit.call_args_list]
        assert snap_in in calls

    @pytest.mark.parametrize("direction", list(SlideDirection))
    def test_all_directions_no_error(self, direction):
        tr = self._make(direction)
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in = _FakeSurface()
        run_to_swap(tr)
        advance(tr, 0.1)
        tr.draw(fake_screen())


class TestWipeTransition:
    def _make(self, horizontal=True):
        return WipeTransition(horizontal=horizontal, duration_out=0.3, duration_in=0.3)

    def test_draw_out_calls_draw_rect(self):
        tr = self._make()
        tr.snapshot_out = _FakeSurface()
        advance(tr, 0.1)
        pygame.draw.rect.reset_mock()
        tr.draw(fake_screen())
        pygame.draw.rect.assert_called_once()

    def test_draw_in_calls_draw_rect(self):
        tr = self._make()
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in = _FakeSurface()
        run_to_swap(tr)
        advance(tr, 0.1)
        pygame.draw.rect.reset_mock()
        tr.draw(fake_screen())
        pygame.draw.rect.assert_called_once()

    @pytest.mark.parametrize("horizontal", [True, False])
    def test_draw_no_error(self, horizontal):
        tr = self._make(horizontal=horizontal)
        tr.snapshot_out = _FakeSurface()
        tr.snapshot_in = _FakeSurface()
        advance(tr, 0.1)
        tr.draw(fake_screen())
        run_to_done(tr)
        tr.draw(fake_screen())


class TestCrossfadeTransition:
    def _make(self):
        return CrossfadeTransition(duration=0.4)

    def test_duration_split_equally(self):
        tr = CrossfadeTransition(duration=0.6)
        assert tr.duration_out == pytest.approx(0.3)
        assert tr.duration_in == pytest.approx(0.3)

    def test_draw_out_with_real_surfaces(self):
        tr = self._make()
        tr.snapshot_out = real_surface()
        advance(tr, 0.1)
        tr.draw(real_surface())
        assert tr._alpha_surf is not None

    def test_draw_in_with_real_surfaces(self):
        tr = self._make()
        tr.snapshot_out = real_surface()
        tr.snapshot_in = real_surface()
        run_to_swap(tr)
        advance(tr, 0.1)
        tr.draw(real_surface())
        assert tr._alpha_surf is not None

    def test_draw_done_no_fake_blit(self):
        tr = self._make()
        sc = fake_screen()
        run_to_done(tr)
        tr.draw(sc)
        sc.blit.assert_not_called()
        sc.fill.assert_not_called()


class TestFullCycleIntegration:
    @pytest.mark.parametrize("cls,kwargs", [
        (FadeTransition, {"duration_out": 0.2, "duration_in": 0.2}),
        (SlideTransition, {"duration_out": 0.01, "duration_in": 0.2}),
        (WipeTransition, {"duration_out": 0.2, "duration_in": 0.2}),
        (CrossfadeTransition, {"duration": 0.4}),
    ])
    def test_full_cycle(self, cls, kwargs):
        tr = cls(**kwargs)
        assert tr.phase == TransitionPhase.OUT
        run_to_swap(tr)
        assert tr.phase == TransitionPhase.SWAP
        advance(tr, 0.001)
        assert tr.phase == TransitionPhase.IN
        advance(tr, tr.duration_in + 0.01)
        assert tr.phase == TransitionPhase.DONE
        assert tr.is_done

    @pytest.mark.parametrize("cls,kwargs", [
        (FadeTransition, {"duration_out": 0.2, "duration_in": 0.2}),
        (SlideTransition, {"duration_out": 0.01, "duration_in": 0.2}),
        (WipeTransition, {"duration_out": 0.2, "duration_in": 0.2}),
        (CrossfadeTransition, {"duration": 0.4}),
    ])
    def test_draw_no_error_in_all_phases(self, cls, kwargs):
        tr = cls(**kwargs)
        if isinstance(tr, CrossfadeTransition):
            sc = real_surface()
            snap = real_surface()
        else:
            sc = fake_screen()
            snap = _FakeSurface()
        tr.snapshot_out = snap
        tr.snapshot_in = snap
        advance(tr, 0.05)
        tr.draw(sc)
        run_to_swap(tr)
        tr.draw(sc)
        advance(tr, 0.001)
        tr.draw(sc)
        run_to_done(tr)
        tr.draw(sc)
