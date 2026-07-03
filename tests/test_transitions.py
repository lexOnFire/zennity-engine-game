"""
tests/test_transitions.py
=================================================================
Testes para engine/transitions.py - sem display pygame.
Cobre: easing, Transition base, FadeTransition,
       SlideTransition, WipeTransition, CrossfadeTransition.
"""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.display.init()


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def make_surface(w: int = 100, h: int = 80) -> pygame.Surface:
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((30, 60, 200, 255))
    return s


def make_screen(w: int = 100, h: int = 80) -> pygame.Surface:
    s = pygame.Surface((w, h))
    s.fill((10, 10, 10))
    return s


def run_to_swap(transition) -> None:
    from engine.transitions import TransitionPhase
    while transition.phase not in (TransitionPhase.SWAP, TransitionPhase.DONE):
        transition.update(0.016)


def run_to_done(transition) -> None:
    for _ in range(5000):
        transition.update(0.016)
        if transition.is_done:
            break


# ==========================================================================
# Easing
# ==========================================================================

class TestEasing:
    @pytest.mark.parametrize("name", ["linear", "ease_in", "ease_out", "ease_in_out"])
    def test_zero_returns_zero(self, name):
        from engine.transitions import EASING
        assert EASING[name](0.0) == pytest.approx(0.0)

    @pytest.mark.parametrize("name", ["linear", "ease_in", "ease_out", "ease_in_out"])
    def test_one_returns_one(self, name):
        from engine.transitions import EASING
        assert EASING[name](1.0) == pytest.approx(1.0)

    @pytest.mark.parametrize("name", ["linear", "ease_in", "ease_out", "ease_in_out"])
    def test_midpoint_in_range(self, name):
        from engine.transitions import EASING
        val = EASING[name](0.5)
        assert 0.0 <= val <= 1.0

    def test_ease_in_slower_than_linear_at_midpoint(self):
        from engine.transitions import EASING
        assert EASING["ease_in"](0.5) < EASING["linear"](0.5)

    def test_ease_out_faster_than_linear_at_midpoint(self):
        from engine.transitions import EASING
        assert EASING["ease_out"](0.5) > EASING["linear"](0.5)

    def test_ease_in_out_symmetric(self):
        from engine.transitions import EASING
        assert EASING["ease_in_out"](0.5) == pytest.approx(0.5)

    def test_unknown_easing_falls_back_to_ease_in_out(self):
        from engine.transitions import Transition, _ease_in_out
        t = Transition(easing="nonexistent")
        assert t._ease(0.5) == pytest.approx(_ease_in_out(0.5))


# ==========================================================================
# Transition (base)
# ==========================================================================

class TestTransitionBase:
    def test_initial_phase_is_out(self):
        from engine.transitions import Transition, TransitionPhase
        assert Transition().phase == TransitionPhase.OUT

    def test_initial_progress_is_zero(self):
        from engine.transitions import Transition
        assert Transition().progress == pytest.approx(0.0)

    def test_is_done_false_initially(self):
        from engine.transitions import Transition
        assert not Transition().is_done

    def test_should_swap_false_initially(self):
        from engine.transitions import Transition
        assert not Transition().should_swap

    def test_duration_minimum_clamped(self):
        from engine.transitions import Transition
        t = Transition(duration_out=-5.0, duration_in=0.0)
        assert t.duration_out >= 0.01
        assert t.duration_in  >= 0.01

    def test_update_advances_progress(self):
        from engine.transitions import Transition
        t = Transition(duration_out=1.0, duration_in=1.0, easing="linear")
        t.update(0.5)
        assert t.progress == pytest.approx(0.5)

    def test_progress_capped_at_one(self):
        from engine.transitions import Transition
        t = Transition(duration_out=0.1, duration_in=0.1, easing="linear")
        t.update(9999.0)
        assert t.progress == pytest.approx(1.0)

    def test_out_phase_transitions_to_swap(self):
        from engine.transitions import Transition, TransitionPhase
        t = Transition(duration_out=0.1, duration_in=0.5, easing="linear")
        t.update(0.2)
        assert t.phase == TransitionPhase.SWAP

    def test_swap_phase_transitions_to_in_next_update(self):
        from engine.transitions import Transition, TransitionPhase
        t = Transition(duration_out=0.01, duration_in=0.5, easing="linear")
        run_to_swap(t)
        assert t.phase == TransitionPhase.SWAP
        t.update(0.001)
        assert t.phase == TransitionPhase.IN

    def test_should_swap_true_in_swap_phase(self):
        from engine.transitions import Transition
        t = Transition(duration_out=0.01, duration_in=0.5, easing="linear")
        run_to_swap(t)
        assert t.should_swap

    def test_in_phase_progresses_to_done(self):
        from engine.transitions import Transition, TransitionPhase
        t = Transition(duration_out=0.01, duration_in=0.01, easing="linear")
        run_to_done(t)
        assert t.phase == TransitionPhase.DONE
        assert t.is_done

    def test_update_after_done_is_noop(self):
        from engine.transitions import Transition
        t = Transition(duration_out=0.01, duration_in=0.01, easing="linear")
        run_to_done(t)
        p = t.progress
        t.update(99.9)
        assert t.progress == p

    def test_in_phase_progress_restarts_from_zero(self):
        from engine.transitions import Transition, TransitionPhase
        t = Transition(duration_out=0.01, duration_in=1.0, easing="linear")
        run_to_swap(t)
        t.update(0.001)
        assert t.phase == TransitionPhase.IN
        assert t.progress < 0.1

    def test_draw_base_does_nothing(self):
        from engine.transitions import Transition
        Transition().draw(make_screen())


# ==========================================================================
# FadeTransition
# ==========================================================================

class TestFadeTransition:
    def test_default_color_is_black(self):
        from engine.transitions import FadeTransition
        assert FadeTransition().color == (0, 0, 0)

    def test_custom_color_stored(self):
        from engine.transitions import FadeTransition
        assert FadeTransition(color=(255, 0, 128)).color == (255, 0, 128)

    def test_draw_out_without_snapshot_no_crash(self):
        from engine.transitions import FadeTransition
        t = FadeTransition(duration_out=0.5)
        t.update(0.1)
        t.draw(make_screen())

    def test_draw_out_with_snapshot_blits_overlay(self):
        from engine.transitions import FadeTransition, TransitionPhase
        t = FadeTransition(duration_out=0.5, duration_in=0.5, easing="linear")
        t.snapshot_out = make_surface()
        t.update(0.25)
        assert t.phase == TransitionPhase.OUT
        t.draw(make_screen())

    def test_draw_in_with_snapshot_no_crash(self):
        from engine.transitions import FadeTransition
        t = FadeTransition(duration_out=0.01, duration_in=0.5, easing="linear")
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        run_to_swap(t)
        t.update(0.01)
        t.draw(make_screen())

    def test_draw_done_is_noop(self):
        from engine.transitions import FadeTransition
        t = FadeTransition(duration_out=0.01, duration_in=0.01)
        run_to_done(t)
        screen = make_screen()
        before = pygame.surfarray.array3d(screen).tolist()
        t.draw(screen)
        assert pygame.surfarray.array3d(screen).tolist() == before

    def test_full_lifecycle_no_exception(self):
        from engine.transitions import FadeTransition
        t = FadeTransition(color=(128, 0, 64), duration_out=0.1, duration_in=0.1)
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        screen = make_screen()
        for _ in range(200):
            t.update(0.002)
            t.draw(screen)
            if t.is_done:
                break
        assert t.is_done


# ==========================================================================
# SlideTransition
# ==========================================================================

class TestSlideTransition:
    @pytest.mark.parametrize("direction_name", ["LEFT", "RIGHT", "UP", "DOWN"])
    def test_all_directions_no_crash(self, direction_name):
        from engine.transitions import SlideTransition, SlideDirection
        t = SlideTransition(direction=SlideDirection[direction_name],
                            duration_out=0.01, duration_in=0.3)
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        screen = make_screen()
        for _ in range(300):
            t.update(0.002)
            t.draw(screen)
            if t.is_done:
                break
        assert t.is_done

    def test_draws_snapshot_out_during_out_phase(self):
        from engine.transitions import SlideTransition, TransitionPhase
        t = SlideTransition(duration_out=1.0, duration_in=0.3, easing="linear")
        t.snapshot_out = make_surface()
        t.update(0.1)
        assert t.phase == TransitionPhase.OUT
        t.draw(make_screen())

    def test_slide_left_in_phase_entered(self):
        from engine.transitions import SlideTransition, SlideDirection, TransitionPhase
        t = SlideTransition(direction=SlideDirection.LEFT,
                            duration_out=0.01, duration_in=1.0, easing="linear")
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        run_to_swap(t)
        t.update(0.001)
        assert t.phase == TransitionPhase.IN

    def test_default_direction_is_left(self):
        from engine.transitions import SlideTransition, SlideDirection
        assert SlideTransition().direction == SlideDirection.LEFT

    def test_draw_without_snapshots_no_crash(self):
        from engine.transitions import SlideTransition
        t = SlideTransition(duration_out=0.01, duration_in=0.3)
        run_to_swap(t)
        t.update(0.01)
        t.draw(make_screen())


# ==========================================================================
# WipeTransition
# ==========================================================================

class TestWipeTransition:
    def test_horizontal_wipe_full_lifecycle(self):
        from engine.transitions import WipeTransition
        t = WipeTransition(horizontal=True, duration_out=0.1, duration_in=0.1)
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        run_to_done(t)
        assert t.is_done

    def test_vertical_wipe_full_lifecycle(self):
        from engine.transitions import WipeTransition
        t = WipeTransition(horizontal=False, duration_out=0.1, duration_in=0.1)
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        screen = make_screen()
        for _ in range(300):
            t.update(0.002)
            t.draw(screen)
            if t.is_done:
                break
        assert t.is_done

    def test_draw_out_phase_draws_black_rect(self):
        from engine.transitions import WipeTransition, TransitionPhase
        t = WipeTransition(horizontal=True, duration_out=1.0, duration_in=0.1, easing="linear")
        t.snapshot_out = make_surface(100, 80)
        screen = make_screen(100, 80)
        t.update(0.5)
        assert t.phase == TransitionPhase.OUT
        t.draw(screen)
        assert screen.get_at((0, 0))[:3] == (0, 0, 0)

    def test_draw_done_is_noop(self):
        from engine.transitions import WipeTransition
        t = WipeTransition(duration_out=0.01, duration_in=0.01)
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        run_to_done(t)
        screen = make_screen()
        before = pygame.surfarray.array3d(screen).tolist()
        t.draw(screen)
        assert pygame.surfarray.array3d(screen).tolist() == before

    def test_default_is_horizontal(self):
        from engine.transitions import WipeTransition
        assert WipeTransition().horizontal is True


# ==========================================================================
# CrossfadeTransition
# ==========================================================================

class TestCrossfadeTransition:
    def test_duration_split_equally(self):
        from engine.transitions import CrossfadeTransition
        t = CrossfadeTransition(duration=1.0)
        assert t.duration_out == pytest.approx(0.5)
        assert t.duration_in  == pytest.approx(0.5)

    def test_full_crossfade_no_crash(self):
        from engine.transitions import CrossfadeTransition
        t = CrossfadeTransition(duration=0.2)
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        screen = make_screen()
        for _ in range(500):
            t.update(0.001)
            t.draw(screen)
            if t.is_done:
                break
        assert t.is_done

    def test_draw_out_phase_no_crash_without_snapshots(self):
        from engine.transitions import CrossfadeTransition
        t = CrossfadeTransition(duration=1.0)
        t.update(0.1)
        t.draw(make_screen())

    def test_draw_in_phase_with_snapshot_no_crash(self):
        from engine.transitions import CrossfadeTransition
        t = CrossfadeTransition(duration=0.04)
        t.snapshot_out = make_surface()
        t.snapshot_in  = make_surface()
        run_to_swap(t)
        t.update(0.002)
        t.draw(make_screen())

    def test_alpha_surf_recreated_on_resize(self):
        from engine.transitions import CrossfadeTransition
        t = CrossfadeTransition(duration=1.0)
        t.snapshot_out = make_surface(50, 50)
        t.snapshot_in  = make_surface(200, 150)
        t.update(0.1)
        t.draw(make_screen(50, 50))
        t.draw(make_screen(200, 150))

    def test_draw_done_is_noop(self):
        from engine.transitions import CrossfadeTransition
        t = CrossfadeTransition(duration=0.02)
        run_to_done(t)
        screen = make_screen()
        before = pygame.surfarray.array3d(screen).tolist()
        t.draw(screen)
        assert pygame.surfarray.array3d(screen).tolist() == before


# ==========================================================================
# SlideDirection enum
# ==========================================================================

class TestSlideDirection:
    def test_all_four_directions_exist(self):
        from engine.transitions import SlideDirection
        assert {d.name for d in SlideDirection} == {"LEFT", "RIGHT", "UP", "DOWN"}
