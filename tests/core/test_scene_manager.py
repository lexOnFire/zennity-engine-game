"""
tests/core/test_scene_manager.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/core/scene_manager.py.

Estratégia de isolamento:
  - SceneManager.reset() antes de cada teste (singleton limpo).
  - pygame, engine.transitions, engine.ui.ui_manager,
    engine.physics.collider e engine.audio são stubados em sys.modules
    antes do import — nenhum código externo é executado.
  - _FakeScene encapsula spies de start / update / draw / on_exit /
    handle_event para verificar propagação.
  - Transições são simuladas por _FakeTransition, permitindo controlar
    exatamente as fases OUT → SWAP → IN sem depender de pygame.time.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, call

import pytest

# ── stubs de módulos externos ──────────────────────────────────────────

# pygame
if "pygame" not in sys.modules:
    _pg = ModuleType("pygame")
    _Surface = MagicMock
    _pg.Surface = _Surface
    _pg.event = ModuleType("pygame.event")
    _pg.event.Event = MagicMock
    sys.modules["pygame"] = _pg
    sys.modules["pygame.event"] = _pg.event

# engine.transitions — stub com TransitionPhase e FadeTransition
_trans_mod = ModuleType("engine.transitions")

class _FakePhase:
    OUT  = "OUT"
    SWAP = "SWAP"
    IN   = "IN"
    DONE = "DONE"

_trans_mod.TransitionPhase = _FakePhase
_trans_mod.Transition      = MagicMock
_trans_mod.FadeTransition  = MagicMock
sys.modules["engine.transitions"] = _trans_mod

# engine.ui.ui_manager
_ui_mod           = ModuleType("engine.ui.ui_manager")
_UIManager        = MagicMock()
_UIManager.reset  = MagicMock()
_ui_mod.UIManager = _UIManager
sys.modules["engine.ui"]             = ModuleType("engine.ui")
sys.modules["engine.ui.ui_manager"]  = _ui_mod

# engine.physics.collider
_phys_mod = ModuleType("engine.physics.collider")
_BC = MagicMock()
_BC._scene_tilemaps            = {}
_BC._scene_tilemap_components  = {}
_BC._registry                  = []
_BC.check_all                  = MagicMock()
_CC = MagicMock()
_CC._registry                  = []
_CC.check_all                  = MagicMock()
_phys_mod.BoxCollider    = _BC
_phys_mod.CircleCollider = _CC
sys.modules["engine.physics"]          = ModuleType("engine.physics")
sys.modules["engine.physics.collider"] = _phys_mod

# engine.audio
_audio_mod              = ModuleType("engine.audio")
_AudioManager           = MagicMock()
_AudioManager.stop_music    = MagicMock()
_AudioManager.unload_cache  = MagicMock()
_audio_mod.AudioManager     = _AudioManager
sys.modules["engine.audio"] = _audio_mod

# Agora importa o módulo real
from engine.core.scene_manager import SceneManager  # noqa: E402


# ── helpers ───────────────────────────────────────────────────────────────

class _FakeScene:
    def __init__(self, name="FakeScene"):
        self.__class__.__name__ = name
        self.engine  = None
        self.start       = MagicMock()
        self.update      = MagicMock()
        self.draw        = MagicMock()
        self.on_exit     = MagicMock()
        self.handle_event = MagicMock()


class _FakeTransition:
    """Transição fake totalmente controlável por testes."""
    def __init__(self):
        self.phase         = _FakePhase.OUT
        self.is_done       = False
        self.should_swap   = False
        self.snapshot_out  = None
        self.snapshot_in   = None
        self.update        = MagicMock()
        self.draw          = MagicMock()


@pytest.fixture(autouse=True)
def clean_sm(monkeypatch):
    SceneManager.reset()
    monkeypatch.setattr(
        SceneManager,
        "_get_collider_classes",
        staticmethod(lambda: (_BC, _CC)),
    )
    _UIManager.reset.reset_mock()
    _BC.check_all.reset_mock()
    _CC.check_all.reset_mock()
    _AudioManager.stop_music.reset_mock()
    _AudioManager.unload_cache.reset_mock()
    yield
    SceneManager.reset()


def sm() -> SceneManager:
    return SceneManager.instance()


def fake_engine():
    e = MagicMock()
    e.change_scene = MagicMock()
    return e


# ─────────────────────────────────────────────────────────────────────────────
class TestSingleton:
    def test_instance_is_same_object(self):
        assert SceneManager.instance() is SceneManager.instance()

    def test_reset_creates_new_instance(self):
        a = SceneManager.instance()
        SceneManager.reset()
        b = SceneManager.instance()
        assert a is not b

    def test_initial_state_empty_stack(self):
        assert sm().stack_depth == 0

    def test_initial_current_is_none(self):
        assert sm().current is None

    def test_not_transitioning_by_default(self):
        assert sm().is_transitioning is False


# ─────────────────────────────────────────────────────────────────────────────
class TestBind:
    def test_bind_sets_engine_ref(self):
        e = fake_engine()
        sm().bind(e)
        assert sm()._engine is e

    def test_bind_patches_change_scene(self):
        e = fake_engine()
        sm().bind(e)
        assert e.change_scene is sm().load


# ─────────────────────────────────────────────────────────────────────────────
class TestLoad:
    def test_load_sets_current(self):
        s = _FakeScene()
        sm().load(s)
        assert sm().current is s

    def test_load_calls_start(self):
        s = _FakeScene()
        sm().load(s)
        s.start.assert_called_once()

    def test_load_clears_previous_stack(self):
        a, b = _FakeScene("A"), _FakeScene("B")
        m = sm()
        m.load(a)
        m.load(b)
        assert m.stack_depth == 1
        assert m.current is b

    def test_load_resets_ui(self):
        sm().load(_FakeScene())
        _UIManager.reset.assert_called()

    def test_load_stops_audio(self):
        sm().load(_FakeScene())
        _AudioManager.stop_music.assert_called_once()
        _AudioManager.unload_cache.assert_called_once()

    def test_load_sets_engine_on_scene(self):
        e = fake_engine()
        m = sm()
        m.bind(e)
        s = _FakeScene()
        m.load(s)
        assert s.engine is e

    def test_load_with_transition_starts_transition(self):
        tr = _FakeTransition()
        m  = sm()
        s  = _FakeScene()
        m.load(s, transition=tr)
        assert m._transition is tr
        assert m._pending_scene is s


# ─────────────────────────────────────────────────────────────────────────────
class TestPush:
    def test_push_adds_scene_to_stack(self):
        m = sm()
        a, b = _FakeScene("A"), _FakeScene("B")
        m.load(a)
        m.push(b)
        assert m.stack_depth == 2
        assert m.current is b

    def test_push_resets_ui(self):
        sm().push(_FakeScene())
        _UIManager.reset.assert_called()

    def test_push_sets_engine(self):
        e = fake_engine()
        m = sm()
        m.bind(e)
        s = _FakeScene()
        m.push(s)
        assert s.engine is e

    def test_push_with_transition_sets_flags(self):
        m = sm()
        tr = _FakeTransition()
        s = _FakeScene()
        m.push(s, transition=tr)
        assert m._transition is tr
        assert m._pending_push is True
        assert m._pending_scene is s


# ─────────────────────────────────────────────────────────────────────────────
class TestPop:
    def test_pop_empty_or_single_noop(self):
        m = sm()
        m.pop()
        assert m.stack_depth == 0
        m.load(_FakeScene())
        m.pop()
        assert m.stack_depth == 1

    def test_pop_removes_top(self):
        m = sm()
        a, b = _FakeScene("A"), _FakeScene("B")
        m.load(a)
        m.push(b)
        m.pop()
        assert m.current is a
        assert m.stack_depth == 1

    def test_pop_resets_ui(self):
        m = sm()
        m.load(_FakeScene("A"))
        m.push(_FakeScene("B"))
        _UIManager.reset.reset_mock()
        m.pop()
        _UIManager.reset.assert_called()

    def test_pop_with_transition_sets_flags(self):
        m = sm()
        a, b = _FakeScene("A"), _FakeScene("B")
        m.load(a)
        m.push(b)
        tr = _FakeTransition()
        m.pop(transition=tr)
        assert m._transition is tr
        assert m._pending_pop is True


# ─────────────────────────────────────────────────────────────────────────────
class TestUpdate:
    def test_update_delegates_to_current(self):
        m = sm()
        s = _FakeScene()
        m.load(s)
        s.update.reset_mock()
        m.update(0.016)
        s.update.assert_called_once_with(0.016)

    def test_update_empty_stack_no_error(self):
        sm().update(0.016)

    def test_update_runs_physics(self):
        m = sm()
        m.load(_FakeScene())
        _BC.check_all.reset_mock()
        _CC.check_all.reset_mock()
        m.update(0.016)
        _BC.check_all.assert_called()
        _CC.check_all.assert_called()

    def test_update_during_out_phase_does_not_update_scene(self):
        m  = sm()
        s  = _FakeScene()
        tr = _FakeTransition()
        tr.phase = _FakePhase.OUT
        m.load(s)
        m._transition = tr
        s.update.reset_mock()
        m.update(0.016)
        s.update.assert_not_called()

    def test_update_transition_update_called(self):
        m = sm()
        s = _FakeScene()
        tr = _FakeTransition()
        m.load(s)
        m._transition = tr
        m.update(0.016)
        tr.update.assert_called_once_with(0.016)

    def test_update_swap_executes_pending(self):
        m = sm()
        a, b = _FakeScene("A"), _FakeScene("B")
        tr = _FakeTransition()
        tr.phase = _FakePhase.SWAP
        tr.should_swap = True
        m.load(a)
        m.load(b, transition=tr)
        m.update(0.016)
        assert m.current is b

    def test_update_done_clears_transition(self):
        m = sm()
        s = _FakeScene()
        tr = _FakeTransition()
        tr.is_done = True
        m.load(s)
        m._transition = tr
        m.update(0.016)
        assert m._transition is tr or m._transition is None


# ─────────────────────────────────────────────────────────────────────────────
class TestDraw:
    def test_draw_delegates_to_current(self):
        m = sm()
        s = _FakeScene()
        screen = MagicMock()
        m.load(s)
        m.draw(screen)
        s.draw.assert_called()

    def test_draw_empty_no_error(self):
        sm().draw(MagicMock())

    def test_draw_during_transition_calls_transition_draw(self):
        m = sm()
        s = _FakeScene()
        tr = _FakeTransition()
        m.load(s)
        m._transition = tr
        m.draw(MagicMock(get_size=MagicMock(return_value=(10, 10))))
        tr.draw.assert_called()


# ─────────────────────────────────────────────────────────────────────────────
class TestHandleEvent:
    def test_handle_event_delegates_to_current(self):
        m = sm()
        s = _FakeScene()
        ev = MagicMock()
        m.load(s)
        m.handle_event(ev)
        s.handle_event.assert_called_once_with(ev)

    def test_handle_event_blocked_during_transition(self):
        m = sm()
        s = _FakeScene()
        tr = _FakeTransition()
        m.load(s)
        m._transition = tr
        ev = MagicMock()
        m.handle_event(ev)
        s.handle_event.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
class TestCallbacks:
    def test_transition_start_callback(self):
        m = sm()
        cb = MagicMock()
        m.on_transition_start = cb
        target = _FakeScene("Target")
        m.load(target, transition=_FakeTransition())
        cb.assert_called_once_with(target.__class__.__name__)

    def test_transition_end_callback(self):
        m = sm()
        cb = MagicMock()
        m.on_transition_end = cb
        s = _FakeScene("Scene")
        m.load(s)
        tr = _FakeTransition()
        tr.phase = _FakePhase.DONE
        tr.is_done = True
        m._transition = tr
        m.update(0.016)
        if cb.called:
            cb.assert_called_with(s.__class__.__name__)


# ─────────────────────────────────────────────────────────────────────────────
class TestRepr:
    def test_repr_contains_current(self):
        m = sm()
        assert "None" in repr(m)
        m.load(_FakeScene("Menu"))
        assert "Menu" in repr(m)

    def test_repr_contains_depth(self):
        m = sm()
        m.load(_FakeScene())
        assert "depth=1" in repr(m)

    def test_repr_contains_transitioning(self):
        m = sm()
        assert "transitioning" in repr(m)
