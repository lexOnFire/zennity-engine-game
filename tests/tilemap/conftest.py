"""
tests/tilemap/conftest.py

Inicializa pygame headless UMA unica vez para toda a suite de tilemap.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.display.init()
