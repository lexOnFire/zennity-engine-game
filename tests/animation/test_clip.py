"""
tests/animation/test_clip.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/animation/clip.py.

Estratégia de isolamento:
  - pygame.transform.flip é mockado apenas durante cada teste deste arquivo.
  - O mock é restaurado automaticamente pelo monkeypatch, sem afetar outros testes.
  - Frames são MagicMock opacos.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

# ── pygame / transform guard ────────────────────────────────────────────────

if "pygame" not in sys.modules:
    _pg = ModuleType("pygame")
    _transform = ModuleType("pygame.transform")
    _pg.transform = _transform
    sys.modules["pygame"] = _pg
    sys.modules["pygame.transform"] = _transform
else:
    _pg = sys.modules["pygame"]
    _transform = sys.modules.get("pygame.transform", getattr(_pg, "transform", None))
    if _transform is None:
        _transform = ModuleType("pygame.transform")
        _pg.transform = _transform
        sys.modules["pygame.transform"] = _transform

from engine.animation.clip import AnimationClip, AnimationEvent  # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_flip(monkeypatch):
    flip_mock = MagicMock(side_effect=lambda f, h, v: MagicMock(name=f"flip({f})"))
    monkeypatch.setattr(_transform, "flip", flip_mock, raising=False)
    monkeypatch.setattr(_pg, "transform", _transform, raising=False)
    yield


def _frames(n=4):
    return [MagicMock(name=f"f{i}") for i in range(n)]


def _clip(name="idle", n=4, fps=10.0, loop=True, flip_h=False):
    return AnimationClip(name=name, frames=_frames(n), fps=fps,
                         loop=loop, flip_h=flip_h)


# ── TestAnimationEvent ──────────────────────────────────────────────────────
class TestAnimationEvent:
    def test_frame_index_stored(self):
        ev = AnimationEvent(frame_index=3, callback=lambda: None)
        assert ev.frame_index == 3

    def test_callback_stored(self):
        cb = MagicMock()
        ev = AnimationEvent(frame_index=0, callback=cb)
        assert ev.callback is cb

    def test_fired_defaults_false(self):
        ev = AnimationEvent(frame_index=0, callback=lambda: None)
        assert ev.fired is False

    def test_fired_can_be_set_true(self):
        ev = AnimationEvent(frame_index=0, callback=lambda: None)
        ev.fired = True
        assert ev.fired is True

    def test_callback_is_callable(self):
        ev = AnimationEvent(frame_index=1, callback=lambda: None)
        assert callable(ev.callback)

    def test_two_events_independent(self):
        ev1 = AnimationEvent(frame_index=0, callback=lambda: None)
        ev2 = AnimationEvent(frame_index=1, callback=lambda: None)
        ev1.fired = True
        assert ev2.fired is False


# ── TestAnimationClipInit ───────────────────────────────────────────────────
class TestAnimationClipInit:
    def test_name_stored(self):
        assert _clip("run").name == "run"

    def test_fps_stored(self):
        assert _clip(fps=12.0).fps == pytest.approx(12.0)

    def test_fps_minimum_clamped(self):
        c = AnimationClip("x", _frames(), fps=0.0)
        assert c.fps == pytest.approx(0.01)

    def test_fps_negative_clamped(self):
        c = AnimationClip("x", _frames(), fps=-5.0)
        assert c.fps == pytest.approx(0.01)

    def test_loop_stored_true(self):
        assert _clip(loop=True).loop is True

    def test_loop_stored_false(self):
        assert _clip(loop=False).loop is False

    def test_frames_stored_as_list(self):
        frames = _frames(3)
        c = AnimationClip("idle", frames)
        assert c.frames == frames

    def test_frames_are_copy_not_same_list(self):
        frames = _frames(3)
        c = AnimationClip("idle", frames)
        assert c.frames is not frames

    def test_events_empty_on_init(self):
        assert _clip().events == []

    def test_no_flip_h_does_not_call_transform(self):
        _clip(flip_h=False)
        _transform.flip.assert_not_called()


# ── TestFlipH ───────────────────────────────────────────────────────────────
class TestFlipH:
    def test_flip_h_calls_transform_for_each_frame(self):
        frames = _frames(3)
        AnimationClip("idle", frames, flip_h=True)
        assert _transform.flip.call_count == 3

    def test_flip_h_replaces_frames_with_flipped(self):
        frames = _frames(2)
        c = AnimationClip("idle", frames, flip_h=True)
        for f in frames:
            assert f not in c.frames

    def test_flip_h_preserves_frame_count(self):
        frames = _frames(5)
        c = AnimationClip("idle", frames, flip_h=True)
        assert c.frame_count == 5

    def test_flip_h_called_with_correct_args(self):
        frames = _frames(1)
        AnimationClip("idle", frames, flip_h=True)
        _transform.flip.assert_called_once_with(frames[0], True, False)

    def test_no_flip_h_frames_identical_to_input(self):
        frames = _frames(4)
        c = AnimationClip("idle", frames, flip_h=False)
        assert c.frames == frames


# ── TestFrameCount ──────────────────────────────────────────────────────────
class TestFrameCount:
    def test_frame_count_matches_input(self):
        assert _clip(n=6).frame_count == 6

    def test_frame_count_one(self):
        assert _clip(n=1).frame_count == 1

    def test_frame_count_zero(self):
        c = AnimationClip("x", [])
        assert c.frame_count == 0


# ── TestDuration ────────────────────────────────────────────────────────────
class TestDuration:
    def test_duration_4_frames_10fps(self):
        assert _clip(n=4, fps=10.0).duration == pytest.approx(0.4)

    def test_duration_8_frames_8fps(self):
        assert _clip(n=8, fps=8.0).duration == pytest.approx(1.0)

    def test_duration_zero_frames(self):
        c = AnimationClip("x", [], fps=10.0)
        assert c.duration == pytest.approx(0.0)

    def test_duration_scales_with_fps(self):
        c1 = _clip(n=4, fps=10.0)
        c2 = _clip(n=4, fps=20.0)
        assert c1.duration == pytest.approx(c2.duration * 2)


# ── TestAddEvent ────────────────────────────────────────────────────────────
class TestAddEvent:
    def test_add_event_returns_self(self):
        c = _clip()
        assert c.add_event(0, lambda: None) is c

    def test_add_event_appended_to_events(self):
        c = _clip()
        cb = MagicMock()
        c.add_event(2, cb)
        assert len(c.events) == 1
        assert c.events[0].frame_index == 2
        assert c.events[0].callback is cb

    def test_add_multiple_events(self):
        c = _clip()
        c.add_event(0, MagicMock())
        c.add_event(1, MagicMock())
        c.add_event(3, MagicMock())
        assert len(c.events) == 3

    def test_add_event_fired_starts_false(self):
        c = _clip()
        c.add_event(0, lambda: None)
        assert c.events[0].fired is False

    def test_add_event_chaining(self):
        c = _clip()
        cb1, cb2 = MagicMock(), MagicMock()
        c.add_event(0, cb1).add_event(1, cb2)
        assert len(c.events) == 2

    def test_events_property_returns_list(self):
        assert isinstance(_clip().events, list)

    def test_events_with_constructor_events_param(self):
        c = _clip()
        c.add_event(0, lambda: None)
        assert len(c.events) == 1


# ── TestRepr ────────────────────────────────────────────────────────────────
class TestRepr:
    def test_repr_contains_name(self):
        assert "run" in repr(_clip("run"))

    def test_repr_contains_frame_count(self):
        c = _clip(n=6)
        assert "6" in repr(c)

    def test_repr_contains_fps(self):
        c = _clip(fps=12.0)
        assert "12" in repr(c)

    def test_repr_contains_loop(self):
        assert "True" in repr(_clip(loop=True))
        assert "False" in repr(_clip(loop=False))
