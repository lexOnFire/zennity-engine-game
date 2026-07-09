"""
tests/conftest.py
────────────────────────────────────────────────────────────────────────────
Garante que pygame.draw.rect e pygame.Surface sejam stubs ANTES que
engine.transitions seja importado pelos testes.

Problema raiz:
  O pytest coleta TODOS os testes antes de rodar qualquer um. Durante a
  coleta, outro módulo de teste importa `engine` (via engine/__init__.py),
  que por sua vez importa `engine.transitions`. Nesse momento pygame.Surface
  e pygame.draw.rect ainda são as implementações C reais. Quando
  test_transitions.py tenta importar SlideTransition, o módulo já está em
  sys.modules com a referência antiga — retornando "unknown location".

Solução:
  1. Instalar os stubs em pygame antes de qualquer coisa.
  2. Remover engine.transitions de sys.modules para forçar reload limpo.
  3. Reimportar engine.transitions já com os stubs ativos.
"""
from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock

import pygame
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


# ── 1. Instalar stubs no pygame ───────────────────────────────────────────────────

pygame.Surface   = _FakeSurface         # type: ignore[assignment]
pygame.draw.rect = MagicMock()

# ── 2. Forçar reload de engine.transitions com stubs já ativos ────────────────
#
# Remove o módulo e todos os submódulos do engine que dependem de pygame,
# para que o próximo import use pygame.Surface = _FakeSurface.

_MODULES_TO_RELOAD = [
    "engine.transitions",
    "engine",
]

for _mod in _MODULES_TO_RELOAD:
    sys.modules.pop(_mod, None)

importlib.import_module("engine.transitions")


# ── Fixtures ───────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=False)
def fake_surface_class():
    """Exibe _FakeSurface para testes que precisam dela explicitamente."""
    return _FakeSurface


@pytest.fixture(autouse=True)
def reset_pygame_mocks():
    """Reseta mocks de pygame antes e depois de cada teste."""
    pygame.draw.rect.reset_mock()
    yield
    pygame.draw.rect.reset_mock()
