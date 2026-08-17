"""Testes de equivalência, culling, transform e otimização do BatchedSimulationRenderer (Phase 12 - Item 12.4)."""
from __future__ import annotations

import pygame
import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.render_batch import BatchedSimulationRenderer, SimulationRenderBuffer


def test_buffer_sync_equivalence_and_capacity_reuse():
    pool = SimulationEntityPool(initial_capacity=100)
    for i in range(50):
        pool.create(position=(float(i * 10), float(i * 5)))

    buf = SimulationRenderBuffer(initial_capacity=100)
    buf.sync_from_pool(pool, sprite_id=2, layer=1)

    assert buf.count == 50
    assert buf._capacity >= 100

    # Valida dados sincronizados
    for i in range(50):
        assert buf.position_x[i] == float(i * 10)
        assert buf.position_y[i] == float(i * 5)
        assert buf.sprite_ids[i] == 2
        assert buf.layers[i] == 1
        assert buf.entity_indices[i] == i

    # Steady-state reuse: segundo sync não deve realocar capacidade
    cap_before = buf._capacity
    buf.sync_from_pool(pool, sprite_id=3)
    assert buf._capacity == cap_before
    assert buf.count == 50
    assert buf.sprite_ids[0] == 3


def test_camera_transform_exact_equivalence():
    cam_positions = [(0.0, 0.0), (100.0, -50.0), (-250.0, 300.0)]
    zooms = [0.5, 1.0, 2.0]
    screen_sizes = [(1280, 720), (1920, 1080), (800, 600)]

    for cam_x, cam_y in cam_positions:
        for zoom in zooms:
            for sw, sh in screen_sizes:
                for wx, wy in [(-100.0, -100.0), (0.0, 0.0), (500.0, 350.0)]:
                    # Referência canônica
                    ref_sx, ref_sy = BatchedSimulationRenderer.world_to_screen_canonical(
                        wx, wy, cam_x, cam_y, zoom, sw, sh
                    )
                    # Inlining exato
                    inlined_sx = (wx - cam_x) * zoom + (sw / 2.0)
                    inlined_sy = (wy - cam_y) * zoom + (sh / 2.0)

                    assert ref_sx == inlined_sx
                    assert ref_sy == inlined_sy


def test_culling_exact_counts_and_partial_visibility():
    pygame.init()
    target = pygame.Surface((800, 600))
    sprite = pygame.Surface((32, 32))
    registry = {1: sprite}

    buf = SimulationRenderBuffer(initial_capacity=10)
    # Entidade 0: no centro exato (visível)
    buf.submit(0.0, 0.0, sprite_id=1)
    # Entidade 1: na borda parcial da tela (800/2 + 10 = 410, dentro da margem de 16px da sprite de 32px)
    buf.submit(410.0, 0.0, sprite_id=1)
    # Entidade 2: claramente fora da tela (1000, 0)
    buf.submit(1000.0, 0.0, sprite_id=1)

    renderer = BatchedSimulationRenderer()
    stats = renderer.render(buf, camera=(0.0, 0.0), target_surface=target, sprite_registry=registry, default_sprite_size=(32, 32))

    assert stats["submitted_instances"] == 3
    assert stats["visible_instances"] == 2
    assert stats["culled_instances"] == 1
    assert stats["draw_operations"] == 2


def test_batch_blits_and_individual_blit_visual_equivalence():
    pygame.init()
    target_individual = pygame.Surface((400, 400))
    target_blits = pygame.Surface((400, 400))

    # Cria sprites com cores distintas
    sprite1 = pygame.Surface((16, 16))
    sprite1.fill((255, 0, 0))
    sprite2 = pygame.Surface((16, 16))
    sprite2.fill((0, 255, 0))
    registry = {1: sprite1, 2: sprite2}

    buf = SimulationRenderBuffer(initial_capacity=20)
    for i in range(10):
        s_id = 1 if i % 2 == 0 else 2
        buf.submit(float(i * 20 - 90), float(i * 20 - 90), sprite_id=s_id)

    renderer = BatchedSimulationRenderer()

    # Render com fallback individual
    stats_indiv = renderer.render(buf, camera=(0.0, 0.0), target_surface=target_individual, sprite_registry=registry, use_blits=False)
    # Render com batch blits
    stats_blits = renderer.render(buf, camera=(0.0, 0.0), target_surface=target_blits, sprite_registry=registry, use_blits=True)

    assert stats_indiv["draw_operations"] == 10
    assert stats_blits["draw_operations"] == 10
    assert stats_blits["backend_submit_calls"] == 1

    # Valida equivalência visual exata de bytes das superfícies
    raw_indiv = pygame.image.tobytes(target_individual, "RGBA")
    raw_blits = pygame.image.tobytes(target_blits, "RGBA")
    assert raw_indiv == raw_blits


def test_layer_ordering_and_deterministic_sorting():
    pygame.init()
    target = pygame.Surface((400, 400))
    sprite = pygame.Surface((16, 16))
    registry = {1: sprite}

    buf = SimulationRenderBuffer(initial_capacity=10)
    # Submete fora de ordem de layer
    buf.submit(0.0, 0.0, sprite_id=1, layer=10, entity_index=5)
    buf.submit(0.0, 0.0, sprite_id=1, layer=0, entity_index=2)
    buf.submit(0.0, 0.0, sprite_id=1, layer=0, entity_index=1)
    buf.submit(0.0, 0.0, sprite_id=1, layer=5, entity_index=3)

    renderer = BatchedSimulationRenderer()
    stats = renderer.render(buf, camera=(0.0, 0.0), target_surface=target, sprite_registry=registry)

    assert stats["visible_instances"] == 4
    assert stats["draw_operations"] == 4


def test_slot_reuse_and_no_ghost_sprites():
    pool = SimulationEntityPool(initial_capacity=10)
    h1 = pool.create(position=(0.0, 0.0))
    h2 = pool.create(position=(50.0, 50.0))

    buf = SimulationRenderBuffer(initial_capacity=10)
    buf.sync_from_pool(pool, sprite_id=1)
    assert buf.count == 2

    # Destrói h1
    pool.destroy(h1)
    buf.sync_from_pool(pool, sprite_id=1)
    assert buf.count == 1
    assert buf.entity_indices[0] == h2.index

    # Reutiliza slot
    h3 = pool.create(position=(100.0, 100.0))
    assert h3.index == h1.index
    buf.sync_from_pool(pool, sprite_id=2)
    assert buf.count == 2
