"""
conftest.py — fixtures globais para os testes da Zennity Engine.

pytest_configure() roda ANTES de qualquer coleta ou import de módulo de teste.
Aqui apenas instalamos os stubs de pygame — NÃO importamos engine.transitions
para evitar import duplo / conflito de cache durante a coleta.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock

import pytest


class _FakeSurface:
    """
    Surface mínima que rastreia blit/fill/set_alpha via MagicMock.
    Aceita qualquer argumento — sem validação de tipo SDL.
    """
    _fake = True

    def __init__(self, size=(800, 600), flags=0):
        self._size  = tuple(size)
        self._flags = flags
        self._alpha = 255
        self.blit      = MagicMock()
        self.fill      = MagicMock()
        self.set_alpha = MagicMock(side_effect=lambda a: setattr(self, "_alpha", a))

    def get_size(self):  return self._size
    def get_alpha(self): return self._alpha


def pytest_configure(config):
    """
    Instala stubs de pygame antes de qualquer coleta.
    NÃO chama importlib.import_module("engine.transitions") aqui —
    isso causava import duplo e o erro '(unknown location)'.
    """
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

    import pygame  # noqa: PLC0415
    pygame.init()

    # Stubs — instalados UMA vez, antes de qualquer import de engine.*
    pygame.Surface   = _FakeSurface          # type: ignore[assignment]
    pygame.draw.rect = MagicMock()
    pygame.SRCALPHA  = 65536                 # valor real do pygame, evita AttributeError

    # Garante que engine.transitions seja importado pela 1ª vez JÁ com os stubs
    # removendo qualquer cache residual (ex: de um import acidental anterior)
    for mod in list(sys.modules.keys()):
        if mod.startswith("engine"):
            del sys.modules[mod]


# ── Inicialização do pygame ───────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _pygame_init():
    """Pygame já foi inicializado em pytest_configure; apenas faz yield."""
    yield
    import pygame  # noqa: PLC0415
    pygame.quit()


# ── Fixtures globais ──────────────────────────────────────────────────────────

@pytest.fixture
def fake_surface_class():
    """Expõe _FakeSurface para testes que precisam dela explicitamente."""
    return _FakeSurface


@pytest.fixture
def screen():
    """_FakeSurface 800x600 para testes que chamam .draw(screen)."""
    return _FakeSurface((800, 600))


@pytest.fixture
def empty_scene():
    """Scene vazia pronta para uso nos testes."""
    from engine.core import Scene
    return Scene(name="TestScene")


@pytest.fixture
def simple_go():
    """GameObject básico sem cena associada."""
    from engine.core import GameObject
    return GameObject("TestGO", tag="Test")


@pytest.fixture(autouse=True)
def reset_pygame_mocks():
    """Reseta mocks de pygame antes e depois de cada teste."""
    import pygame  # noqa: PLC0415
    pygame.draw.rect.reset_mock()
    yield
    pygame.draw.rect.reset_mock()
