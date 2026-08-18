"""Testes de regressão do ParticleSystem (Pre-Phase 13 Sprint R1)."""
from __future__ import annotations

import pygame
import pytest

from engine.core.game_object import GameObject
from engine.graphics.camera import Camera
from engine.graphics.camera_manager import CameraManager
from engine.graphics.particles import ParticleSystem


def test_particle_system_draw_without_camera():
    """Valida que o draw() de ParticleSystem funciona corretamente quando não há câmera ativa."""
    pygame.init()
    surface = pygame.Surface((320, 240))

    go = GameObject("Emitter")
    go.transform.position = (50.0, 50.0, 0.0)
    ps = ParticleSystem()
    go.add_component(ps)

    ps.emit(5)
    assert len(ps.particles) == 5

    # Avança tempo para simular ciclo de vida
    ps.update(0.016)

    # Executa o draw sem levantar NameError
    ps.draw(surface)


def test_particle_system_draw_with_active_camera():
    """Valida que o draw() de ParticleSystem converte coordenadas com a câmera ativa sem NameError."""
    pygame.init()
    surface = pygame.Surface((640, 480))

    # Configura câmera ativa canônica
    cam_go = GameObject("MainCamera")
    cam_comp = Camera()
    cam_go.add_component(cam_comp)
    cam_go.transform.position = (100.0, 100.0, 0.0)
    CameraManager.set_main_camera(cam_comp)

    go = GameObject("Emitter")
    go.transform.position = (150.0, 150.0, 0.0)
    ps = ParticleSystem()
    go.add_component(ps)

    ps.emit(10)
    assert len(ps.particles) == 10

    ps.update(0.016)

    # Executa o draw com câmera ativa
    ps.draw(surface)
