"""
tests/core/test_scene_manager.py
─────────────────────────────────────────────────────────────────
Testes unitários do SceneManager.

Estratégia de isolamento:
  - pygame NÃO é inicializado. Onde Surface é necessária, usamos MagicMock.
  - UIManager, BoxCollider, CircleCollider, AudioManager são todos mockados
    via sys.modules antes de qualquer import do módulo testado.
  - SceneManager.reset() é chamado em cada teardown para garantir
    isolamento completo entre testes (singleton limpo).
  - Transition é subclassificada minimamente para controlar o estado
    sem pygame.Surface real.

Grupos:
  TestSingleton              — instance()/reset()
  TestLoad                   — load() sem transição
  TestPushPop                — push()/pop() sem transição
  TestStackProperties        — current, stack_depth, is_transitioning
  TestBind                   — bind() e patch de engine.change_scene
  TestHandleEvent            — bloqueio durante transição
  TestLoadWithTransition     — load() com transição, swap no momento certo
  TestPushWithTransition     — push() com transição
  TestPopWithTransition      — pop() com transição
  TestCallbacks              — on_transition_start / on_transition_end
  TestUpdateDraw             — update() e draw() delegam à cena correta
  TestRunPhysics             — _run_physics() via update
  TestDoSwapLoadCleanup      — limpeza de colliders e audio em _do_swap_load
"""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch, call

import pytest

# ─────────────────────────────────────────────────────────────────
# Mock de módulos pesados ANTES de qualquer import da engine
# ─────────────────────────────────────────────────────────────────

def _make_pygame_mock():
    pg = MagicMock()
    # Surface precisa ser uma classe real que aceita instanciação com args
    class FakeSurface:
        def __init__(self, size=(800, 600)):
            self.size = size
        def get_size(self):
            return self.size
    pg.Surface = FakeSurface
    return pg

pg_mock = _make_pygame_mock()
sys.modules.setdefault("pygame", pg_mock)
sys.modules.setdefault("pygame.mixer", MagicMock())
sys.modules.setdefault("pygame.font", MagicMock())
sys.modules.setdefault("pygame.image", MagicMock())

# Stub UIManager
ui_manager_mock = MagicMock()
ui_pkg = types.ModuleType("engine.ui")
ui_mgr_mod = types.ModuleType("engine.ui.ui_manager")
ui_mgr_mod.UIManager = ui_manager_mock
sys.modules.setdefault("engine.ui", ui_pkg)
sys.modules.setdefault("engine.ui.ui_manager", ui_mgr_mod)

# Stub transitions
class _Phase:
    OUT  = "OUT"
    SWAP = "SWAP"
    IN   = "IN"
    DONE = "DONE"

class _FakeTransitionBase:
    """Base stub — não depende de pygame."""
    def __init__(self):
        self.phase        = _Phase.OUT
        self.is_done      = False
        self.should_swap  = False
        self.snapshot_out = None
        self.snapshot_in  = None
    def update(self, dt): pass
    def draw(self, screen): pass

class _FakeFadeTransition(_FakeTransitionBase):
    def __init__(self, color=(0, 0, 0), duration_out=0.3, duration_in=0.3):
        super().__init__()

transitions_mod = types.ModuleType("engine.transitions")
transitions_mod.Transition      = _FakeTransitionBase
transitions_mod.TransitionPhase = _Phase
transitions_mod.FadeTransition  = _FakeFadeTransition
sys.modules["engine.transitions"] = transitions_mod

# Agora é seguro importar
from engine.core.scene_manager import SceneManager  # noqa: E402


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def make_scene(name="Scene"):
    s = MagicMock()
    s.__class__.__name__ = name
    s.start = MagicMock()
    s.update = MagicMock()
    s.draw = MagicMock()
    s.handle_event = MagicMock()
    s._ui_setup = MagicMock()
    return s


def make_transition(should_swap_after: int = 0):
    """Retorna transição que dispara should_swap após N chamadas a update."""
    tr = _FakeTransitionBase()
    tr._update_count = 0
    tr._swap_after   = should_swap_after
    original_update  = tr.update

    def _update(dt):
        tr._update_count += 1
        if tr._update_count > tr._swap_after:
            tr.should_swap = True
            tr.phase       = _Phase.IN
        if tr._update_count > tr._swap_after + 1:
            tr.is_done = True
            tr.phase   = _Phase.DONE

    tr.update = _update
    return tr


@pytest.fixture(autouse=True)
def reset_sm():
    """Garante singleton limpo antes e depois de cada teste."""
    SceneManager.reset()
    ui_manager_mock.reset.reset_mock()
    yield
    SceneManager.reset()


# ─────────────────────────────────────────────────────────────────
# TestSingleton
# ─────────────────────────────────────────────────────────────────

class TestSingleton:
    def test_instance_returns_same_object(self):
        a = SceneManager.instance()
        b = SceneManager.instance()
        assert a is b

    def test_reset_creates_new_instance(self):
        a = SceneManager.instance()
        SceneManager.reset()
        b = SceneManager.instance()
        assert a is not b

    def test_reset_clears_inst(self):
        SceneManager.instance()
        SceneManager.reset()
        assert SceneManager._inst is None

    def test_new_instance_has_empty_stack(self):
        sm = SceneManager.instance()
        assert sm.stack_depth == 0

    def test_new_instance_no_transition(self):
        sm = SceneManager.instance()
        assert sm._transition is None


# ─────────────────────────────────────────────────────────────────
# TestLoad (sem transição)
# ─────────────────────────────────────────────────────────────────

class TestLoad:
    def test_load_sets_current(self):
        sm = SceneManager.instance()
        scene = make_scene("A")
        with patch.object(sm, "_do_swap_load", wraps=sm._do_swap_load):
            sm.load(scene)
        assert sm.current is scene

    def test_load_calls_scene_start(self):
        sm = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        scene.start.assert_called_once()

    def test_load_sets_stack_depth_1(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        assert sm.stack_depth == 1

    def test_load_replaces_previous_scene(self):
        sm = SceneManager.instance()
        a, b = make_scene("A"), make_scene("B")
        sm.load(a)
        sm.load(b)
        assert sm.current is b
        assert sm.stack_depth == 1

    def test_load_clears_stack_completely(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm._stack.append(make_scene())   # força 2 cenas manualmente
        sm.load(make_scene())
        assert sm.stack_depth == 1

    def test_load_assigns_engine_to_scene(self):
        sm = SceneManager.instance()
        engine = MagicMock()
        sm.bind(engine)
        scene = make_scene()
        sm.load(scene)
        assert scene.engine is engine

    def test_load_calls_ui_manager_reset(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        ui_manager_mock.reset.assert_called()


# ─────────────────────────────────────────────────────────────────
# TestPushPop (sem transição)
# ─────────────────────────────────────────────────────────────────

class TestPushPop:
    def test_push_increases_depth(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm.push(make_scene())
        assert sm.stack_depth == 2

    def test_push_changes_current(self):
        sm = SceneManager.instance()
        sm.load(make_scene("Base"))
        top = make_scene("Top")
        sm.push(top)
        assert sm.current is top

    def test_push_calls_start_on_new_scene(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        top = make_scene()
        sm.push(top)
        top.start.assert_called_once()

    def test_pop_decreases_depth(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm.push(make_scene())
        sm.pop()
        assert sm.stack_depth == 1

    def test_pop_restores_previous_scene(self):
        sm = SceneManager.instance()
        base = make_scene("Base")
        sm.load(base)
        sm.push(make_scene("Top"))
        sm.pop()
        assert sm.current is base

    def test_pop_on_single_scene_does_nothing(self):
        sm = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        sm.pop()
        assert sm.stack_depth == 1
        assert sm.current is scene

    def test_pop_calls_ui_setup_if_present(self):
        sm = SceneManager.instance()
        base = make_scene()
        sm.load(base)
        sm.push(make_scene())
        sm.pop()
        base._ui_setup.assert_called_once()

    def test_multiple_push_pop_restores_order(self):
        sm = SceneManager.instance()
        a, b, c = make_scene("A"), make_scene("B"), make_scene("C")
        sm.load(a)
        sm.push(b)
        sm.push(c)
        sm.pop()
        sm.pop()
        assert sm.current is a
        assert sm.stack_depth == 1


# ─────────────────────────────────────────────────────────────────
# TestStackProperties
# ─────────────────────────────────────────────────────────────────

class TestStackProperties:
    def test_current_none_when_empty(self):
        sm = SceneManager.instance()
        assert sm.current is None

    def test_stack_depth_zero_initially(self):
        sm = SceneManager.instance()
        assert sm.stack_depth == 0

    def test_is_transitioning_false_initially(self):
        sm = SceneManager.instance()
        assert sm.is_transitioning is False

    def test_is_transitioning_true_during_active_transition(self):
        sm = SceneManager.instance()
        tr = _FakeTransitionBase()
        tr.is_done = False
        sm._transition = tr
        assert sm.is_transitioning is True

    def test_is_transitioning_false_when_transition_done(self):
        sm = SceneManager.instance()
        tr = _FakeTransitionBase()
        tr.is_done = True
        sm._transition = tr
        assert sm.is_transitioning is False


# ─────────────────────────────────────────────────────────────────
# TestBind
# ─────────────────────────────────────────────────────────────────

class TestBind:
    def test_bind_sets_engine(self):
        sm = SceneManager.instance()
        engine = MagicMock()
        sm.bind(engine)
        assert sm._engine is engine

    def test_bind_patches_change_scene(self):
        sm = SceneManager.instance()
        engine = MagicMock()
        sm.bind(engine)
        assert engine.change_scene is sm.load


# ─────────────────────────────────────────────────────────────────
# TestHandleEvent
# ─────────────────────────────────────────────────────────────────

class TestHandleEvent:
    def test_event_forwarded_to_current_scene(self):
        sm = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        event = MagicMock()
        sm.handle_event(event)
        scene.handle_event.assert_called_once_with(event)

    def test_event_blocked_during_transition(self):
        sm = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        tr = _FakeTransitionBase()   # is_done=False por padrão
        sm._transition = tr
        sm.handle_event(MagicMock())
        scene.handle_event.assert_not_called()

    def test_event_forwarded_after_transition_done(self):
        sm = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        tr = _FakeTransitionBase()
        tr.is_done = True
        sm._transition = tr
        event = MagicMock()
        sm.handle_event(event)
        scene.handle_event.assert_called_once_with(event)


# ─────────────────────────────────────────────────────────────────
# TestLoadWithTransition
# ─────────────────────────────────────────────────────────────────

class TestLoadWithTransition:
    def test_transition_stored(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        tr = make_transition(should_swap_after=0)
        new_scene = make_scene()
        sm.load(new_scene, transition=tr)
        assert sm._transition is tr

    def test_pending_scene_set(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        tr = make_transition(should_swap_after=99)  # não dispara no setup
        new_scene = make_scene()
        sm.load(new_scene, transition=tr)
        assert sm._pending_scene is new_scene

    def test_scene_swaps_when_should_swap(self):
        sm = SceneManager.instance()
        initial = make_scene("Initial")
        sm.load(initial)
        tr = make_transition(should_swap_after=0)
        new_scene = make_scene("New")
        sm.load(new_scene, transition=tr)
        # 1ª chamada a update: _update_count=1 > 0, should_swap=True
        sm.update(0.016)
        assert sm.current is new_scene

    def test_transition_cleared_when_done(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        tr = make_transition(should_swap_after=0)
        sm.load(make_scene(), transition=tr)
        sm.update(0.016)  # swap
        sm.update(0.016)  # done
        assert sm._transition is None


# ─────────────────────────────────────────────────────────────────
# TestPushWithTransition
# ─────────────────────────────────────────────────────────────────

class TestPushWithTransition:
    def test_push_transition_adds_scene_on_swap(self):
        sm = SceneManager.instance()
        sm.load(make_scene("Base"))
        tr = make_transition(should_swap_after=0)
        top = make_scene("Top")
        sm.push(top, transition=tr)
        sm.update(0.016)
        assert sm.current is top
        assert sm.stack_depth == 2

    def test_push_transition_does_not_clear_stack(self):
        sm = SceneManager.instance()
        base = make_scene("Base")
        sm.load(base)
        tr = make_transition(should_swap_after=0)
        sm.push(make_scene("Top"), transition=tr)
        sm.update(0.016)
        assert sm.stack_depth == 2


# ─────────────────────────────────────────────────────────────────
# TestPopWithTransition
# ─────────────────────────────────────────────────────────────────

class TestPopWithTransition:
    def test_pop_transition_removes_top(self):
        sm = SceneManager.instance()
        base = make_scene("Base")
        sm.load(base)
        sm.push(make_scene("Top"))
        tr = make_transition(should_swap_after=0)
        sm.pop(transition=tr)
        sm.update(0.016)
        assert sm.stack_depth == 1
        assert sm.current is base

    def test_pop_on_single_with_transition_does_nothing(self):
        sm = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        tr = make_transition(should_swap_after=0)
        sm.pop(transition=tr)   # pilha com 1 — ignorado silenciosamente
        assert sm.stack_depth == 1


# ─────────────────────────────────────────────────────────────────
# TestCallbacks
# ─────────────────────────────────────────────────────────────────

class TestCallbacks:
    def test_on_transition_start_called(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        cb = MagicMock()
        sm.on_transition_start = cb
        tr = make_transition(should_swap_after=99)
        new_scene = make_scene("Target")
        sm.load(new_scene, transition=tr)
        cb.assert_called_once_with("Target")

    def test_on_transition_end_called_when_done(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        cb = MagicMock()
        sm.on_transition_end = cb
        tr = make_transition(should_swap_after=0)
        sm.load(make_scene("Final"), transition=tr)
        sm.update(0.016)   # swap
        sm.update(0.016)   # done → callback
        cb.assert_called_once()

    def test_no_callback_no_error(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        tr = make_transition(should_swap_after=0)
        sm.load(make_scene(), transition=tr)
        sm.update(0.016)
        sm.update(0.016)   # não deve levantar exceção


# ─────────────────────────────────────────────────────────────────
# TestUpdateDraw
# ─────────────────────────────────────────────────────────────────

class TestUpdateDraw:
    def test_update_calls_scene_update(self):
        sm = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        sm.update(0.016)
        scene.update.assert_called_once_with(0.016)

    def test_update_no_scene_no_error(self):
        sm = SceneManager.instance()
        sm.update(0.016)  # stack vazio — deve ser silencioso

    def test_draw_calls_scene_draw(self):
        sm = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        screen = pg_mock.Surface((800, 600))
        sm.draw(screen)
        scene.draw.assert_called_once_with(screen)

    def test_draw_no_scene_no_error(self):
        sm = SceneManager.instance()
        sm.draw(pg_mock.Surface((800, 600)))


# ─────────────────────────────────────────────────────────────────
# TestRunPhysics
# ─────────────────────────────────────────────────────────────────

class TestRunPhysics:
    def test_run_physics_called_on_update(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        box_mock    = MagicMock()
        circle_mock = MagicMock()
        collider_mod = MagicMock()
        collider_mod.BoxCollider    = box_mock
        collider_mod.CircleCollider = circle_mock
        with patch.dict(sys.modules, {"engine.physics.collider": collider_mod}):
            sm.update(0.016)
        box_mock.check_all.assert_called_once()
        circle_mock.check_all.assert_called_once()

    def test_run_physics_silences_exceptions(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        broken_mod = MagicMock()
        broken_mod.BoxCollider.check_all.side_effect = RuntimeError("boom")
        broken_mod.CircleCollider = MagicMock()
        with patch.dict(sys.modules, {"engine.physics.collider": broken_mod}):
            sm.update(0.016)  # não deve propagar a exceção


# ─────────────────────────────────────────────────────────────────
# TestDoSwapLoadCleanup
# ─────────────────────────────────────────────────────────────────

class TestDoSwapLoadCleanup:
    def test_do_swap_load_clears_collider_registry(self):
        sm = SceneManager.instance()
        box_mock    = MagicMock()
        circle_mock = MagicMock()
        box_mock._scene_tilemaps             = {"x": 1}
        box_mock._scene_tilemap_components   = {"x": 1}
        box_mock._registry                   = ["a"]
        circle_mock._registry                = ["b"]
        collider_mod = MagicMock()
        collider_mod.BoxCollider    = box_mock
        collider_mod.CircleCollider = circle_mock
        with patch.dict(sys.modules, {"engine.physics.collider": collider_mod}):
            sm._do_swap_load(make_scene())
        assert box_mock._registry == []
        assert circle_mock._registry == []

    def test_do_swap_load_stops_music(self):
        sm = SceneManager.instance()
        audio_mock = MagicMock()
        audio_mod  = MagicMock()
        audio_mod.AudioManager = audio_mock
        collider_mod = MagicMock()
        collider_mod.BoxCollider    = MagicMock()
        collider_mod.CircleCollider = MagicMock()
        with patch.dict(sys.modules, {
            "engine.physics.collider": collider_mod,
            "engine.audio": audio_mod,
        }):
            sm._do_swap_load(make_scene())
        audio_mock.stop_music.assert_called_once()
        audio_mock.unload_cache.assert_called_once()

    def test_repr_contains_class_name(self):
        sm = SceneManager.instance()
        sm.load(make_scene("MyScene"))
        r = repr(sm)
        assert "MyScene" in r
        assert "depth=1" in r
