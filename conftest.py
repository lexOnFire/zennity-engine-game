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

# Se for Linux e estiver rodando headless (no GitHub Actions), evitamos herança real para não quebrar alocações de vídeo C-level
IS_LINUX_HEADLESS = sys.platform.startswith("linux") and os.environ.get("SDL_VIDEODRIVER") == "dummy"

if IS_LINUX_HEADLESS:
    class _FakeSurface:
        """
        Mock puro de Surface para o Linux Headless em CI (evita alocações gráficas via SDL).
        """
        _fake = True
        SRCALPHA = 65536

        def __init__(self, size=(800, 600), flags=0):
            self._size = tuple(size)
            self._flags = flags
            self._pixels: dict[tuple[int, int], tuple] = {}
            self._alpha = 255
            self.blit_mock = MagicMock(return_value=pygame.Rect(0, 0, 0, 0))
            self.fill_mock = MagicMock(return_value=pygame.Rect(0, 0, 0, 0))
            self.set_alpha_mock = MagicMock()

        def blit(self, *args, **kwargs):
            return self.blit_mock(*args, **kwargs)

        def fill(self, *args, **kwargs):
            return self.fill_mock(*args, **kwargs)

        def set_alpha(self, value, *args, **kwargs):
            self._alpha = value
            return self.set_alpha_mock(value, *args, **kwargs)

        def get_alpha(self):
            return self._alpha

        def get_width(self):
            return self._size[0]

        def get_height(self):
            return self._size[1]

        def get_size(self):
            return self._size

        def get_rect(self, **kwargs):
            rect = pygame.Rect(0, 0, self._size[0], self._size[1])
            for k, v in kwargs.items():
                setattr(rect, k, v)
            return rect

        def subsurface(self, rect):
            r = pygame.Rect(rect)
            return _FakeSurface((r.width, r.height))

        def convert(self, *args, **kwargs):
            return self

        def convert_alpha(self, *args, **kwargs):
            return self

        def copy(self):
            new_surf = _FakeSurface(self._size, self._flags)
            new_surf._pixels = dict(self._pixels)
            new_surf._alpha = self._alpha
            return new_surf

        def set_at(self, pos, color):
            self._pixels[tuple(pos)] = tuple(color)

        def get_at(self, pos):
            return self._pixels.get(tuple(pos), (0, 0, 0, 255))
else:
    class _FakeSurface(pygame.Surface):
        """
        Subclasse de Surface que rastreia chamadas de blit/fill via MagicMock,
        preservando o funcionamento real no Windows.
        """
        _fake = True
        SRCALPHA = 65536

        def __init__(self, size=(800, 600), flags=0):
            super().__init__(size, flags)
            self._size = tuple(size)
            self._flags = flags
            self._pixels: dict[tuple[int, int], tuple] = {}
            _real_blit  = super().blit
            _real_fill  = super().fill
            _real_alpha = super().set_alpha
            self._alpha = 255

            def _safe_blit(source, dest, *args, **kwargs):
                if isinstance(source, pygame.surface.Surface):
                    return _real_blit(source, dest, *args, **kwargs)
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

        def get_alpha(self):
            return super().get_alpha() or 255

        def copy(self):
            new_surf = super().copy()
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
            new_surf._pixels = dict(getattr(self, "_pixels", {}))
            new_surf._alpha = getattr(self, "_alpha", 255)
            return new_surf


def _make_fake_flip(fake_cls):
    """
    Retorna uma versão de pygame.transform.flip que:
      - no Windows (onde _FakeSurface herda pygame.Surface), delega ao SDL;
      - no Linux Headless (onde _FakeSurface é mock puro), simula a inversão em memória pura.
    """
    import pygame as _pg
    _real_flip = _pg.transform.flip

    def _fake_flip(surface, flip_x: bool, flip_y: bool):
        if IS_LINUX_HEADLESS:
            # Simula a inversão de pixels em memória pura para _FakeSurface
            new_surf = surface.copy()
            w, h = surface.get_width(), surface.get_height()
            new_pixels = {}
            for (x, y), color in getattr(surface, "_pixels", {}).items():
                nx = w - 1 - x if flip_x else x
                ny = h - 1 - y if flip_y else y
                new_pixels[(nx, ny)] = color
            new_surf._pixels = new_pixels
            return new_surf

        # Windows: usa o flip real do SDL
        return _real_flip(surface, flip_x, flip_y)

    return _fake_flip


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
