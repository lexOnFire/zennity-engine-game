"""
tests/core/test_scene_manager.py
─────────────────────────────────────────────────────────────────
Testes unitários do SceneManager.

Estratégia de isolamento:
  - pygame NÃO é inicializado.
  - engine/__init__.py executa imports pesados no momento em que qualquer
    submódulo de `engine` é importado.  Para evitar isso, todos os
    submódulos relevantes são inseridos em sys.modules ANTES de qualquer
    `import engine.*`.
  - SceneManager.reset() em autouse fixture garante singleton limpo.
"""
from __future__ import annotations

import sys
import types
import importlib
from unittest.mock import MagicMock

import pytest


# ─────────────────────────────────────────────────────────────────
# Stub de pygame
# ─────────────────────────────────────────────────────────────────

class _FakeSurface:
    def __init__(self, size=(800, 600)):
        self.size = size
    def get_size(self):
        return self.size

_pygame = MagicMock()
_pygame.Surface = _FakeSurface

for _mod in (
    "pygame", "pygame.mixer", "pygame.font",
    "pygame.image", "pygame.display", "pygame.event",
    "pygame.transform", "pygame.draw",
):
    sys.modules.setdefault(_mod, _pygame)


# ─────────────────────────────────────────────────────────────────
# Stubs de TransitionPhase e transições
# ─────────────────────────────────────────────────────────────────

class _Phase:
    OUT  = "OUT"
    SWAP = "SWAP"
    IN   = "IN"
    DONE = "DONE"


class _FakeTransitionBase:
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


class _FakeSlideDirection:
    LEFT = "LEFT"; RIGHT = "RIGHT"; UP = "UP"; DOWN = "DOWN"


_transitions_mod = types.ModuleType("engine.transitions")
_transitions_mod.Transition       = _FakeTransitionBase
_transitions_mod.TransitionPhase  = _Phase
_transitions_mod.FadeTransition   = _FakeFadeTransition
_transitions_mod.SlideTransition  = MagicMock()
_transitions_mod.SlideDirection   = _FakeSlideDirection
_transitions_mod.WipeTransition   = MagicMock()
_transitions_mod.CrossfadeTransition = MagicMock()
sys.modules["engine.transitions"] = _transitions_mod


# ─────────────────────────────────────────────────────────────────
# Stubs de todos os submódulos importados por engine/__init__.py
# Sem isso, o import de engine.core.scene_manager aciona engine/__init__.py
# que tenta importar pygame real, colliders, ui, etc.
# ─────────────────────────────────────────────────────────────────

_ui_manager_mock = MagicMock()

def _stub(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules.setdefault(name, m)
    return m

# engine.ui
_ui_mod = _stub("engine.ui",
    UIElement=MagicMock(), Anchor=MagicMock(), Pivot=MagicMock(),
    Label=MagicMock(), Button=MagicMock(), UIImage=MagicMock(),
    ProgressBar=MagicMock(), Panel=MagicMock(), UICanvas=MagicMock(),
    UIManager=_ui_manager_mock,
)
_stub("engine.ui.ui_manager", UIManager=_ui_manager_mock)

# engine.physics.*
_box_mock    = MagicMock()
_circle_mock = MagicMock()
_box_mock._scene_tilemaps           = {}
_box_mock._scene_tilemap_components = {}
_box_mock._registry                 = []
_circle_mock._registry              = []
_stub("engine.physics",
    BoxCollider=_box_mock, CircleCollider=_circle_mock,
    CollisionInfo=MagicMock())
_stub("engine.physics.collider",
    BoxCollider=_box_mock, CircleCollider=_circle_mock,
    CollisionInfo=MagicMock())
_stub("engine.physics.rigidbody",   RigidBody=MagicMock())
_stub("engine.physics.tilemap_collider", TilemapCollider=MagicMock())

# engine.tilemap.*
_stub("engine.tilemap",
    TileMap=MagicMock(), TilemapRenderer=MagicMock(), TileMapLoader=MagicMock())
_stub("engine.tilemap.tilemap",
    TileMap=MagicMock(), TilemapRenderer=MagicMock())
_stub("engine.tilemap.tilemap_loader", TileMapLoader=MagicMock())

# engine.graphics.*
_stub("engine.graphics",  Camera2D=MagicMock())
_stub("engine.graphics.camera2d",   Camera2D=MagicMock())
_stub("engine.graphics.particles",
    Particle=MagicMock(), ParticleSystem=MagicMock())

# engine.audio
_audio_mock = MagicMock()
_stub("engine.audio", AudioManager=_audio_mock)

# engine.core.*  (shims que reexportam do subpacote)
_stub("engine.core.scene",        Scene=MagicMock())
_stub("engine.core.engine",       Engine=MagicMock())
_stub("engine.core.game_object",  GameObject=MagicMock())
_stub("engine.core.component",    Component=MagicMock())
_stub("engine.core.system",       System=MagicMock())
_stub("engine.core.event_bus",    EventBus=MagicMock())
_stub("engine.core.application",  Application=MagicMock())
_stub("engine.core.logger",       Logger=MagicMock())
_stub("engine.core.time",         Time=MagicMock())

# engine.core.__init__ precisa de Engine e Scene
_engine_core_init = types.ModuleType("engine.core")
_engine_core_init.Engine       = MagicMock()
_engine_core_init.Scene        = MagicMock()
_engine_core_init.SceneManager = None   # será preenchido após import real
sys.modules.setdefault("engine.core", _engine_core_init)

# engine.__init__ completo
_engine_init = types.ModuleType("engine")
for _attr in (
    "Engine", "Scene", "SceneManager",
    "Transition", "FadeTransition", "SlideTransition", "SlideDirection",
    "WipeTransition", "CrossfadeTransition",
    "TileMap", "TilemapRenderer", "TileMapLoader",
    "Camera2D", "RigidBody",
    "BoxCollider", "CircleCollider", "CollisionInfo", "TilemapCollider",
    "UIElement", "Anchor", "Pivot", "Label", "Button", "UIImage",
    "ProgressBar", "Panel", "UICanvas", "UIManager",
    "Particle", "ParticleSystem",
):
    setattr(_engine_init, _attr, MagicMock())
sys.modules.setdefault("engine", _engine_init)


# ─────────────────────────────────────────────────────────────────
# Agora é seguro importar o módulo real
# ─────────────────────────────────────────────────────────────────

from engine.core.scene_manager import SceneManager  # noqa: E402


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def make_scene(name="Scene"):
    s = MagicMock()
    s.__class__.__name__ = name
    s.start        = MagicMock()
    s.update       = MagicMock()
    s.draw         = MagicMock()
    s.handle_event = MagicMock()
    s._ui_setup    = MagicMock()
    return s


def make_transition(should_swap_after: int = 0):
    """Transição que dispara should_swap após N chamadas a update()."""
    tr = _FakeTransitionBase()
    tr._update_count = 0
    tr._swap_after   = should_swap_after

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
    SceneManager.reset()
    _ui_manager_mock.reset.reset_mock()
    yield
    SceneManager.reset()


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
class TestLoad:
    def test_load_sets_current(self):
        sm    = SceneManager.instance()
        scene = make_scene()
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
        sm   = SceneManager.instance()
        a, b = make_scene("A"), make_scene("B")
        sm.load(a)
        sm.load(b)
        assert sm.current is b
        assert sm.stack_depth == 1

    def test_load_clears_stack_completely(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm._stack.append(make_scene())  # força 2 cenas
        sm.load(make_scene())
        assert sm.stack_depth == 1

    def test_load_assigns_engine_to_scene(self):
        sm     = SceneManager.instance()
        engine = MagicMock()
        sm.bind(engine)
        scene  = make_scene()
        sm.load(scene)
        assert scene.engine is engine

    def test_load_calls_ui_manager_reset(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        _ui_manager_mock.reset.assert_called()


# ─────────────────────────────────────────────────────────────────
class TestPushPop:
    def test_push_increases_depth(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm.push(make_scene())
        assert sm.stack_depth == 2

    def test_push_changes_current(self):
        sm  = SceneManager.instance()
        sm.load(make_scene("Base"))
        top = make_scene("Top")
        sm.push(top)
        assert sm.current is top

    def test_push_calls_start_on_new_scene(self):
        sm  = SceneManager.instance()
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
        sm   = SceneManager.instance()
        base = make_scene("Base")
        sm.load(base)
        sm.push(make_scene("Top"))
        sm.pop()
        assert sm.current is base

    def test_pop_on_single_scene_does_nothing(self):
        sm    = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        sm.pop()
        assert sm.stack_depth == 1
        assert sm.current is scene

    def test_pop_calls_ui_setup_if_present(self):
        sm   = SceneManager.instance()
        base = make_scene()
        sm.load(base)
        sm.push(make_scene())
        sm.pop()
        base._ui_setup.assert_called_once()

    def test_multiple_push_pop_restores_order(self):
        sm       = SceneManager.instance()
        a, b, c  = make_scene("A"), make_scene("B"), make_scene("C")
        sm.load(a)
        sm.push(b)
        sm.push(c)
        sm.pop()
        sm.pop()
        assert sm.current is a
        assert sm.stack_depth == 1


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
        sm    = SceneManager.instance()
        tr    = _FakeTransitionBase()
        tr.is_done = False
        sm._transition = tr
        assert sm.is_transitioning is True

    def test_is_transitioning_false_when_done(self):
        sm    = SceneManager.instance()
        tr    = _FakeTransitionBase()
        tr.is_done = True
        sm._transition = tr
        assert sm.is_transitioning is False


# ─────────────────────────────────────────────────────────────────
class TestBind:
    def test_bind_sets_engine(self):
        sm     = SceneManager.instance()
        engine = MagicMock()
        sm.bind(engine)
        assert sm._engine is engine

    def test_bind_patches_change_scene(self):
        sm     = SceneManager.instance()
        engine = MagicMock()
        sm.bind(engine)
        assert engine.change_scene is sm.load


# ─────────────────────────────────────────────────────────────────
class TestHandleEvent:
    def test_event_forwarded_to_current_scene(self):
        sm    = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        event = MagicMock()
        sm.handle_event(event)
        scene.handle_event.assert_called_once_with(event)

    def test_event_blocked_during_transition(self):
        sm    = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        tr         = _FakeTransitionBase()
        tr.is_done = False
        sm._transition = tr
        sm.handle_event(MagicMock())
        scene.handle_event.assert_not_called()

    def test_event_forwarded_after_transition_done(self):
        sm    = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        tr         = _FakeTransitionBase()
        tr.is_done = True
        sm._transition = tr
        event = MagicMock()
        sm.handle_event(event)
        scene.handle_event.assert_called_once_with(event)


# ─────────────────────────────────────────────────────────────────
class TestLoadWithTransition:
    def test_transition_stored(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        tr = make_transition(should_swap_after=99)
        sm.load(make_scene(), transition=tr)
        assert sm._transition is tr

    def test_pending_scene_set(self):
        sm        = SceneManager.instance()
        sm.load(make_scene())
        tr        = make_transition(should_swap_after=99)
        new_scene = make_scene()
        sm.load(new_scene, transition=tr)
        assert sm._pending_scene is new_scene

    def test_scene_swaps_when_should_swap(self):
        sm        = SceneManager.instance()
        sm.load(make_scene("Initial"))
        tr        = make_transition(should_swap_after=0)
        new_scene = make_scene("New")
        sm.load(new_scene, transition=tr)
        sm.update(0.016)   # 1ª chamada: should_swap=True
        assert sm.current is new_scene

    def test_transition_cleared_when_done(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        tr = make_transition(should_swap_after=0)
        sm.load(make_scene(), transition=tr)
        sm.update(0.016)   # swap
        sm.update(0.016)   # done
        assert sm._transition is None


# ─────────────────────────────────────────────────────────────────
class TestPushWithTransition:
    def test_push_transition_adds_scene_on_swap(self):
        sm  = SceneManager.instance()
        sm.load(make_scene("Base"))
        tr  = make_transition(should_swap_after=0)
        top = make_scene("Top")
        sm.push(top, transition=tr)
        sm.update(0.016)
        assert sm.current is top
        assert sm.stack_depth == 2

    def test_push_transition_does_not_clear_stack(self):
        sm   = SceneManager.instance()
        base = make_scene("Base")
        sm.load(base)
        tr   = make_transition(should_swap_after=0)
        sm.push(make_scene("Top"), transition=tr)
        sm.update(0.016)
        assert sm.stack_depth == 2


# ─────────────────────────────────────────────────────────────────
class TestPopWithTransition:
    def test_pop_transition_removes_top(self):
        sm   = SceneManager.instance()
        base = make_scene("Base")
        sm.load(base)
        sm.push(make_scene("Top"))
        tr   = make_transition(should_swap_after=0)
        sm.pop(transition=tr)
        sm.update(0.016)
        assert sm.stack_depth == 1
        assert sm.current is base

    def test_pop_on_single_with_transition_does_nothing(self):
        sm    = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        sm.pop(transition=make_transition())
        assert sm.stack_depth == 1


# ─────────────────────────────────────────────────────────────────
class TestCallbacks:
    def test_on_transition_start_called(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        cb = MagicMock()
        sm.on_transition_start = cb
        tr = make_transition(should_swap_after=99)
        sm.load(make_scene("Target"), transition=tr)
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
class TestUpdateDraw:
    def test_update_calls_scene_update(self):
        sm    = SceneManager.instance()
        scene = make_scene()
        sm.load(scene)
        sm.update(0.016)
        scene.update.assert_called_once_with(0.016)

    def test_update_no_scene_no_error(self):
        sm = SceneManager.instance()
        sm.update(0.016)

    def test_draw_calls_scene_draw(self):
        sm     = SceneManager.instance()
        scene  = make_scene()
        sm.load(scene)
        screen = _FakeSurface()
        sm.draw(screen)
        scene.draw.assert_called_once_with(screen)

    def test_draw_no_scene_no_error(self):
        sm = SceneManager.instance()
        sm.draw(_FakeSurface())


# ─────────────────────────────────────────────────────────────────
class TestRunPhysics:
    def test_run_physics_called_on_update(self):
        import unittest.mock as _mock
        sm          = SceneManager.instance()
        sm.load(make_scene())
        box_mock    = MagicMock()
        circle_mock = MagicMock()
        collider_mod = types.ModuleType("engine.physics.collider")
        collider_mod.BoxCollider    = box_mock
        collider_mod.CircleCollider = circle_mock
        with _mock.patch.dict(sys.modules, {"engine.physics.collider": collider_mod}):
            sm.update(0.016)
        box_mock.check_all.assert_called_once()
        circle_mock.check_all.assert_called_once()

    def test_run_physics_silences_exceptions(self):
        import unittest.mock as _mock
        sm          = SceneManager.instance()
        sm.load(make_scene())
        broken_mod  = types.ModuleType("engine.physics.collider")
        broken_mock = MagicMock()
        broken_mock.check_all.side_effect = RuntimeError("boom")
        broken_mod.BoxCollider    = broken_mock
        broken_mod.CircleCollider = MagicMock()
        with _mock.patch.dict(sys.modules, {"engine.physics.collider": broken_mod}):
            sm.update(0.016)   # não deve propagar


# ─────────────────────────────────────────────────────────────────
class TestDoSwapLoadCleanup:
    def test_do_swap_load_clears_collider_registry(self):
        import unittest.mock as _mock
        sm          = SceneManager.instance()
        box_mock    = MagicMock()
        circle_mock = MagicMock()
        box_mock._scene_tilemaps           = {"x": 1}
        box_mock._scene_tilemap_components = {"x": 1}
        box_mock._registry                 = ["a"]
        circle_mock._registry              = ["b"]
        collider_mod = types.ModuleType("engine.physics.collider")
        collider_mod.BoxCollider    = box_mock
        collider_mod.CircleCollider = circle_mock
        with _mock.patch.dict(sys.modules, {"engine.physics.collider": collider_mod}):
            sm._do_swap_load(make_scene())
        assert box_mock._registry == []
        assert circle_mock._registry == []

    def test_do_swap_load_stops_music(self):
        import unittest.mock as _mock
        sm          = SceneManager.instance()
        audio_mock  = MagicMock()
        audio_mod   = types.ModuleType("engine.audio")
        audio_mod.AudioManager = audio_mock
        collider_mod = types.ModuleType("engine.physics.collider")
        collider_mod.BoxCollider    = MagicMock()
        collider_mod.CircleCollider = MagicMock()
        with _mock.patch.dict(sys.modules, {
            "engine.physics.collider": collider_mod,
            "engine.audio":            audio_mod,
        }):
            sm._do_swap_load(make_scene())
        audio_mock.stop_music.assert_called_once()
        audio_mock.unload_cache.assert_called_once()

    def test_repr_contains_class_name(self):
        sm = SceneManager.instance()
        sm.load(make_scene("MyScene"))
        r  = repr(sm)
        assert "MyScene" in r
        assert "depth=1" in r
