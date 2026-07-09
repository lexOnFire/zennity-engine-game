"""
conftest.py — fixtures globais para os testes da Zennity Engine.

pytest_configure() é o hook mais cedo possível — roda ANTES da coleta,
BEFORE de qualquer import de módulo de teste, mesmo antes das fixtures.
Por isso os stubs de pygame ficam aqui dentro desse hook.
"""
from __future__ import annotations

import importlib
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
    Hook mais cedo do pytest — roda antes de qualquer coleta ou import
    de módulo de teste.

    Instala os stubs de pygame.Surface e pygame.draw.rect para que
    CrossfadeTransition e WipeTransition funcionem com _FakeSurface
    nos testes unitários.
    """
    # Vars SDL antes do primeiro import de pygame
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

    import pygame  # noqa: PLC0415

    # Substituir Surface e draw.rect por stubs
    pygame.Surface   = _FakeSurface          # type: ignore[assignment]
    pygame.draw.rect = MagicMock()

    # Limpar cache de engine.transitions para que o próximo import
    # use os stubs recém instalados
    for mod in ("engine.transitions", "engine"):
        sys.modules.pop(mod, None)

    importlib.import_module("engine.transitions")


# ── Inicialização do pygame ───────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _pygame_init():
    """Inicializa o pygame uma única vez para toda a sessão de testes."""
    import pygame  # noqa: PLC0415
    pygame.init()
    yield
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
