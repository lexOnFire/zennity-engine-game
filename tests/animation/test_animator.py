"""
tests/animation/test_animator.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/animation/animator.py.

Estratégia de isolamento:
  - pygame stubado via sys.modules (somente import guard).
  - AnimationClip é instanciado diretamente com frames fictícios
    (objetos opacos / MagicMock); não depende de Surface real.
  - SpriteRenderer é interceptado via patch em
    engine.graphics.renderer2d para verificar que `image` é
    atualizado sem import do módulo real.
  - game_object é MagicMock com get_component controlado.
  - Eventos (AnimationEvent) são criados diretamente.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────
if "pygame" not in sys.modules:
    _pg = ModuleType("pygame")
    sys.modules["pygame"] = _pg

# stub engine.graphics.renderer2d para evitar import circular
if "engine.graphics.renderer2d" not in sys.modules:
    _r2d = ModuleType("engine.graphics.renderer2d")
    class _FakeSR:
        image = None
    _r2d.SpriteRenderer = _FakeSR
    sys.modules["engine.graphics.renderer2d"] = _r2d

from engine.animation.clip import AnimationClip, AnimationEvent  # noqa: E402
from engine.animation.animator import Animator                    # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────

def _frames(n=4):
    """Cria n frames opacos (MagicMock) para uso em clips."""
    return [MagicMock(name=f"frame{i}") for i in range(n)]


def _clip(name="idle", n=4, fps=8, loop=True, events=None):
    return AnimationClip(name=name, frames=_frames(n), fps=fps,
                         loop=loop, events=events or [])


def _animator_with_go(clips=None, default=None):
    """Cria Animator com game_object + SpriteRenderer mockado."""
    anim = Animator(default_clip=default)
    for c in (clips or []):
        anim.add_clip(c)

    sr = MagicMock()
    sr.image = None

    go = MagicMock()
    go.get_component = MagicMock(return_value=sr)
    anim.game_object = go
    anim._sr = sr  # atalho para asserts
    return anim


def _animator(clips=None, default=None):
    anim = Animator(default_clip=default)
    for c in (clips or []):
        anim.add_clip(c)
    anim.game_object = None
    return anim


# ── TestInit ────────────────────────────────────────────────────────────────
class TestInit:
    def test_no_clips_on_init(self):
        assert Animator()._clips == {}

    def test_no_current_on_init(self):
        assert Animator()._current is None

    def test_frame_index_zero(self):
        assert Animator()._frame_index == 0

    def test_timer_zero(self):
        assert Animator()._timer == pytest.approx(0.0)

    def test_finished_false(self):
        assert Animator()._finished is False

    def test_on_finish_none(self):
        assert Animator().on_finish is None

    def test_default_clip_stored(self):
        assert Animator(default_clip="idle")._default == "idle"


# ── TestAddClip ────────────────────────────────────────────────────────────
class TestAddClip:
    def test_add_clip_registers(self):
        anim = _animator()
        c = _clip("idle")
        anim.add_clip(c)
        assert "idle" in anim._clips

    def test_add_clip_returns_self(self):
        anim = _animator()
        assert anim.add_clip(_clip()) is anim

    def test_add_multiple_clips(self):
        anim = _animator()
        anim.add_clip(_clip("idle"))
        anim.add_clip(_clip("run"))
        assert len(anim._clips) == 2

    def test_add_clip_overwrites_same_name(self):
        anim = _animator()
        c1 = _clip("idle", n=2)
        c2 = _clip("idle", n=6)
        anim.add_clip(c1)
        anim.add_clip(c2)
        assert anim._clips["idle"].frame_count == 6


# ── TestPlay ────────────────────────────────────────────────────────────────
class TestPlay:
    def test_play_sets_current(self):
        anim = _animator([_clip("idle")])
        anim.play("idle")
        assert anim.current_clip == "idle"

    def test_play_resets_frame_index(self):
        anim = _animator([_clip("idle")])
        anim._frame_index = 3
        anim.play("idle")
        assert anim._frame_index == 0

    def test_play_resets_timer(self):
        anim = _animator([_clip("idle")])
        anim._timer = 5.0
        anim.play("idle")
        assert anim._timer == pytest.approx(0.0)

    def test_play_clears_finished(self):
        anim = _animator([_clip("idle")])
        anim._finished = True
        anim.play("idle")
        assert anim._finished is False

    def test_play_unknown_clip_no_crash(self):
        anim = _animator()
        anim.play("nonexistent")  # não deve lançar
        assert anim._current is None

    def test_play_same_clip_no_restart_without_force(self):
        anim = _animator([_clip("idle")])
        anim.play("idle")
        anim._frame_index = 3
        anim.play("idle", force=False)
        assert anim._frame_index == 3  # não reiniciou

    def test_play_force_restarts(self):
        anim = _animator([_clip("idle")])
        anim.play("idle")
        anim._frame_index = 3
        anim.play("idle", force=True)
        assert anim._frame_index == 0

    def test_play_transition_between_clips(self):
        anim = _animator([_clip("idle"), _clip("run")])
        anim.play("idle")
        anim.play("run")
        assert anim.current_clip == "run"


# ── TestStart ────────────────────────────────────────────────────────────────
class TestStart:
    def test_start_plays_default_clip(self):
        anim = _animator([_clip("idle")], default="idle")
        anim.start()
        assert anim.current_clip == "idle"

    def test_start_no_default_no_crash(self):
        anim = _animator([_clip("idle")])
        anim.start()  # default=None

    def test_start_unknown_default_no_crash(self):
        anim = _animator([], default="missing")
        anim.start()
        assert anim.current_clip is None


# ── TestUpdateFrameAdvance ──────────────────────────────────────────────────────
class TestUpdateFrameAdvance:
    def test_update_no_clip_no_crash(self):
        anim = _animator()
        anim.update(0.1)  # nenhum clip

    def test_update_advances_frame_after_duration(self):
        """fps=8 → frame_duration=0.125s. dt=0.13 → avança 1 frame."""
        anim = _animator([_clip(fps=8)])
        anim.play("idle")
        anim.update(0.13)
        assert anim.current_frame == 1

    def test_update_no_advance_before_duration(self):
        anim = _animator([_clip(fps=8)])
        anim.play("idle")
        anim.update(0.05)
        assert anim.current_frame == 0

    def test_update_multiple_frames_large_dt(self):
        """dt=0.5s, fps=8 → 4 frames (0.5 / 0.125)."""
        anim = _animator([_clip(fps=8, n=8)])
        anim.play("idle")
        anim.update(0.5)
        assert anim.current_frame == 4

    def test_update_loops_back_to_zero(self):
        """4 frames, fps=8; dt=0.5s → 4 frames avançados → loop para frame 0."""
        anim = _animator([_clip(fps=8, n=4, loop=True)])
        anim.play("idle")
        anim.update(0.5)
        assert anim.current_frame == 0

    def test_update_stops_at_last_frame_nonloop(self):
        anim = _animator([_clip(fps=8, n=4, loop=False)])
        anim.play("idle")
        anim.update(10.0)  # muito tempo
        assert anim.is_finished is True

    def test_update_frozen_when_finished(self):
        anim = _animator([_clip(fps=8, n=4, loop=False)])
        anim.play("idle")
        anim.update(10.0)
        frame_after_finish = anim.current_frame
        anim.update(1.0)
        assert anim.current_frame == frame_after_finish

    def test_timer_accumulates_correctly(self):
        anim = _animator([_clip(fps=8)])
        anim.play("idle")
        anim.update(0.05)
        assert anim._timer == pytest.approx(0.05)

    def test_timer_reset_after_frame_advance(self):
        anim = _animator([_clip(fps=8)])
        anim.play("idle")
        anim.update(0.125)
        assert anim._timer == pytest.approx(0.0, abs=1e-9)


# ── TestOnFinish ─────────────────────────────────────────────────────────────
class TestOnFinish:
    def test_on_finish_called_when_nonloop_ends(self):
        cb = MagicMock()
        anim = _animator([_clip("attack", n=3, fps=8, loop=False)])
        anim.on_finish = cb
        anim.play("attack")
        anim.update(10.0)
        cb.assert_called_once_with("attack")

    def test_on_finish_not_called_for_loop_clip(self):
        cb = MagicMock()
        anim = _animator([_clip("idle", n=4, fps=8, loop=True)])
        anim.on_finish = cb
        anim.play("idle")
        anim.update(10.0)
        cb.assert_not_called()

    def test_on_finish_called_once_even_with_many_updates(self):
        cb = MagicMock()
        anim = _animator([_clip("die", n=2, fps=8, loop=False)])
        anim.on_finish = cb
        anim.play("die")
        for _ in range(20):
            anim.update(1.0)
        cb.assert_called_once()


# ── TestTransitions ────────────────────────────────────────────────────────────
class TestTransitions:
    def test_add_transition_returns_self(self):
        anim = _animator()
        assert anim.add_transition("idle", "run", lambda: True) is anim

    def test_transition_fires_when_condition_true(self):
        anim = _animator([_clip("idle"), _clip("run")])
        anim.play("idle")
        anim.add_transition("idle", "run", lambda: True)
        anim.update(0.01)
        assert anim.current_clip == "run"

    def test_transition_not_fires_when_condition_false(self):
        anim = _animator([_clip("idle"), _clip("run")])
        anim.play("idle")
        anim.add_transition("idle", "run", lambda: False)
        anim.update(0.01)
        assert anim.current_clip == "idle"

    def test_global_transition_fires_from_any_state(self):
        anim = _animator([_clip("idle"), _clip("run"), _clip("jump")])
        anim.play("run")
        anim.add_transition("*", "jump", lambda: True)
        anim.update(0.01)
        assert anim.current_clip == "jump"

    def test_transition_condition_exception_ignored(self):
        anim = _animator([_clip("idle"), _clip("run")])
        anim.play("idle")
        def bad(): raise RuntimeError("oops")
        anim.add_transition("idle", "run", bad)
        anim.update(0.01)  # não deve propagar
        assert anim.current_clip == "idle"

    def test_no_self_transition(self):
        """Transição para o próprio estado não deve reiniciar o clip."""
        anim = _animator([_clip("idle")])
        anim.play("idle")
        anim._frame_index = 2
        anim.add_transition("idle", "idle", lambda: True)
        anim.update(0.01)
        assert anim._frame_index == 2  # não reiniciou


# ── TestAnimationEvents ──────────────────────────────────────────────────────────
class TestAnimationEvents:
    def test_event_fires_at_correct_frame(self):
        cb = MagicMock()
        ev = AnimationEvent(frame_index=2, callback=cb)
        clip = AnimationClip("idle", frames=_frames(4), fps=8, events=[ev])
        anim = _animator([clip])
        anim.play("idle")
        anim.update(0.25)  # 0.25s @ 8fps = 2 frames
        cb.assert_called_once()

    def test_event_not_fired_before_frame(self):
        cb = MagicMock()
        ev = AnimationEvent(frame_index=3, callback=cb)
        clip = AnimationClip("idle", frames=_frames(4), fps=8, events=[ev])
        anim = _animator([clip])
        anim.play("idle")
        anim.update(0.125)  # só 1 frame
        cb.assert_not_called()

    def test_event_fired_only_once_per_cycle(self):
        cb = MagicMock()
        ev = AnimationEvent(frame_index=1, callback=cb)
        clip = AnimationClip("idle", frames=_frames(4), fps=8, events=[ev])
        anim = _animator([clip])
        anim.play("idle")
        anim.update(0.2)   # avança frame 1
        first_count = cb.call_count
        anim.update(0.01)  # mais um tick sem novo ciclo
        assert cb.call_count == first_count

    def test_event_resets_on_loop(self):
        cb = MagicMock()
        ev = AnimationEvent(frame_index=1, callback=cb)
        clip = AnimationClip("idle", frames=_frames(2), fps=8,
                             loop=True, events=[ev])
        anim = _animator([clip])
        anim.play("idle")
        anim.update(0.5)   # 4 loops completos de 2 frames
        assert cb.call_count >= 2


# ── TestStateQueries ────────────────────────────────────────────────────────────
class TestStateQueries:
    def test_current_clip_none_initially(self):
        assert _animator().current_clip is None

    def test_current_clip_after_play(self):
        anim = _animator([_clip("run")])
        anim.play("run")
        assert anim.current_clip == "run"

    def test_is_playing_true(self):
        anim = _animator([_clip("run")])
        anim.play("run")
        assert anim.is_playing("run") is True

    def test_is_playing_false_different_clip(self):
        anim = _animator([_clip("run"), _clip("idle")])
        anim.play("idle")
        assert anim.is_playing("run") is False

    def test_is_playing_false_no_clip(self):
        assert _animator().is_playing("idle") is False

    def test_is_finished_false_initially(self):
        anim = _animator([_clip("idle", loop=False)])
        anim.play("idle")
        assert anim.is_finished is False

    def test_is_finished_true_after_nonloop_ends(self):
        anim = _animator([_clip("die", n=2, fps=8, loop=False)])
        anim.play("die")
        anim.update(10.0)
        assert anim.is_finished is True

    def test_repr_contains_clip_name(self):
        anim = _animator([_clip("idle")])
        anim.play("idle")
        assert "idle" in repr(anim)

    def test_repr_contains_frame_index(self):
        anim = _animator([_clip("idle")])
        anim.play("idle")
        assert "0" in repr(anim)
