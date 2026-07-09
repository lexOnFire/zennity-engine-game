"""
tests/conftest.py
─────────────────────────────────────────────────────────────────────────────
Garante que pygame.draw.rect seja um MagicMock e que pygame.Surface aceite
_FakeSurface nos testes de transição.

Esse arquivo é carregado pelo pytest ANTES de qualquer módulo de teste,
resolvendo o conflito entre o pygame real (inicializado pelo engine) e o
stub de _FakeSurface em test_transitions.py.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pygame
import pytest


class _FakeSurface:
    """Surface mínima compatível com pygame.Surface para fins de teste."""
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


# ── Instalar stub de pygame.draw.rect antes de qualquer import de teste ───────

pygame.draw.rect = MagicMock()

# Expõe _FakeSurface e o módulo pygame patchado como fixtures globais
# para que test_transitions.py possa usar sem re-instalar o stub.

@pytest.fixture(autouse=False)
def fake_surface_class():
    return _FakeSurface


@pytest.fixture(autouse=True)
def reset_draw_rect_mock():
    """Reseta o mock de pygame.draw.rect antes de cada teste."""
    pygame.draw.rect.reset_mock()
    yield
    pygame.draw.rect.reset_mock()
