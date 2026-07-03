"""
tests/core/test_scene_manager.py
─────────────────────────────────────────────────────────────────
Testes unitários do SceneManager.

Estratégia de isolamento:
  - Todos os módulos pesados de `engine.*` são colocados em sys.modules
    como stubs ANTES de qualquer import real.
  - `engine.core` e `engine` precisam de __path__ apontando para o
    diretório físico real, caso contrário o Python não encontra
    engine/core/scene_manager.py no disco.
  - engine/core/scene_manager.py é carregado via importlib.util.spec_from_file_location
    para total controle, evitando que engine/__init__.py seja re-executado.
"""
from __future__ import annotations

import sys
import os
import types
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ─────────────────────────────────────────────────────────────────
# Localiza a raiz do projeto (onde engine/ existe)
# ─────────────────────────────────────────────────────────────────

_HERE       = Path(__file__).resolve().parent          # tests/core/
_TESTS_DIR  = _HERE.parent                             # tests/
_ROOT       = _TESTS_DIR.parent                        # raiz do projeto
_ENGINE_DIR = _ROOT / "engine"                         # engine/
_CORE_DIR   = _ENGINE_DIR / "core"                     # engine/core/
_SM_FILE    = _CORE_DIR / "scene_manager.py"           # arquivo real

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
for _n in ("pygame", "pygame.mixer", "pygame.font",
           "pygame.image", "pygame.display", "pygame.event",
           "pygame.transform", "pygame.draw"):
    sys.modules.setdefault(_n, _pg)

# ─────────────────────────────────────────────────────────────────
# Stubs de transições
# ─────────────────────────────────────────────────────────────────

class _Phase:
    OUT = "OUT"; SWAP = "SWAP"; IN = "IN"; DONE = "DONE"


class _FakeTransition:
    def __init__(self):
        self.phase        = _Phase.OUT
        self.is_done      = False
        self.should_swap  = False
        self.snapshot_out = None
        self.snapshot_in  = None
    def update(self, dt): pass
    def draw(self, screen): pass


_tr_mod = types.ModuleType("engine.transitions")
_tr_mod.Transition          = _FakeTransition
_tr_mod.TransitionPhase     = _Phase
_tr_mod.FadeTransition      = MagicMock()
_tr_mod.SlideTransition     = MagicMock()
_tr_mod.SlideDirection      = MagicMock()
_tr_mod.WipeTransition      = MagicMock()
_tr_mod.CrossfadeTransition = MagicMock()
sys.modules["engine.transitions"] = _tr_mod

# ─────────────────────────────────────────────────────────────────
# UIManager mock
# ─────────────────────────────────────────────────────────────────

_ui_manager_mock = MagicMock()

_ui_pkg = types.ModuleType("engine.ui")
_ui_pkg.__path__    = [str(_ENGINE_DIR / "ui")]
_ui_pkg.__package__ = "engine.ui"
_ui_pkg.UIManager   = _ui_manager_mock
sys.modules["engine.ui"] = _ui_pkg

_ui_mgr_mod = types.ModuleType("engine.ui.ui_manager")
_ui_mgr_mod.UIManager = _ui_manager_mock
sys.modules["engine.ui.ui_manager"] = _ui_mgr_mod

# ─────────────────────────────────────────────────────────────────
# Stubs de todos os outros submódulos que engine/__init__.py importa
# ─────────────────────────────────────────────────────────────────

def _fake_mod(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m

_box_mock    = MagicMock()
_circle_mock = MagicMock()
_box_mock._scene_tilemaps           = {}
_box_mock._scene_tilemap_components = {}
_box_mock._registry                 = []
_circle_mock._registry              = []
_audio_mock = MagicMock()

_fake_mod("engine.physics.collider",
          BoxCollider=_box_mock, CircleCollider=_circle_mock,
          CollisionInfo=MagicMock())
_fake_mod("engine.physics.rigidbody",        RigidBody=MagicMock())
_fake_mod("engine.physics.tilemap_collider", TilemapCollider=MagicMock())
_fake_mod("engine.tilemap.tilemap",
          TileMap=MagicMock(), TilemapRenderer=MagicMock())
_fake_mod("engine.tilemap.tilemap_loader",   TileMapLoader=MagicMock())
_fake_mod("engine.graphics.camera2d",        Camera2D=MagicMock())
_fake_mod("engine.graphics.particles",
          Particle=MagicMock(), ParticleSystem=MagicMock())
_fake_mod("engine.audio",                    AudioManager=_audio_mock)

# engine.core submódulos (folhas)
_fake_mod("engine.core.scene",       Scene=MagicMock())
_fake_mod("engine.core.engine",      Engine=MagicMock())
_fake_mod("engine.core.game_object", GameObject=MagicMock())
_fake_mod("engine.core.component",   Component=MagicMock())
_fake_mod("engine.core.system",      System=MagicMock())
_fake_mod("engine.core.event_bus",   EventBus=MagicMock())
_fake_mod("engine.core.application", Application=MagicMock())
_fake_mod("engine.core.logger",      Logger=MagicMock())
_fake_mod("engine.core.time",        Time=MagicMock())

# ─────────────────────────────────────────────────────────────────
# engine.core como PACOTE com __path__ real
# ─────────────────────────────────────────────────────────────────
# __path__ precisa apontar para o diretório físico para que
# Python encontre engine/core/scene_manager.py ao fazer o import.

_engine_core_pkg = types.ModuleType("engine.core")
_engine_core_pkg.__path__    = [str(_CORE_DIR)]   # ← caminho real no disco
_engine_core_pkg.__package__ = "engine.core"
_engine_core_pkg.Engine      = MagicMock()
_engine_core_pkg.Scene       = MagicMock()
sys.modules["engine.core"] = _engine_core_pkg

# engine (pacote raiz) também com __path__ real
_engine_pkg = types.ModuleType("engine")
_engine_pkg.__path__    = [str(_ENGINE_DIR)]      # ← caminho real
_engine_pkg.__package__ = "engine"
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
    setattr(_engine_pkg, _attr, MagicMock())
_engine_pkg.UIManager = _ui_manager_mock
sys.modules["engine"] = _engine_pkg

# ─────────────────────────────────────────────────────────────────
# Carrega engine/core/scene_manager.py diretamente do disco
# ─────────────────────────────────────────────────────────────────

_spec = importlib.util.spec_from_file_location(
    "engine.core.scene_manager",
    str(_SM_FILE),
)
_sm_module = importlib.util.module_from_spec(_spec)
sys.modules["engine.core.scene_manager"] = _sm_module
_spec.loader.exec_module(_sm_module)

SceneManager = _sm_module.SceneManager

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
    tr = _FakeTransition()
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


# ================================================================
# TESTES
# ================================================================

class TestSingleton:
    def test_instance_returns_same_object(self):
        assert SceneManager.instance() is SceneManager.instance()

    def test_reset_creates_new_instance(self):
        a = SceneManager.instance()
        SceneManager.reset()
        assert SceneManager.instance() is not a

    def test_reset_clears_inst(self):
        SceneManager.instance()
        SceneManager.reset()
        assert SceneManager._inst is None

    def test_new_instance_has_empty_stack(self):
        assert SceneManager.instance().stack_depth == 0

    def test_new_instance_no_transition(self):
        assert SceneManager.instance()._transition is None


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
        assert sm.current is b and sm.stack_depth == 1

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
        assert sm.stack_depth == 1 and sm.current is s

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
        sm.load(a); sm.push(b); sm.push(c)
        sm.pop();   sm.pop()
        assert sm.current is a and sm.stack_depth == 1


class TestStackProperties:
    def test_current_none_when_empty(self):
        assert SceneManager.instance().current is None

    def test_stack_depth_zero_initially(self):
        assert SceneManager.instance().stack_depth == 0

    def test_is_transitioning_false_initially(self):
        assert SceneManager.instance().is_transitioning is False

    def test_is_transitioning_true_during_active_transition(self):
        sm = SceneManager.instance()
        tr = _FakeTransition()   # is_done=False
        sm._transition = tr
        assert sm.is_transitioning is True

    def test_is_transitioning_false_when_done(self):
        sm = SceneManager.instance()
        tr = _FakeTransition()
        tr.is_done = True
        sm._transition = tr
        assert sm.is_transitioning is False


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
        sm._transition = _FakeTransition()
        sm.handle_event(MagicMock())
        s.handle_event.assert_not_called()

    def test_event_forwarded_after_transition_done(self):
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        tr = _FakeTransition(); tr.is_done = True
        sm._transition = tr
        ev = MagicMock()
        sm.handle_event(ev)
        s.handle_event.assert_called_once_with(ev)


class TestLoadWithTransition:
    def test_transition_stored(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        tr = make_transition(should_swap_after=99)
        sm.load(make_scene(), transition=tr)
        assert sm._transition is tr

    def test_pending_scene_set(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        ns = make_scene()
        sm.load(ns, transition=make_transition(should_swap_after=99))
        assert sm._pending_scene is ns

    def test_scene_swaps_when_should_swap(self):
        sm = SceneManager.instance()
        sm.load(make_scene("Init"))
        ns = make_scene("New")
        sm.load(ns, transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        assert sm.current is ns

    def test_transition_cleared_when_done(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm.load(make_scene(), transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        sm.update(0.016)
        assert sm._transition is None


class TestPushWithTransition:
    def test_push_transition_adds_scene_on_swap(self):
        sm  = SceneManager.instance()
        sm.load(make_scene("Base"))
        top = make_scene("Top")
        sm.push(top, transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        assert sm.current is top and sm.stack_depth == 2

    def test_push_transition_does_not_clear_stack(self):
        sm = SceneManager.instance()
        sm.load(make_scene("Base"))
        sm.push(make_scene("Top"), transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        assert sm.stack_depth == 2


class TestPopWithTransition:
    def test_pop_transition_removes_top(self):
        sm   = SceneManager.instance()
        base = make_scene("Base")
        sm.load(base)
        sm.push(make_scene("Top"))
        sm.pop(transition=make_transition(should_swap_after=0))
        sm.update(0.016)
        assert sm.stack_depth == 1 and sm.current is base

    def test_pop_on_single_with_transition_does_nothing(self):
        sm = SceneManager.instance()
        sm.load(make_scene())
        sm.pop(transition=make_transition())
        assert sm.stack_depth == 1


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
        sm = SceneManager.instance()
        s  = make_scene()
        sm.load(s)
        sc = _FakeSurface()
        sm.draw(sc)
        s.draw.assert_called_once_with(sc)

    def test_draw_no_scene_no_error(self):
        SceneManager.instance().draw(_FakeSurface())


class TestRunPhysics:
    def test_run_physics_called_on_update(self):
        from unittest.mock import patch as _patch
        sm     = SceneManager.instance()
        sm.load(make_scene())
        box    = MagicMock()
        circle = MagicMock()
        fake   = types.ModuleType("engine.physics.collider")
        fake.BoxCollider    = box
        fake.CircleCollider = circle
        with _patch.dict(sys.modules, {"engine.physics.collider": fake}):
            sm.update(0.016)
        box.check_all.assert_called_once()
        circle.check_all.assert_called_once()

    def test_run_physics_silences_exceptions(self):
        from unittest.mock import patch as _patch
        sm     = SceneManager.instance()
        sm.load(make_scene())
        broken = MagicMock()
        broken.check_all.side_effect = RuntimeError("boom")
        fake   = types.ModuleType("engine.physics.collider")
        fake.BoxCollider    = broken
        fake.CircleCollider = MagicMock()
        with _patch.dict(sys.modules, {"engine.physics.collider": fake}):
            sm.update(0.016)


class TestDoSwapLoadCleanup:
    def test_do_swap_load_clears_collider_registry(self):
        from unittest.mock import patch as _patch
        sm     = SceneManager.instance()
        box    = MagicMock()
        circle = MagicMock()
        box._scene_tilemaps           = {"x": 1}
        box._scene_tilemap_components = {"x": 1}
        box._registry                 = ["a"]
        circle._registry              = ["b"]
        fake   = types.ModuleType("engine.physics.collider")
        fake.BoxCollider    = box
        fake.CircleCollider = circle
        with _patch.dict(sys.modules, {"engine.physics.collider": fake}):
            sm._do_swap_load(make_scene())
        assert box._registry == [] and circle._registry == []

    def test_do_swap_load_stops_music(self):
        from unittest.mock import patch as _patch
        sm        = SceneManager.instance()
        audio     = MagicMock()
        audio_mod = types.ModuleType("engine.audio")
        audio_mod.AudioManager = audio
        col_mod   = types.ModuleType("engine.physics.collider")
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
        assert "MyScene" in r and "depth=1" in r
