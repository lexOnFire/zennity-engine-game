"""
tests/animation/conftest.py

Inicializa pygame headless UMA unica vez para toda a suite de animation.
pygame.init() é necessário (não só display.init()) para que
Surface.set_at / get_at funcionem corretamente nos testes de flip_h.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
