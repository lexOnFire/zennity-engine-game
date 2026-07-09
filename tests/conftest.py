"""
tests/conftest.py
────────────────────────────────────────────────────────────────────────────
Garante que pygame.draw.rect seja um MagicMock e que pygame.Surface retorne
um _FakeSurface nos testes de transição.

Problema raiz: CrossfadeTransition.draw() cria internamente
    self._alpha_surf = pygame.Surface((w, h), pygame.SRCALPHA)
e depois faz
    self._alpha_surf.blit(snapshot, (0, 0))
Se pygame.Surface for a classe C real, _alpha_surf é uma Surface SDL que
rejeita _FakeSurface como argumento do blit com:
    TypeError: argument 1 must be pygame.surface.Surface, not _FakeSurface

Solução: substituir pygame.Surface por _FakeSurface aqui no conftest,
que é carregado pelo pytest ANTES de qualquer módulo de teste.
"""
from __future__ import annotations

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


# ── Instalar stubs no pygame antes de qualquer import de teste ──────────────
#
# pygame.Surface  → _FakeSurface
#   CrossfadeTransition cria `self._alpha_surf = pygame.Surface(...)` dentro
#   do draw(). Se for a Surface C real, ela rejeita _FakeSurface no blit.
#   Ao substituir por _FakeSurface, _alpha_surf também se torna um fake e
#   aceita qualquer argumento.
#
# pygame.draw.rect → MagicMock
#   WipeTransition chama pygame.draw.rect(screen, color, rect). A função C
#   real também rejeita _FakeSurface como primeiro argumento.

pygame.Surface  = _FakeSurface          # type: ignore[assignment]
pygame.draw.rect = MagicMock()


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
