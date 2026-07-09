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

# ── stubs de módulos externos ──────────────────────────────────────────────────────

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

# engine.physics.collider — FIX: CollisionInfo incluído no stub
_phys_mod = ModuleType("engine.physics.collider")
_BC = MagicMock()
_BC._scene_tilemaps            = {}
_BC._scene_tilemap_components  = {}
_BC._registry                  = []
_BC.check_all                  = MagicMock()
_CC = MagicMock()
_CC._registry                  = []
_CC.check_all                  = MagicMock()
_CollisionInfo                 = MagicMock()  # FIX: adicionado
_phys_mod.BoxCollider    = _BC
_phys_mod.CircleCollider = _CC
_phys_mod.CollisionInfo  = _CollisionInfo     # FIX: adicionado
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


# ── helpers ──────────────────────────────────────────────────────────────────────────

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
def clean_sm():
    SceneManager.reset()
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


# ────────────────────────────────────────────────────────────────────────────────
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


# ────────────────────────────────────────────────────────────────────────────────
class TestBind:
    def test_bind_sets_engine_ref(self):
        e = fake_engine()
        sm().bind(e)
        assert sm()._engine is e

    def test_bind_patches_change_scene(self):
        e = fake_engine()
        sm().bind(e)
        assert e.change_scene is sm().load


# ────────────────────────────────────────────────────────────────────────────────
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
        m.load(_FakeScene(), transition=tr)
        assert m._transition is tr
        assert m.is_transitioning is True

    def test_load_with_transition_defers_start(self):
        s  = _FakeScene()
        tr = _FakeTransition()
        sm().load(s, transition=tr)
        s.start.assert_not_called()


# ────────────────────────────────────────────────────────────────────────────────
class TestPush:
    def test_push_increases_depth(self):
        m = sm()
        m.load(_FakeScene("A"))
        m.push(_FakeScene("B"))
        assert m.stack_depth == 2

    def test_push_current_is_new(self):
        m = sm()
        a = _FakeScene("A")
        b = _FakeScene("B")
        m.load(a)
        m.push(b)
        assert m.current is b

    def test_push_calls_start_on_new(self):
        m = sm()
        m.load(_FakeScene("A"))
        b = _FakeScene("B")
        m.push(b)
        b.start.assert_called_once()

    def test_push_preserves_previous_scene(self):
        m = sm()
        a = _FakeScene("A")
        m.load(a)
        m.push(_FakeScene("B"))
        assert m._stack[0] is a

    def test_push_with_transition(self):
        tr = _FakeTransition()
        m  = sm()
        m.load(_FakeScene("A"))
        m.push(_FakeScene("B"), transition=tr)
        assert m._transition is tr


# ────────────────────────────────────────────────────────────────────────────────
class TestPop:
    def test_pop_reduces_depth(self):
        m = sm()
        m.load(_FakeScene("A"))
        m.push(_FakeScene("B"))
        m.pop()
        assert m.stack_depth == 1

    def test_pop_restores_previous_current(self):
        m = sm()
        a = _FakeScene("A")
        m.load(a)
        m.push(_FakeScene("B"))
        m.pop()
        assert m.current is a

    def test_pop_single_scene_no_effect(self):
        m = sm()
        m.load(_FakeScene("A"))
        m.pop()
        assert m.stack_depth == 1

    def test_pop_empty_stack_no_error(self):
        sm().pop()  # pilha vazia

    def test_pop_with_transition(self):
        tr = _FakeTransition()
        m  = sm()
        m.load(_FakeScene("A"))
        m.push(_FakeScene("B"))
        m.pop(transition=tr)
        assert m._transition is tr

    def test_pop_resets_ui(self):
        m = sm()
        m.load(_FakeScene("A"))
        m.push(_FakeScene("B"))
        _UIManager.reset.reset_mock()
        m.pop()
        _UIManager.reset.assert_called()


# ────────────────────────────────────────────────────────────────────────────────
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

    def test_update_during_in_phase_updates_scene(self):
        m  = sm()
        s  = _FakeScene()
        tr = _FakeTransition()
        tr.phase     = _FakePhase.IN
        tr.should_swap = False
        m.load(s)
        m._transition = tr
        s.update.reset_mock()
        m.update(0.016)
        s.update.assert_called_once_with(0.016)

    def test_update_clears_transition_when_done(self):
        m  = sm()
        s  = _FakeScene()
        tr = _FakeTransition()
        tr.is_done   = True
        tr.should_swap = False
        tr.phase     = _FakePhase.DONE
        m.load(s)
        m._transition = tr
        m.update(0.016)
        assert m._transition is None

    def test_update_fires_on_transition_end_callback(self):
        m  = sm()
        s  = _FakeScene("End")
        tr = _FakeTransition()
        tr.is_done   = True
        tr.should_swap = False
        tr.phase     = _FakePhase.DONE
        m.load(s)
        m._transition = tr
        cb = MagicMock()
        m.on_transition_end = cb
        m.update(0.016)
        cb.assert_called_once()

    def test_update_executes_swap_when_should_swap(self):
        m   = sm()
        old = _FakeScene("Old")
        new = _FakeScene("New")
        m.load(old)
        tr = _FakeTransition()
        tr.should_swap = True
        tr.phase       = _FakePhase.OUT
        m._transition    = tr
        m._pending_scene = new
        m._pending_pop   = False
        m._pending_push  = False
        m.update(0.016)
        assert m.current is new


# ────────────────────────────────────────────────────────────────────────────────
class TestDraw:
    def test_draw_delegates_to_current(self):
        m      = sm()
        s      = _FakeScene()
        screen = MagicMock()
        m.load(s)
        m.draw(screen)
        s.draw.assert_called_once_with(screen)

    def test_draw_empty_stack_no_error(self):
        sm().draw(MagicMock())

    def test_draw_out_phase_uses_transition_draw(self):
        m      = sm()
        s      = _FakeScene()
        screen = MagicMock()
        screen.get_size = MagicMock(return_value=(800, 600))
        tr     = _FakeTransition()
        tr.phase   = _FakePhase.OUT
        tr.is_done = False
        m.load(s)
        m._transition = tr
        m.draw(screen)
        tr.draw.assert_called_once_with(screen)

    def test_draw_in_phase_uses_transition_draw(self):
        m      = sm()
        s      = _FakeScene()
        screen = MagicMock()
        screen.get_size = MagicMock(return_value=(800, 600))
        tr     = _FakeTransition()
        tr.phase   = _FakePhase.IN
        tr.is_done = False
        m.load(s)
        m._transition = tr
        m.draw(screen)
        tr.draw.assert_called_once_with(screen)


# ────────────────────────────────────────────────────────────────────────────────
class TestHandleEvent:
    def test_handle_event_delegates_to_current(self):
        m  = sm()
        s  = _FakeScene()
        ev = MagicMock()
        m.load(s)
        m.handle_event(ev)
        s.handle_event.assert_called_once_with(ev)

    def test_handle_event_blocked_during_transition(self):
        m  = sm()
        s  = _FakeScene()
        ev = MagicMock()
        tr = _FakeTransition()
        tr.is_done = False
        m.load(s)
        m._transition = tr
        s.handle_event.reset_mock()
        m.handle_event(ev)
        s.handle_event.assert_not_called()

    def test_handle_event_empty_stack_no_error(self):
        sm().handle_event(MagicMock())


# ────────────────────────────────────────────────────────────────────────────────
class TestCallbacks:
    def test_on_transition_start_fires_on_load(self):
        cb = MagicMock()
        m  = sm()
        m.on_transition_start = cb
        tr = _FakeTransition()
        s  = _FakeScene("Target")
        m.load(s, transition=tr)
        cb.assert_called_once()

    def test_on_transition_end_fires_when_done(self):
        cb = MagicMock()
        m  = sm()
        s  = _FakeScene("Done")
        m.load(s)
        tr = _FakeTransition()
        tr.is_done     = True
        tr.should_swap = False
        tr.phase       = _FakePhase.DONE
        m._transition  = tr
        m.on_transition_end = cb
        m.update(0.016)
        cb.assert_called_once()


# ────────────────────────────────────────────────────────────────────────────────
class TestRepr:
    def test_repr_contains_depth(self):
        m = sm()
        m.load(_FakeScene("X"))
        assert "depth=1" in repr(m)

    def test_repr_shows_not_transitioning(self):
        m = sm()
        m.load(_FakeScene())
        assert "transitioning=False" in repr(m)

    def test_repr_empty_stack(self):
        r = repr(sm())
        assert "None" in r
