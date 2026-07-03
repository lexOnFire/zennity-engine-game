"""
tests/core/test_scene_manager.py
─────────────────────────────────────────────────────────────────
Testes unitários do SceneManager.

Estratégia de isolamento:
  - pygame NÃO é inicializado.
  - engine/__init__.py executa imports pesados quando qualquer submódulo
    de `engine` é carregado. Para evitar isso, TODOS os módulos do
    pacote `engine` são inseridos em sys.modules como stubs ANTES de
    qualquer `import engine.*`.
  - Stubs que representam pacotes (diretórios) precisam de __path__=[]
    para que o Python os trate como pacote e permita `from pkg.sub import X`.
  - SceneManager.reset() em autouse fixture garante singleton limpo.
"""
from __future__ import annotations

import sys
import os
import types
from unittest.mock import MagicMock

import pytest


# ─────────────────────────────────────────────────────────────────
# Helpers para criar stubs de módulo e pacote
# ─────────────────────────────────────────────────────────────────

def _mod(name: str, is_package: bool = False, **attrs):
    """
    Cria e registra um stub de módulo em sys.modules.
    is_package=True define __path__=[] para que Python aceite
    `from <name>.<sub> import X` sem tentar carregar do disco.
    """
    m = types.ModuleType(name)
    if is_package:
        m.__path__ = []          # marca como pacote
        m.__package__ = name
    else:
        m.__package__ = name.rsplit(".", 1)[0] if "." in name else name
    m.__spec__ = None
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


# ─────────────────────────────────────────────────────────────────
# pygame stubs
# ─────────────────────────────────────────────────────────────────

class _FakeSurface:
    def __init__(self, size=(800, 600)):
        self.size = size
    def get_size(self):
        return self.size

_pg = MagicMock()
_pg.Surface = _FakeSurface

for _name in (
    "pygame", "pygame.mixer", "pygame.font",
    "pygame.image", "pygame.display", "pygame.event",
    "pygame.transform", "pygame.draw",
):
    sys.modules.setdefault(_name, _pg)


# ─────────────────────────────────────────────────────────────────
# Stubs de transições
# ─────────────────────────────────────────────────────────────────

class _Phase:
    OUT = "OUT"; SWAP = "SWAP"; IN = "IN"; DONE = "DONE"


class _FakeTransitionBase:
    def __init__(self):
        self.phase = _Phase.OUT
        self.is_done = False
        self.should_swap = False
        self.snapshot_out = None
        self.snapshot_in = None
    def update(self, dt): pass
    def draw(self, screen): pass


_mod("engine.transitions",
    Transition=_FakeTransitionBase,
    TransitionPhase=_Phase,
    FadeTransition=MagicMock(),
    SlideTransition=MagicMock(),
    SlideDirection=MagicMock(),
    WipeTransition=MagicMock(),
    CrossfadeTransition=MagicMock(),
)


# ─────────────────────────────────────────────────────────────────
# UIManager mock (usado diretamente por SceneManager)
# ─────────────────────────────────────────────────────────────────

_ui_manager_mock = MagicMock()
_mod("engine.ui", is_package=True,
    UIElement=MagicMock(), Anchor=MagicMock(), Pivot=MagicMock(),
    Label=MagicMock(), Button=MagicMock(), UIImage=MagicMock(),
    ProgressBar=MagicMock(), Panel=MagicMock(), UICanvas=MagicMock(),
    UIManager=_ui_manager_mock,
)
_mod("engine.ui.ui_manager", UIManager=_ui_manager_mock)


# ─────────────────────────────────────────────────────────────────
# Stubs de todos os submódulos de engine.*
# (engine/__init__.py importa todos eles ao ser carregado)
# ─────────────────────────────────────────────────────────────────

_box_mock    = MagicMock()
_circle_mock = MagicMock()
_box_mock._scene_tilemaps           = {}
_box_mock._scene_tilemap_components = {}
_box_mock._registry                 = []
_circle_mock._registry              = []

_mod("engine.physics", is_package=True,
    BoxCollider=_box_mock, CircleCollider=_circle_mock,
    CollisionInfo=MagicMock())
_mod("engine.physics.collider",
    BoxCollider=_box_mock, CircleCollider=_circle_mock,
    CollisionInfo=MagicMock())
_mod("engine.physics.rigidbody",        RigidBody=MagicMock())
_mod("engine.physics.tilemap_collider", TilemapCollider=MagicMock())

_mod("engine.tilemap", is_package=True,
    TileMap=MagicMock(), TilemapRenderer=MagicMock(), TileMapLoader=MagicMock())
_mod("engine.tilemap.tilemap",
    TileMap=MagicMock(), TilemapRenderer=MagicMock())
_mod("engine.tilemap.tilemap_loader",   TileMapLoader=MagicMock())

_mod("engine.graphics", is_package=True, Camera2D=MagicMock())
_mod("engine.graphics.camera2d",        Camera2D=MagicMock())
_mod("engine.graphics.particles",
    Particle=MagicMock(), ParticleSystem=MagicMock())

_audio_mock = MagicMock()
_mod("engine.audio", AudioManager=_audio_mock)

# engine.core como PACOTE (is_package=True é obrigatório)
# para que `from engine.core.scene_manager import ...` funcione
_mod("engine.core", is_package=True,
    Engine=MagicMock(), Scene=MagicMock(), SceneManager=None)

_mod("engine.core.scene",       Scene=MagicMock())
_mod("engine.core.engine",      Engine=MagicMock())
_mod("engine.core.game_object", GameObject=MagicMock())
_mod("engine.core.component",   Component=MagicMock())
_mod("engine.core.system",      System=MagicMock())
_mod("engine.core.event_bus",   EventBus=MagicMock())
_mod("engine.core.application", Application=MagicMock())
_mod("engine.core.logger",      Logger=MagicMock())
_mod("engine.core.time",        Time=MagicMock())

# engine (pacote raiz) — evita que engine/__init__.py real seja executado
_mod("engine", is_package=True,
    Engine=MagicMock(), Scene=MagicMock(), SceneManager=None,
    Transition=_FakeTransitionBase, FadeTransition=MagicMock(),
    SlideTransition=MagicMock(), SlideDirection=MagicMock(),
    WipeTransition=MagicMock(), CrossfadeTransition=MagicMock(),
    TileMap=MagicMock(), TilemapRenderer=MagicMock(), TileMapLoader=MagicMock(),
    Camera2D=MagicMock(), RigidBody=MagicMock(),
    BoxCollider=_box_mock, CircleCollider=_circle_mock,
    CollisionInfo=MagicMock(), TilemapCollider=MagicMock(),
    UIElement=MagicMock(), Anchor=MagicMock(), Pivot=MagicMock(),
    Label=MagicMock(), Button=MagicMock(), UIImage=MagicMock(),
    ProgressBar=MagicMock(), Panel=MagicMock(), UICanvas=MagicMock(),
    UIManager=_ui_manager_mock,
    Particle=MagicMock(), ParticleSystem=MagicMock(),
)


# ─────────────────────────────────────────────────────────────────
# Import do módulo real — seguro agora
# ─────────────────────────────────────────────────────────────────

import importlib as _il
# Remover o stub de engine.core.scene_manager para que o arquivo real seja carregado
sys.modules.pop("engine.core.scene_manager", None)
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
        assert SceneManager.instance().stack_depth == 0

    def test_new_instance_no_transition(self):
        assert SceneManager.instance()._transition is None


# ─────────────────────────────────────────────────────────────────
class TestLoad:
    def test_load_sets_current(self):
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        assert sm.current is s

    def test_load_calls_scene_start(self):
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        s.start.assert_called_once()

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
        sm._stack.append(make_scene())
        sm.load(make_scene())
        assert sm.stack_depth == 1

    def test_load_assigns_engine_to_scene(self):
        sm  = SceneManager.instance()
        eng = MagicMock()
        sm.bind(eng)
        s   = make_scene()
        sm.load(s)
        assert s.engine is eng

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
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        sm.pop()
        assert sm.stack_depth == 1
        assert sm.current is s

    def test_pop_calls_ui_setup_if_present(self):
        sm   = SceneManager.instance()
        base = make_scene()
        sm.load(base)
        sm.push(make_scene())
        sm.pop()
        base._ui_setup.assert_called_once()

    def test_multiple_push_pop_restores_order(self):
        sm      = SceneManager.instance()
        a, b, c = make_scene("A"), make_scene("B"), make_scene("C")
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
        assert SceneManager.instance().current is None

    def test_stack_depth_zero_initially(self):
        assert SceneManager.instance().stack_depth == 0

    def test_is_transitioning_false_initially(self):
        assert SceneManager.instance().is_transitioning is False

    def test_is_transitioning_true_during_active_transition(self):
        sm = SceneManager.instance()
        tr = _FakeTransitionBase()
        sm._transition = tr   # is_done=False por padrão
        assert sm.is_transitioning is True

    def test_is_transitioning_false_when_done(self):
        sm = SceneManager.instance()
        tr = _FakeTransitionBase()
        tr.is_done = True
        sm._transition = tr
        assert sm.is_transitioning is False


# ─────────────────────────────────────────────────────────────────
class TestBind:
    def test_bind_sets_engine(self):
        sm  = SceneManager.instance()
        eng = MagicMock()
        sm.bind(eng)
        assert sm._engine is eng

    def test_bind_patches_change_scene(self):
        sm  = SceneManager.instance()
        eng = MagicMock()
        sm.bind(eng)
        assert eng.change_scene is sm.load


# ─────────────────────────────────────────────────────────────────
class TestHandleEvent:
    def test_event_forwarded_to_current_scene(self):
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        ev = MagicMock()
        sm.handle_event(ev)
        s.handle_event.assert_called_once_with(ev)

    def test_event_blocked_during_transition(self):
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        sm._transition = _FakeTransitionBase()   # is_done=False
        sm.handle_event(MagicMock())
        s.handle_event.assert_not_called()

    def test_event_forwarded_after_transition_done(self):
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        tr = _FakeTransitionBase()
        tr.is_done = True
        sm._transition = tr
        ev = MagicMock()
        sm.handle_event(ev)
        s.handle_event.assert_called_once_with(ev)


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
        new_scene = make_scene()
        sm.load(new_scene, transition=make_transition(should_swap_after=99))
        assert sm._pending_scene is new_scene

    def test_scene_swaps_when_should_swap(self):
        sm        = SceneManager.instance()
        sm.load(make_scene("Initial"))
        new_scene = make_scene("New")
        sm.load(new_scene, transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        assert sm.current is new_scene

    def test_transition_cleared_when_done(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm.load(make_scene(), transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        sm.update(0.016)
        assert sm._transition is None


# ─────────────────────────────────────────────────────────────────
class TestPushWithTransition:
    def test_push_transition_adds_scene_on_swap(self):
        sm  = SceneManager.instance()
        sm.load(make_scene("Base"))
        top = make_scene("Top")
        sm.push(top, transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        assert sm.current is top
        assert sm.stack_depth == 2

    def test_push_transition_does_not_clear_stack(self):
        sm = SceneManager.instance()
        sm.load(make_scene("Base"))
        sm.push(make_scene("Top"), transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        assert sm.stack_depth == 2


# ─────────────────────────────────────────────────────────────────
class TestPopWithTransition:
    def test_pop_transition_removes_top(self):
        sm   = SceneManager.instance()
        base = make_scene("Base")
        sm.load(base)
        sm.push(make_scene("Top"))
        sm.pop(transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        assert sm.stack_depth == 1
        assert sm.current is base

    def test_pop_on_single_with_transition_does_nothing(self):
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        sm.pop(transition=make_transition())
        assert sm.stack_depth == 1


# ─────────────────────────────────────────────────────────────────
class TestCallbacks:
    def test_on_transition_start_called(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        cb = MagicMock()
        sm.on_transition_start = cb
        sm.load(make_scene("Target"),
                transition=make_transition(should_swap_after=99))
        cb.assert_called_once_with("Target")

    def test_on_transition_end_called_when_done(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        cb = MagicMock()
        sm.on_transition_end = cb
        sm.load(make_scene("Final"),
                transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        sm.update(0.016)
        cb.assert_called_once()

    def test_no_callback_no_error(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm.load(make_scene(), transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        sm.update(0.016)


# ─────────────────────────────────────────────────────────────────
class TestUpdateDraw:
    def test_update_calls_scene_update(self):
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        sm.update(0.016)
        s.update.assert_called_once_with(0.016)

    def test_update_no_scene_no_error(self):
        SceneManager.instance().update(0.016)

    def test_draw_calls_scene_draw(self):
        sm     = SceneManager.instance()
        s      = make_scene()
        sm.load(s)
        screen = _FakeSurface()
        sm.draw(screen)
        s.draw.assert_called_once_with(screen)

    def test_draw_no_scene_no_error(self):
        SceneManager.instance().draw(_FakeSurface())


# ─────────────────────────────────────────────────────────────────
class TestRunPhysics:
    def test_run_physics_called_on_update(self):
        from unittest.mock import patch as _patch
        sm          = SceneManager.instance()
        sm.load(make_scene())
        box         = MagicMock()
        circle      = MagicMock()
        fake_mod    = types.ModuleType("engine.physics.collider")
        fake_mod.BoxCollider    = box
        fake_mod.CircleCollider = circle
        with _patch.dict(sys.modules, {"engine.physics.collider": fake_mod}):
            sm.update(0.016)
        box.check_all.assert_called_once()
        circle.check_all.assert_called_once()

    def test_run_physics_silences_exceptions(self):
        from unittest.mock import patch as _patch
        sm       = SceneManager.instance()
        sm.load(make_scene())
        broken   = MagicMock()
        broken.check_all.side_effect = RuntimeError("boom")
        fake_mod = types.ModuleType("engine.physics.collider")
        fake_mod.BoxCollider    = broken
        fake_mod.CircleCollider = MagicMock()
        with _patch.dict(sys.modules, {"engine.physics.collider": fake_mod}):
            sm.update(0.016)


# ─────────────────────────────────────────────────────────────────
class TestDoSwapLoadCleanup:
    def test_do_swap_load_clears_collider_registry(self):
        from unittest.mock import patch as _patch
        sm          = SceneManager.instance()
        box         = MagicMock()
        circle      = MagicMock()
        box._scene_tilemaps           = {"x": 1}
        box._scene_tilemap_components = {"x": 1}
        box._registry                 = ["a"]
        circle._registry              = ["b"]
        fake_mod = types.ModuleType("engine.physics.collider")
        fake_mod.BoxCollider    = box
        fake_mod.CircleCollider = circle
        with _patch.dict(sys.modules, {"engine.physics.collider": fake_mod}):
            sm._do_swap_load(make_scene())
        assert box._registry    == []
        assert circle._registry == []

    def test_do_swap_load_stops_music(self):
        from unittest.mock import patch as _patch
        sm         = SceneManager.instance()
        audio      = MagicMock()
        audio_mod  = types.ModuleType("engine.audio")
        audio_mod.AudioManager = audio
        col_mod    = types.ModuleType("engine.physics.collider")
        col_mod.BoxCollider    = MagicMock()
        col_mod.CircleCollider = MagicMock()
        with _patch.dict(sys.modules, {
            "engine.physics.collider": col_mod,
            "engine.audio":            audio_mod,
        }):
            sm._do_swap_load(make_scene())
        audio.stop_music.assert_called_once()
        audio.unload_cache.assert_called_once()

    def test_repr_contains_class_name(self):
        sm = SceneManager.instance()
        sm.load(make_scene("MyScene"))
        r  = repr(sm)
        assert "MyScene" in r
        assert "depth=1" in r
