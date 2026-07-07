"""Configuração global dos testes.

Alguns testes legados usam módulos fake para isolar pygame/engine. Quando o
pytest executa a suíte inteira, esses fakes podem permanecer em sys.modules
durante a coleta de outros testes e quebrar imports reais como:

    engine.physics.collider
    engine.transitions

Este arquivo também padroniza o ambiente headless usado por Qt/Pygame durante
os testes para reduzir diferenças entre Windows, Linux, CI e Codespaces.
"""
from __future__ import annotations

import os
import sys

import pytest


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


_REAL_ENGINE_MODULES = (
    "engine.physics.collider",
    "engine.transitions",
    "engine.audio",
    "engine.graphics.math3d",
)


def _remove_fake_engine_modules() -> None:
    physics_module = sys.modules.get("engine.physics")
    if physics_module is not None and not hasattr(physics_module, "__path__"):
        sys.modules.pop("engine.physics", None)

    for module_name in _REAL_ENGINE_MODULES:
        module = sys.modules.get(module_name)
        if module is None:
            continue

        if module_name == "engine.physics.collider" and not hasattr(module, "CollisionInfo"):
            sys.modules.pop(module_name, None)
        elif module_name == "engine.transitions" and not hasattr(module, "SlideTransition"):
            sys.modules.pop(module_name, None)
        elif module_name == "engine.audio" and not getattr(module, "__file__", None):
            sys.modules.pop(module_name, None)
        elif module_name == "engine.graphics.math3d" and not getattr(module, "__file__", None):
            sys.modules.pop(module_name, None)


def pytest_collect_file(file_path, parent):  # noqa: D401
    """Limpa módulos fake antes da coleta de cada arquivo de teste."""
    _remove_fake_engine_modules()
    return None


@pytest.fixture(autouse=True)
def reset_global_input_state():
    """Evita vazamento de estado global de Input entre testes."""
    yield
    module = sys.modules.get("engine.input")
    input_class = getattr(module, "Input", None) if module is not None else None
    if input_class is None:
        return
    input_class._manager = None
    input_class._keys_current = {}
    input_class._keys_previous = {}
    input_class._mouse_current = (False, False, False)
    input_class._mouse_previous = (False, False, False)
    input_class._mouse_position = (0, 0)
    input_class._mouse_rel = (0, 0)
