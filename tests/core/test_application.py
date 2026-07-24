"""
tests/core/test_application.py
────────────────────────────────────────────────────────────────
Commit 2: valida o contrato público de Application sem inicializar Pygame.

Estratégia: mockar pygame.init, pygame.mixer.init, pygame.time.Clock e
Window.__init__ (não a classe inteira) para preservar a referência
original de Window como chave no service registry.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fixture: reseta Application._instance entre testes
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_application():
    from engine.application import Application
    Application._instance = None
    yield
    Application._instance = None


# ---------------------------------------------------------------------------
# Factory: cria Application sem tocar em Pygame
# ---------------------------------------------------------------------------

def _make_app(**kwargs):
    """
    Instancia Application com Pygame mockado.

    Não substitui a classe Window pelo caminho do módulo (isso trocaria
    a referência usada como chave no registry). Em vez disso, mocka:
      - pygame.init / pygame.mixer.init
      - pygame.time.Clock (evita criar clock real)
      - pygame.display.set_mode (evita janela gráfica)
      - pygame.display.set_caption
      - pygame.display.flip
    Isso deixa Window ser instanciado normalmente, mantendo a classe
    original como chave no _services dict.
    """
    from engine.application import Application

    mock_surface = MagicMock()
    mock_clock   = MagicMock()

    patches = [
        patch("pygame.init"),
        patch("pygame.mixer.init"),
        patch("pygame.time.Clock",          return_value=mock_clock),
        patch("pygame.display.set_mode",    return_value=mock_surface),
        patch("pygame.display.set_caption"),
        patch("pygame.display.flip"),
    ]

    for p in patches:
        p.start()

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

    def test_register_as_and_get_by_interface(self):
        class IPhysics:
            pass
        class Box2DPhysics(IPhysics):
            pass
        impl = Box2DPhysics()
        self.app.register_as(IPhysics, impl)
        assert self.app.get(IPhysics) is impl

    def test_register_as_overrides_existing(self):
        class ISound:
            pass
        v1, v2 = MagicMock(), MagicMock()
        self.app.register_as(ISound, v1)
        self.app.register_as(ISound, v2)
        assert self.app.get(ISound) is v2

    def test_has_returns_true_for_registered(self):
        class Bar:
            pass
        self.app.register(Bar())
        assert self.app.has(Bar) is True

    def test_has_returns_false_for_unregistered(self):
        class Baz:
            pass
        assert self.app.has(Baz) is False


# ===========================================================================
# 3. Built-ins registrados automaticamente
# ===========================================================================

class TestBuiltins:
    def setup_method(self):
        self.app, self.patches = _make_app()

    def teardown_method(self):
        _stop_patches(self.patches)

    def test_window_is_registered(self):
        # Importar pelo mesmo caminho que _register_builtins usa
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
        assert isinstance(self.app.get(Time), Time)

    def test_get_event_bus_returns_event_bus_instance(self):
        from engine.event_bus import EventBus
        assert isinstance(self.app.get(EventBus), EventBus)


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
        assert "services=" in r
        count = int(r.split("services=")[1].rstrip(">"))
        assert count >= 7

    def test_repr_contains_scene_none_when_no_scene(self):
        assert "scene=None" in repr(self.app)


# ===========================================================================
# 5. Propriedades de conveniência
# ===========================================================================

class TestConvenienceProperties:
    def setup_method(self):
        self.app, self.patches = _make_app()

    def teardown_method(self):
        _stop_patches(self.patches)

    def test_screen_property_is_not_none(self):
        assert self.app.screen is not None

    def test_current_scene_is_none_before_run(self):
        assert self.app.current_scene is None
