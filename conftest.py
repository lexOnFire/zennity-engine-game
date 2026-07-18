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

# Configuração dummy global (evita que a engine tente abrir janela/áudio durante import)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()

class _FakeSurface(pygame.Surface):
    """
    Subclasse de Surface que rastreia chamadas de blit/fill via MagicMock,
    enquanto preserva o funcionamento real para funções em C do PyGame.
    O blit é tolerante: se o surface fonte não for um pygame.Surface real
    (ex: _FakeSurface de teste local), não delega ao C-level.
    """
    _fake = True
    SRCALPHA = 65536

    def __init__(self, size=(800, 600), flags=0):
        super().__init__(size, flags)
        self._size = tuple(size)
        _real_blit  = super().blit
        _real_fill  = super().fill
        _real_alpha = super().set_alpha
        self._alpha = 255

        # blit: delega ao C-level somente se o source é pygame.Surface real
        def _safe_blit(source, dest, *args, **kwargs):
            if isinstance(source, pygame.surface.Surface):
                return _real_blit(source, dest, *args, **kwargs)
            # Source é um fake puro (MagicMock, _FakeSurface local) — não blita de verdade
            return pygame.Rect(0, 0, 0, 0)

        def _tracking_alpha(value, *args, **kwargs):
            self._alpha = value
            return _real_alpha(value, *args, **kwargs)

        self.blit_mock = MagicMock(side_effect=_safe_blit)
        self.fill_mock = MagicMock(side_effect=_real_fill)
        self.set_alpha_mock = MagicMock(side_effect=_tracking_alpha)

    def blit(self, *args, **kwargs):
        return self.blit_mock(*args, **kwargs)

    def fill(self, *args, **kwargs):
        return self.fill_mock(*args, **kwargs)

    def set_alpha(self, *args, **kwargs):
        return self.set_alpha_mock(*args, **kwargs)

    def copy(self):
        new_surf = super().copy()
        # Inicializa mocks na nova instância copiada, pois o C-level copy ignora __init__
        _real_blit  = super(type(new_surf), new_surf).blit
        _real_fill  = super(type(new_surf), new_surf).fill
        _real_alpha = super(type(new_surf), new_surf).set_alpha

        def _safe_blit_copy(source, dest, *args, **kwargs):
            if isinstance(source, pygame.surface.Surface):
                return _real_blit(source, dest, *args, **kwargs)
            return pygame.Rect(0, 0, 0, 0)

        new_surf.blit_mock = MagicMock(side_effect=_safe_blit_copy)
        new_surf.fill_mock = MagicMock(side_effect=_real_fill)
        new_surf.set_alpha_mock = MagicMock(side_effect=_real_alpha)
        return new_surf

    # Mantemos algumas propriedades esperadas por testes legados
    def get_alpha(self):
        return super().get_alpha() or 255



def pytest_configure(config):
    """
    Instala stubs de pygame antes de qualquer coleta.
    NÃO chama importlib.import_module("engine.transitions") aqui —
    isso causava import duplo e o erro '(unknown location)'.
    """
    # Garante que as funções de desenho originais executem, mas sejam rastreáveis
    _real_draw_rect = pygame.draw.rect

    # Stubs — instalados UMA vez, antes de qualquer import de engine.*
    pygame.Surface         = _FakeSurface           # type: ignore[assignment]
    def _safe_draw_rect(surface, color, rect, *args, **kwargs):
        # Evita TypeError caso algum teste injete um _FakeSurface local em pygame.draw.rect
        if isinstance(surface, pygame.Surface):
            return _real_draw_rect(surface, color, rect, *args, **kwargs)
        try:
            return pygame.Rect(rect)
        except Exception:
            return pygame.Rect(0, 0, 0, 0)
    pygame.draw.rect       = MagicMock(side_effect=_safe_draw_rect)
    pygame.SRCALPHA        = 65536

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
