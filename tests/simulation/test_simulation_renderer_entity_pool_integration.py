"""Testes de escala para 5.000 entidades renderizadas em lote."""
from __future__ import annotations

import time
import pygame
import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.render_batch import BatchedSimulationRenderer, SimulationRenderBuffer


def test_5000_entities_batched_render_scale_and_fraction_matrix():
    pygame.init()
    target_surf = pygame.Surface((1280, 720))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}

    pool = SimulationEntityPool(initial_capacity=5000)
    # Cria 5.000 entidades distribuídas
    for i in range(5000):
        # 500 dentro da tela [-600, 600] x [-300, 300], 4.500 fora
        if i < 500:
            x = float((i % 25) * 40 - 500)
            y = float((i // 25) * 30 - 250)
        else:
            x = float(2000.0 + i)
            y = float(2000.0 + i)
        pool.create(position=(x, y))

    buf = SimulationRenderBuffer(initial_capacity=5000)
    renderer = BatchedSimulationRenderer()

    # Sync + Render
    t0 = time.perf_counter()
    buf.sync_from_pool(pool, sprite_id=1)
    sync_time = time.perf_counter() - t0

    stats = renderer.render(buf, camera=(0.0, 0.0), target_surface=target_surf, sprite_registry=registry)

    assert stats["submitted_instances"] == 5000
    assert stats["visible_instances"] == 500
    assert stats["culled_instances"] == 4500
    assert stats["draw_operations"] == 500
    assert sync_time + stats["total_s"] < 0.1  # Renderização muito rápida para 5.000 entidades
