"""
conftest.py — fixtures globais para os testes da Zennity Engine.

Ordem de carregamento do pytest:
  1. conftest.py da RAIZ  ← este arquivo (carregado primeiro)
  2. conftest.py de tests/
  3. coleta dos módulos de teste

Por isso os stubs de pygame precisam estar AQUI, instalados antes que
qualquer módulo de teste importe engine.transitions (ou qualquer outro
módulo que use pygame.Surface / pygame.draw.rect diretamente).
"""
from __future__ import annotations

import importlib
import os
import sys
from unittest.mock import MagicMock

# ── Vars de ambiente SDL antes do primeiro import de pygame ───────────────────
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest


# ── _FakeSurface ──────────────────────────────────────────────────────────────

class _FakeSurface:
    """
    Surface mínima que rastreia blit/fill/set_alpha via MagicMock.
    Aceita qualquer argumento — sem validação de tipo SDL.
    Usada pelos testes de transição para evitar que a Surface C real
    rejeite _FakeSurface como argumento do blit.
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


# ── Instalar stubs ANTES de pygame.init() e ANTES da coleta de testes ─────────
#
# pygame.Surface   → _FakeSurface
#   CrossfadeTransition cria `self._alpha_surf = pygame.Surface(...)` dentro
#   do draw(). Se for a Surface C real, ela rejeita _FakeSurface no blit.
#
# pygame.draw.rect → MagicMock
#   WipeTransition chama pygame.draw.rect(screen, color, rect). A função C
#   real também rejeita _FakeSurface como primeiro argumento.

pygame.Surface   = _FakeSurface          # type: ignore[assignment]
pygame.draw.rect = MagicMock()

# Remove engine.transitions do cache para que o próximo import use os stubs.
# Necessário porque outros conftest.py ou imports de módulo podem ter
# pré-carregado engine.transitions com pygame real antes deste arquivo.
for _mod in ("engine.transitions", "engine"):
    sys.modules.pop(_mod, None)

importlib.import_module("engine.transitions")


# ── Inicialização do pygame ───────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _pygame_init():
    """Inicializa o pygame uma única vez para toda a sessão de testes."""
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
    pygame.draw.rect.reset_mock()
    yield
    pygame.draw.rect.reset_mock()
