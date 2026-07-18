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


import pygame
_original_pygame_surface = pygame.Surface

class _FakeSurface(_original_pygame_surface):
    """
    Surface mínima que rastreia blit/fill/set_alpha via MagicMock.
    """
    _fake = True
    SRCALPHA = 65536

    def __init__(self, size=(800, 600), flags=0, *args, **kwargs):
        super().__init__(size, flags, *args, **kwargs)
        
        self._fake = True
        self._alpha = 255
        self._pixels = {}
        
        from unittest.mock import MagicMock
        self.mock_blit = MagicMock()
        self.mock_fill = MagicMock()
        
        # Guardamos as funções originais
        _orig_blit = self.blit
        _orig_fill = self.fill
        
        def fake_blit(*a, **kw):
            self.mock_blit(*a, **kw)
            try:
                return _orig_blit(*a, **kw)
            except TypeError:
                return pygame.Rect(0, 0, 0, 0)
            
        def fake_fill(*a, **kw):
            self.mock_fill(*a, **kw)
            return _orig_fill(*a, **kw)
            
        self.blit = fake_blit
        self.fill = fake_fill
        
        def fake_set_at(pos, color):
            self._pixels[pos] = tuple(color)
            _original_pygame_surface.set_at(self, pos, color)
            
        def fake_get_at(pos):
            return self._pixels.get(pos, (0, 0, 0, 255))
            
        self.set_at = fake_set_at
        self.get_at = fake_get_at


def _make_fake_flip(fake_cls):
    """
    Retorna uma versão de pygame.transform.flip que:
      - espelha o buffer de pixels de _FakeSurface corretamente;
      - delega ao flip real do SDL para surfaces reais.
    """
    import pygame as _pg
    _real_flip = _pg.transform.flip

    def _fake_flip(surface, flip_x: bool, flip_y: bool):
        if not getattr(surface, "_fake", False):
            return _real_flip(surface, flip_x, flip_y)
        w, h = surface.get_size()
        out = fake_cls((w, h))
        for (x, y), color in surface._pixels.items():
            nx = (w - 1 - x) if flip_x else x
            ny = (h - 1 - y) if flip_y else y
            out._pixels[(nx, ny)] = color
        return out

    return _fake_flip


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
    pygame.Surface         = _FakeSurface           # type: ignore[assignment]
    pygame.draw.rect       = MagicMock()
    pygame.SRCALPHA        = 65536
    pygame.transform.flip  = _make_fake_flip(_FakeSurface)  # type: ignore[assignment]

    # Garante que engine.* seja importado pela 1ª vez JÁ com os stubs
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
