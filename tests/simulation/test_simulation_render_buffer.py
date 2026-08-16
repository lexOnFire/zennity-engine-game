"""Testes unitários para SimulationRenderBuffer (Phase 11 - Item 11.6)."""
from __future__ import annotations

import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.render_batch import SimulationRenderBuffer


def test_simulation_render_buffer_submit_and_clear():
    buf = SimulationRenderBuffer(initial_capacity=16)
    assert buf.count == 0

    buf.submit(10.0, 20.0, sprite_id=1, layer=0, entity_index=0)
    buf.submit(30.0, 40.0, sprite_id=2, layer=1, entity_index=1)
    assert buf.count == 2
    assert buf.position_x[0] == 10.0
    assert buf.position_y[1] == 40.0

    buf.clear()
    assert buf.count == 0


def test_simulation_render_buffer_sync_from_pool():
    pool = SimulationEntityPool(initial_capacity=10)
    h1 = pool.create(position=(100.0, 150.0))
    h2 = pool.create(position=(200.0, 250.0))

    buf = SimulationRenderBuffer(initial_capacity=10)
    buf.sync_from_pool(pool, sprite_id=5, layer=2)

    assert buf.count == 2
    assert buf.position_x[0] == 100.0
    assert buf.position_y[0] == 150.0
    assert buf.sprite_ids[0] == 5
    assert buf.layers[0] == 2
    assert buf.entity_indices[0] == h1.index
