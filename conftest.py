"""
conftest.py — fixtures globais para os testes da Zennity Engine.

Aqui instalamos stubs MÍNIMOS para rodar em headless.
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
# Para o Qt headless também, por garantia
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pygame
pygame.init()

# Para testes que especificamente verificam assert_called, embrulhamos as funções reais
# sem perder o funcionamento. Assim, a superfície REAL continua sendo pintada!
def pytest_configure(config):
    # Envelopa os métodos de pygame.draw para suportarem assert_called() sem perder a funcionalidade C.
    for draw_func_name in ["rect", "polygon", "circle", "ellipse", "arc", "line", "lines", "aaline", "aalines"]:
        if hasattr(pygame.draw, draw_func_name):
            real_func = getattr(pygame.draw, draw_func_name)
            setattr(pygame.draw, draw_func_name, MagicMock(wraps=real_func))
            
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

# Muitos testes esperam 'screen' retornar uma surface mockada para checar blit_mock.
# Em vez de mockar pygame.Surface globalmente, apenas a fixture 'screen' retorna
# um proxy que rastreia blit e fill, mas ainda delega para a superfície real.
class SurfaceProxy(pygame.Surface):
    def __init__(self, size=(800, 600)):
        super().__init__(size)
        self.blit_mock = MagicMock(wraps=super().blit)
        self.fill_mock = MagicMock(wraps=super().fill)
        self._fake = True  # Para manter compatibilidade com testes que checam _fake
        
    def blit(self, *args, **kwargs):
        return self.blit_mock(*args, **kwargs)
        
    def fill(self, *args, **kwargs):
        return self.fill_mock(*args, **kwargs)


@pytest.fixture
def fake_surface_class():
    """Retorna o proxy para testes que o instanciam explicitamente."""
    return SurfaceProxy


@pytest.fixture
def screen():
    """Retorna um SurfaceProxy 800x600 para testes que chamam .draw(screen)."""
    return SurfaceProxy((800, 600))


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
    if hasattr(pygame.draw.rect, "reset_mock"):
        pygame.draw.rect.reset_mock()
    yield
    if hasattr(pygame.draw.rect, "reset_mock"):
        pygame.draw.rect.reset_mock()

@pytest.fixture(autouse=True)
def reset_event_bus():
    """Limpa os listeners globais do EventBus entre cada teste."""
    try:
        from engine.event_bus import EventBus
        EventBus.clear()
    except ImportError:
        pass
    yield
    try:
        from engine.event_bus import EventBus
        EventBus.clear()
    except ImportError:
        pass

