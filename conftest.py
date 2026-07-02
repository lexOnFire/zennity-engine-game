"""
conftest.py — fixtures globais para os testes da Zennity Engine.

Este arquivo e carregado automaticamente pelo pytest antes de qualquer
modulo de teste. As variaveis de ambiente SDL ja estao setadas no
pytest.ini, entao pygame pode ser importado com seguranca aqui.
"""
from __future__ import annotations

import os
# Garante as vars antes do primeiro import de pygame (fallback para
# execucao direta com 'python -m pytest' fora do pytest.ini)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest


@pytest.fixture(scope="session", autouse=True)
def _pygame_init():
    """Inicializa o pygame uma unica vez para toda a sessao de testes."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def screen():
    """Surface 800x600 para testes que chamam .draw(screen)."""
    return pygame.Surface((800, 600))


@pytest.fixture
def empty_scene():
    """Scene vazia pronta para uso nos testes."""
    from engine.core import Scene
    return Scene(name="TestScene")


@pytest.fixture
def simple_go():
    """GameObject basico sem cena associada."""
    from engine.core import GameObject
    return GameObject("TestGO", tag="Test")
