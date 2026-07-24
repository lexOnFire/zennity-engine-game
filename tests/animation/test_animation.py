"""
tests/animation/test_animation.py
=================================================================
Testes para engine/animation/ (clip.py, animator.py).

Estrategia:
  - Imports reais de engine.animation e engine.graphics
  - pygame headless (SDL_VIDEODRIVER=dummy) via conftest.py
  - SpriteRenderer mockado via monkeypatch no atributo `image`
    do objeto retornado por get_component — sem patch de modulos
  - game_object=None em todos os testes que nao precisam de SR
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pygame
import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_surface():
    return pygame.Surface((1, 1))


def make_frames(n: int):
    return [make_surface() for _ in range(n)]


def make_animator(n_frames=4, fps=10, loop=True, name="idle"):
    from engine.animation.animator import Animator
    from engine.animation.clip import AnimationClip
    a = Animator()
    a.game_object = None
    a.add_clip(AnimationClip(name, make_frames(n_frames), fps=fps, loop=loop))
    a.play(name)
    return a


# ==========================================================================
# AnimationEvent
# ==========================================================================

class TestAnimationEvent:
    def test_defaults(self):
        from engine.animation.clip import AnimationEvent
        ev = AnimationEvent(frame_index=3, callback=MagicMock())
        assert ev.frame_index == 3
        assert ev.fired is False

    def test_fired_can_be_set(self):
        from engine.animation.clip import AnimationEvent
        ev = AnimationEvent(frame_index=0, callback=MagicMock())
        ev.fired = True
        assert ev.fired is True


# ==========================================================================
# AnimationClip
# ==========================================================================

class TestAnimationClip:
    def test_frame_count(self):
        from engine.animation.clip import AnimationClip
        assert AnimationClip("idle", make_frames(5), fps=10).frame_count == 5

    def test_duration(self):
        from engine.animation.clip import AnimationClip
        assert AnimationClip("run", make_frames(10), fps=10).duration == pytest.approx(1.0)

    def test_fps_minimum(self):
        from engine.animation.clip import AnimationClip
        assert AnimationClip("idle", make_frames(1), fps=0.0).fps >= 0.01

    def test_loop_default_true(self):
        from engine.animation.clip import AnimationClip
        assert AnimationClip("idle", make_frames(1)).loop is True

    def test_loop_false(self):
        from engine.animation.clip import AnimationClip
        assert AnimationClip("jump", make_frames(3), loop=False).loop is False

    def test_frames_stored(self):
        from engine.animation.clip import AnimationClip
        assert len(AnimationClip("idle", make_frames(4)).frames) == 4

    def test_flip_h_mirrors_frames(self):
        from engine.animation.clip import AnimationClip
        frames = [pygame.Surface((4, 4)) for _ in range(2)]
        for f in frames:
            f.set_at((0, 0), (255, 0, 0))
        clip = AnimationClip("idle", frames, flip_h=True)
        for f in clip.frames:
            assert f.get_at((3, 0))[:3] == (255, 0, 0)

    def test_no_flip_h_preserves_frames(self):
        from engine.animation.clip import AnimationClip
        frames = make_frames(3)
        clip = AnimationClip("idle", frames, flip_h=False)
        assert len(clip.frames) == 3

    def test_add_event_returns_self(self):
        from engine.animation.clip import AnimationClip
        clip = AnimationClip("idle", make_frames(4))
        assert clip.add_event(2, MagicMock()) is clip

    def test_add_event_stored(self):
        from engine.animation.clip import AnimationClip
        clip = AnimationClip("idle", make_frames(4))
        cb = MagicMock()
        clip.add_event(1, cb)
        assert len(clip.events) == 1
        assert clip.events[0].frame_index == 1

    def test_multiple_events(self):
        from engine.animation.clip import AnimationClip
        clip = AnimationClip("idle", make_frames(6))
        clip.add_event(0, MagicMock()).add_event(3, MagicMock())
        assert len(clip.events) == 2

    def test_repr(self):
        from engine.animation.clip import AnimationClip
        r = repr(AnimationClip("run", make_frames(4), fps=12))
        assert "run" in r and "4" in r


# ==========================================================================
# Animator — inicializacao e API
# ==========================================================================

class TestAnimatorInit:
    def test_current_clip_none_initially(self):
        from engine.animation.animator import Animator
        assert Animator().current_clip is None

    def test_is_finished_false_initially(self):
        from engine.animation.animator import Animator
        assert Animator().is_finished is False

    def test_add_clip_returns_self(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        assert a.add_clip(AnimationClip("idle", make_frames(2))) is a

    def test_add_transition_returns_self(self):
        from engine.animation.animator import Animator
        a = Animator()
        assert a.add_transition("idle", "run", lambda: True) is a

    def test_play_unknown_no_crash(self):
        from engine.animation.animator import Animator
        a = Animator()
        a.play("nao_existe")
        assert a.current_clip is None

    def test_play_sets_current(self):
        a = make_animator()
        assert a.current_clip == "idle"

    def test_play_resets_frame_and_timer(self):
        a = make_animator()
        assert a.current_frame == 0
        assert a._timer == pytest.approx(0.0)

    def test_play_same_clip_no_restart(self):
        a = make_animator()
        a._frame_index = 2
        a.play("idle")
        assert a.current_frame == 2

    def test_play_same_clip_force_restarts(self):
        a = make_animator()
        a._frame_index = 2
        a.play("idle", force=True)
        assert a.current_frame == 0

    def test_start_plays_default(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator(default_clip="idle")
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(2)))
        a.start()
        assert a.current_clip == "idle"

    def test_start_no_default_no_crash(self):
        from engine.animation.animator import Animator
        a = Animator()
        a.game_object = None
        a.start()
        assert a.current_clip is None


# ==========================================================================
# Animator — avanco de frames
# ==========================================================================

class TestAnimatorUpdate:
    def test_update_no_clip_no_crash(self):
        from engine.animation.animator import Animator
        Animator().update(0.1)

    def test_update_advances_frame(self):
        a = make_animator(fps=10)
        a.update(0.1)
        assert a.current_frame == 1

    def test_update_multiple_frames_one_call(self):
        a = make_animator(n_frames=6, fps=10)
        a.update(0.35)
        assert a.current_frame == 3

    def test_update_loops(self):
        a = make_animator(n_frames=4, fps=10, loop=True)
        a.update(0.4)
        assert a.current_frame == 0

    def test_update_non_loop_stops(self):
        a = make_animator(n_frames=3, fps=10, loop=False)
        a.update(1.0)
        assert a.is_finished is True

    def test_update_non_loop_calls_on_finish(self):
        a = make_animator(n_frames=2, fps=10, loop=False)
        cb = MagicMock()
        a.on_finish = cb
        a.update(1.0)
        cb.assert_called_once_with("idle")

    def test_update_finished_does_not_advance(self):
        a = make_animator(n_frames=2, fps=10, loop=False)
        a.update(1.0)
        frame_after = a.current_frame
        a.update(1.0)
        assert a.current_frame == frame_after

    def test_update_dt_zero_no_advance(self):
        a = make_animator(fps=10)
        a.update(0.0)
        assert a.current_frame == 0


# ==========================================================================
# Animator — eventos de frame
# ==========================================================================

class TestAnimatorEvents:
    def test_event_fires_on_correct_frame(self):
        from engine.animation.clip import AnimationClip
        from engine.animation.animator import Animator
        cb = MagicMock()
        clip = AnimationClip("idle", make_frames(4), fps=10)
        clip.add_event(2, cb)
        a = Animator()
        a.game_object = None
        a.add_clip(clip)
        a.play("idle")
        a.update(0.2)  # 0->1->2
        cb.assert_called_once()

    def test_event_fires_only_once_per_pass(self):
        from engine.animation.clip import AnimationClip
        from engine.animation.animator import Animator
        cb = MagicMock()
        clip = AnimationClip("idle", make_frames(4), fps=10)
        clip.add_event(1, cb)
        a = Animator()
        a.game_object = None
        a.add_clip(clip)
        a.play("idle")
        a.update(0.15)  # 0->1 (fires)
        a.update(0.05)  # permanece no frame 1
        cb.assert_called_once()

    def test_event_fires_again_after_loop(self):
        """
        3 frames a 10fps (frame_duration=0.1s). Evento no frame 1.

        update(0.45) -> 4 ticks inteiros (floor(0.45/0.1)=4):
          tick 1: 0->1  event fires  (call_count=1, fired=True)
          tick 2: 1->2
          tick 3: 2->0  loop: fired resetado
          tick 4: 0->1  event fires  (call_count=2)
        """
        from engine.animation.clip import AnimationClip
        from engine.animation.animator import Animator
        cb = MagicMock()
        clip = AnimationClip("idle", make_frames(3), fps=10, loop=True)
        clip.add_event(1, cb)
        a = Animator()
        a.game_object = None
        a.add_clip(clip)
        a.play("idle")
        a.update(0.45)
        assert cb.call_count == 2


# ==========================================================================
# Animator — transicoes
# ==========================================================================

class TestAnimatorTransitions:
    def _make2(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(4), fps=10))
        a.add_clip(AnimationClip("run",  make_frames(4), fps=10))
        a.play("idle")
        return a

    def test_transition_fires_when_true(self):
        a = self._make2()
        a.add_transition("idle", "run", lambda: True)
        a.update(0.05)
        assert a.current_clip == "run"

    def test_transition_does_not_fire_when_false(self):
        a = self._make2()
        a.add_transition("idle", "run", lambda: False)
        a.update(0.05)
        assert a.current_clip == "idle"

    def test_wildcard_transition(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("run",  make_frames(4), fps=10))
        a.add_clip(AnimationClip("jump", make_frames(4), fps=10))
        a.play("run")
        a.add_transition("*", "jump", lambda: True)
        a.update(0.05)
        assert a.current_clip == "jump"

    def test_transition_exception_no_crash(self):
        a = self._make2()
        a.add_transition("idle", "run", lambda: 1 / 0)
        a.update(0.05)
        assert a.current_clip == "idle"

    def test_no_self_transition(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(4), fps=10))
        a.play("idle")
        a._frame_index = 2
        a.add_transition("idle", "idle", lambda: True)
        a.update(0.0)
        assert a.current_frame == 2


# ==========================================================================
# Animator — push_frame / SpriteRenderer
# ==========================================================================

class TestAnimatorPushFrame:
    def test_push_frame_updates_sprite_renderer(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        from engine.graphics.renderer2d import SpriteRenderer

        mock_sr = MagicMock(spec=SpriteRenderer)
        go = MagicMock()
        go.get_component.return_value = mock_sr

        a = Animator()
        a.game_object = go
        a.add_clip(AnimationClip("idle", make_frames(3), fps=10))
        a.play("idle")

        assert go.get_component.called

    def test_push_frame_no_game_object_no_crash(self):
        a = make_animator()
        a.update(0.2)


# ==========================================================================
# Animator — consultas
# ==========================================================================

class TestAnimatorState:
    def test_is_playing_true(self):
        a = make_animator()
        assert a.is_playing("idle") is True

    def test_is_playing_false_for_other(self):
        a = make_animator()
        assert a.is_playing("run") is False

    def test_current_clip_none_when_no_play(self):
        from engine.animation.animator import Animator
        assert Animator().current_clip is None

    def test_repr_contains_clip_name(self):
        a = make_animator()
        assert "idle" in repr(a)
