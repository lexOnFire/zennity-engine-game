"""Testes de equivalência de câmera e culling do BatchedSimulationRenderer."""
from __future__ import annotations

import pygame
import pytest
from engine.simulation.render_batch import BatchedSimulationRenderer, SimulationRenderBuffer


def test_camera_world_to_screen_canonical_equivalence():
    # Cria uma tela de 800x600 e câmera em (100, 200) com zoom 2.0
    cam_pos = (100.0, 200.0)
    zoom = 2.0
    screen_w, screen_h = 800, 600

    world_x, world_y = 150.0, 250.0

    # Fórmula canônica do BatchedSimulationRenderer
    bx, by = BatchedSimulationRenderer.world_to_screen_canonical(
        world_x, world_y, cam_pos[0], cam_pos[1], zoom, screen_w, screen_h
    )

    # Equivalente esperado: (150 - 100)*2 + 400 = 500; (250 - 200)*2 + 300 = 400
    assert bx == 500.0
    assert by == 400.0


def test_batched_renderer_culling():
    # Tela 800x600 com câmera em (0, 0) e zoom 1.0 -> Visão de mundo: [-400, 400] x [-300, 300]
    pygame.init()
    surf = pygame.Surface((800, 600))
    sprite_surf = pygame.Surface((32, 32))
    registry = {1: sprite_surf}

    buf = SimulationRenderBuffer(initial_capacity=10)
    # 2 instâncias dentro da câmera
    buf.submit(0.0, 0.0, sprite_id=1)
    buf.submit(200.0, 100.0, sprite_id=1)
    # 2 instâncias fora da câmera
    buf.submit(1000.0, 1000.0, sprite_id=1)
    buf.submit(-800.0, 0.0, sprite_id=1)

    renderer = BatchedSimulationRenderer()
    stats = renderer.render(buf, camera=(0.0, 0.0), target_surface=surf, sprite_registry=registry, default_sprite_size=(32, 32))

    assert stats["submitted_instances"] == 4
    assert stats["visible_instances"] == 2
    assert stats["culled_instances"] == 2
    assert stats["draw_operations"] == 2
