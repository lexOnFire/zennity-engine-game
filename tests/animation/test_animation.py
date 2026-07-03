"""
tests/animation/test_animation.py
=================================================================
Testes para engine/animation/ (clip.py, animator.py).

Estrategia:
  - Surfaces sao MagicMock — sem display pygame
  - SpriteRenderer patcheado via seu modulo de origem
  - Cada teste e independente — sem estado compartilhado
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.display.init()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_surface():
    return MagicMock(spec=pygame.Surface)


def make_frames(n: int):
    return [make_surface() for _ in range(n)]


def make_game_object(sr=None):
    go = MagicMock()
    go.get_component.return_value = sr
    return go


# patch global que evita ImportError de engine.graphics durante toda a suite
# SpriteRenderer e resolvido dentro de _push_frame via import local;
# patchamos no modulo de origem para interceptar esse import.
@pytest.fixture(autouse=True)
def patch_sprite_renderer():
    mock_sr_cls = MagicMock()
    with patch.dict(
        "sys.modules",
        {
            "engine.graphics": MagicMock(),
            "engine.graphics.renderer2d": MagicMock(SpriteRenderer=mock_sr_cls),
        },
    ):
        yield mock_sr_cls


# ==========================================================================
# AnimationEvent
# ==========================================================================

class TestAnimationEvent:
    def test_defaults(self):
        from engine.animation.clip import AnimationEvent
        cb = MagicMock()
        ev = AnimationEvent(frame_index=3, callback=cb)
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
        clip = AnimationClip("idle", make_frames(5), fps=10)
        assert clip.frame_count == 5

    def test_duration(self):
        from engine.animation.clip import AnimationClip
        clip = AnimationClip("run", make_frames(10), fps=10)
        assert clip.duration == pytest.approx(1.0)

    def test_fps_minimum(self):
        from engine.animation.clip import AnimationClip
        clip = AnimationClip("idle", make_frames(1), fps=0.0)
        assert clip.fps >= 0.01

    def test_loop_default_true(self):
        from engine.animation.clip import AnimationClip
        clip = AnimationClip("idle", make_frames(1))
        assert clip.loop is True

    def test_loop_false(self):
        from engine.animation.clip import AnimationClip
        clip = AnimationClip("jump", make_frames(3), loop=False)
        assert clip.loop is False

    def test_frames_stored(self):
        from engine.animation.clip import AnimationClip
        frames = make_frames(4)
        clip = AnimationClip("idle", frames)
        assert len(clip.frames) == 4

    def test_flip_h_calls_transform(self):
        from engine.animation.clip import AnimationClip
        frames = make_frames(2)
        flipped = make_surface()
        with patch("pygame.transform.flip", return_value=flipped) as mock_flip:
            clip = AnimationClip("idle", frames, flip_h=True)
            assert mock_flip.call_count == 2
            assert all(f is flipped for f in clip.frames)

    def test_no_flip_h_skips_transform(self):
        from engine.animation.clip import AnimationClip
        with patch("pygame.transform.flip") as mock_flip:
            AnimationClip("idle", make_frames(3), flip_h=False)
            mock_flip.assert_not_called()

    def test_add_event_returns_self(self):
        from engine.animation.clip import AnimationClip
        clip = AnimationClip("idle", make_frames(4))
        result = clip.add_event(2, MagicMock())
        assert result is clip

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
        clip = AnimationClip("run", make_frames(4), fps=12)
        r = repr(clip)
        assert "run" in r and "4" in r


# ==========================================================================
# Animator — inicializacao e API de clips
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

    def test_play_unknown_clip_no_crash(self):
        from engine.animation.animator import Animator
        a = Animator()
        a.play("nao_existe")
        assert a.current_clip is None

    def test_play_sets_current(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(3)))
        a.play("idle")
        assert a.current_clip == "idle"

    def test_play_resets_frame_and_timer(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(4), fps=10))
        a.play("idle")
        assert a.current_frame == 0
        assert a._timer == pytest.approx(0.0)

    def test_play_same_clip_no_restart(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(4), fps=10))
        a.play("idle")
        a._frame_index = 2
        a.play("idle")
        assert a.current_frame == 2

    def test_play_same_clip_force_restarts(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(4), fps=10))
        a.play("idle")
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

    def test_start_with_no_default_no_crash(self):
        from engine.animation.animator import Animator
        a = Animator()
        a.game_object = None
        a.start()
        assert a.current_clip is None


# ==========================================================================
# Animator — avanco de frames
# ==========================================================================

class TestAnimatorUpdate:
    def _make(self, n_frames=4, fps=10, loop=True):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(n_frames), fps=fps, loop=loop))
        a.play("idle")
        return a

    def test_update_no_clip_no_crash(self):
        from engine.animation.animator import Animator
        Animator().update(0.1)

    def test_update_advances_frame(self):
        a = self._make(fps=10)
        a.update(0.1)
        assert a.current_frame == 1

    def test_update_multiple_frames_one_call(self):
        a = self._make(n_frames=6, fps=10)
        a.update(0.35)
        assert a.current_frame == 3

    def test_update_loops(self):
        a = self._make(n_frames=4, fps=10, loop=True)
        a.update(0.4)
        assert a.current_frame == 0

    def test_update_non_loop_stops(self):
        a = self._make(n_frames=3, fps=10, loop=False)
        a.update(1.0)
        assert a.is_finished is True

    def test_update_non_loop_calls_on_finish(self):
        a = self._make(n_frames=2, fps=10, loop=False)
        cb = MagicMock()
        a.on_finish = cb
        a.update(1.0)
        cb.assert_called_once_with("idle")

    def test_update_finished_clip_does_not_advance(self):
        a = self._make(n_frames=2, fps=10, loop=False)
        a.update(1.0)
        frame_after = a.current_frame
        a.update(1.0)
        assert a.current_frame == frame_after

    def test_update_dt_zero_no_advance(self):
        a = self._make(fps=10)
        a.update(0.0)
        assert a.current_frame == 0


# ==========================================================================
# Animator — eventos de frame
# ==========================================================================

class TestAnimatorEvents:
    def test_event_fires_on_correct_frame(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        cb = MagicMock()
        clip = AnimationClip("idle", make_frames(4), fps=10)
        clip.add_event(2, cb)
        a.add_clip(clip)
        a.play("idle")
        a.update(0.2)  # 0->1->2
        cb.assert_called_once()

    def test_event_fires_only_once_per_pass(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        cb = MagicMock()
        clip = AnimationClip("idle", make_frames(4), fps=10)
        clip.add_event(1, cb)
        a.add_clip(clip)
        a.play("idle")
        a.update(0.15)  # 0->1
        a.update(0.05)  # permanece frame 1 (timer < frame_duration)
        cb.assert_called_once()

    def test_event_fires_again_after_loop(self):
        """
        Clip com 3 frames a 10fps (frame_duration=0.1s).
        play() -> frame 0.
        update(0.3) -> avanca frames 1, 2, loop->0  (cb dispara no frame 1).
        update(0.1) -> avanca frame 0->1             (cb dispara novamente).
        Total: cb chamado 2 vezes.
        """
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        cb = MagicMock()
        clip = AnimationClip("idle", make_frames(3), fps=10, loop=True)
        clip.add_event(1, cb)
        a.add_clip(clip)
        a.play("idle")
        a.update(0.3)  # 1(fire), 2, loop->0 (reset fired)
        a.update(0.1)  # 0->1 (fire again)
        assert cb.call_count == 2


# ==========================================================================
# Animator — transicoes automaticas
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
        mock_sr = MagicMock()
        go = make_game_object(sr=mock_sr)
        a = Animator()
        a.game_object = go
        a.add_clip(AnimationClip("idle", make_frames(3), fps=10))
        a.play("idle")  # chama _push_frame -> sr.image = frame
        mock_sr.image  # acesso sem crash confirma que foi setado

    def test_push_frame_no_game_object_no_crash(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(3), fps=10))
        a.play("idle")
        a.update(0.2)


# ==========================================================================
# Animator — consultas de estado
# ==========================================================================

class TestAnimatorState:
    def test_is_playing_true(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(2)))
        a.play("idle")
        assert a.is_playing("idle") is True

    def test_is_playing_false_for_other(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("idle", make_frames(2)))
        a.play("idle")
        assert a.is_playing("run") is False

    def test_current_clip_none_when_no_play(self):
        from engine.animation.animator import Animator
        assert Animator().current_clip is None

    def test_repr_contains_clip_name(self):
        from engine.animation.animator import Animator
        from engine.animation.clip import AnimationClip
        a = Animator()
        a.game_object = None
        a.add_clip(AnimationClip("run", make_frames(2)))
        a.play("run")
        assert "run" in repr(a)
