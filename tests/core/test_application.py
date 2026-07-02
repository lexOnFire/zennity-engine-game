"""
tests/core/test_application.py
────────────────────────────────────────────────────────────────
Commit 2: valida o contrato público de Application sem inicializar Pygame.

Estratégia: mockar todos os subsistemas que tocam Pygame
(Window, pygame.init, pygame.mixer.init, pygame.quit, sys.exit)
para que os testes rodem em CI/headless sem display.
"""
from __future__ import annotations

import sys
import types
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Fixture: reseta Application._instance entre testes
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_application():
    """Garante isolamento: cada teste começa sem instância global."""
    from engine.application import Application
    Application._instance = None
    yield
    Application._instance = None


# ---------------------------------------------------------------------------
# Factory: cria Application sem tocar em Pygame
# ---------------------------------------------------------------------------

def _make_app(**kwargs):
    """
    Instancia Application com todos os subsistemas Pygame mockados.
    Retorna (app, patches) para que os patches permaneçam ativos
    durante o teste.
    """
    from engine.application import Application

    mock_screen = MagicMock()
    mock_window = MagicMock()
    mock_window.screen = mock_screen
    mock_window.width  = kwargs.get("width",  800)
    mock_window.height = kwargs.get("height", 600)
    mock_window.is_fullscreen = False

    mock_clock = MagicMock()

    patches = [
        patch("pygame.init"),
        patch("pygame.mixer.init"),
        patch("pygame.time.Clock", return_value=mock_clock),
        patch("engine.application.Window", return_value=mock_window),
    ]

    started = [p.start() for p in patches]

    app = Application(
        width  = kwargs.get("width",  800),
        height = kwargs.get("height", 600),
        title  = kwargs.get("title",  "Test"),
        fps    = kwargs.get("fps",    60),
    )

    return app, patches


def _stop_patches(patches):
    for p in patches:
        try:
            p.stop()
        except RuntimeError:
            pass


# ===========================================================================
# 1. Singleton
# ===========================================================================

class TestSingleton:
    def test_single_instance_allowed(self):
        app, patches = _make_app()
        try:
            assert app is not None
        finally:
            _stop_patches(patches)

    def test_second_instance_raises(self):
        app, patches = _make_app()
        try:
            with pytest.raises(RuntimeError, match="já foi instanciada"):
                _make_app()
        finally:
            _stop_patches(patches)

    def test_current_returns_instance(self):
        from engine.application import Application
        app, patches = _make_app()
        try:
            assert Application.current() is app
        finally:
            _stop_patches(patches)

    def test_current_raises_before_instantiation(self):
        from engine.application import Application
        with pytest.raises(RuntimeError, match="Nenhuma Application"):
            Application.current()


# ===========================================================================
# 2. Service Locator — register / get
# ===========================================================================

class TestServiceLocator:
    def setup_method(self):
        self.app, self.patches = _make_app()

    def teardown_method(self):
        _stop_patches(self.patches)

    # -- register / get por tipo exato --

    def test_register_and_get_by_exact_type(self):
        class FooService:
            pass

        svc = FooService()
        self.app.register(svc)
        assert self.app.get(FooService) is svc

    def test_get_unknown_raises_key_error(self):
        class Unknown:
            pass

        with pytest.raises(KeyError, match="Unknown"):
            self.app.get(Unknown)

    # -- register_as (interface / classe base) --

    def test_register_as_and_get_by_interface(self):
        class IPhysics:
            pass

        class Box2DPhysics(IPhysics):
            pass

        impl = Box2DPhysics()
        self.app.register_as(IPhysics, impl)
        assert self.app.get(IPhysics) is impl

    def test_register_as_overrides_existing(self):
        class ISoundSystem:
            pass

        svc_v1 = MagicMock(spec=ISoundSystem)
        svc_v2 = MagicMock(spec=ISoundSystem)
        self.app.register_as(ISoundSystem, svc_v1)
        self.app.register_as(ISoundSystem, svc_v2)
        assert self.app.get(ISoundSystem) is svc_v2

    # -- has() --

    def test_has_returns_true_for_registered(self):
        class BarService:
            pass

        self.app.register(BarService())
        assert self.app.has(BarService) is True

    def test_has_returns_false_for_unregistered(self):
        class BazService:
            pass

        assert self.app.has(BazService) is False


# ===========================================================================
# 3. Built-ins registrados automaticamente
# ===========================================================================

class TestBuiltins:
    def setup_method(self):
        self.app, self.patches = _make_app()

    def teardown_method(self):
        _stop_patches(self.patches)

    def test_window_is_registered(self):
        from engine.window import Window
        assert self.app.has(Window)

    def test_time_is_registered(self):
        from engine.time import Time
        assert self.app.has(Time)

    def test_event_bus_is_registered(self):
        from engine.event_bus import EventBus
        assert self.app.has(EventBus)

    def test_scene_manager_is_registered(self):
        from engine.core import SceneManager
        assert self.app.has(SceneManager)

    def test_engine_is_registered(self):
        from engine.core import Engine
        assert self.app.has(Engine)

    def test_input_is_registered(self):
        from engine.input import Input
        assert self.app.has(Input)

    def test_get_time_returns_time_instance(self):
        from engine.time import Time
        result = self.app.get(Time)
        assert isinstance(result, Time)

    def test_get_event_bus_returns_event_bus_instance(self):
        from engine.event_bus import EventBus
        result = self.app.get(EventBus)
        assert isinstance(result, EventBus)


# ===========================================================================
# 4. __repr__
# ===========================================================================

class TestRepr:
    def setup_method(self):
        self.app, self.patches = _make_app()

    def teardown_method(self):
        _stop_patches(self.patches)

    def test_repr_contains_application(self):
        assert "Application" in repr(self.app)

    def test_repr_contains_service_count(self):
        r = repr(self.app)
        # "services=N" onde N >= número de built-ins (7)
        assert "services=" in r
        count_str = r.split("services=")[1].rstrip(">")
        assert int(count_str) >= 7

    def test_repr_contains_scene_none_when_no_scene(self):
        r = repr(self.app)
        assert "scene=None" in r


# ===========================================================================
# 5. Propriedades de conveniência
# ===========================================================================

class TestConvenienceProperties:
    def setup_method(self):
        self.app, self.patches = _make_app()

    def teardown_method(self):
        _stop_patches(self.patches)

    def test_screen_property_returns_pygame_surface(self):
        # deve ser a Surface mockada que o Window retorna
        screen = self.app.screen
        assert screen is not None

    def test_current_scene_is_none_before_run(self):
        assert self.app.current_scene is None
