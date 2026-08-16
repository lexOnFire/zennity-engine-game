"""Testes de integração entre FlowField2D e SimulationEntityPool para 5.000 entidades."""
from __future__ import annotations

import time
import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.flow_field import FlowField2D
from engine.simulation.navigation_grid import NavigationGrid2D


def test_5000_entities_shared_flow_field():
    grid = NavigationGrid2D(width=50, height=50, cell_size=32.0)
    # Bloqueios centrais
    for y in range(15, 35):
        grid.set_walkable(25, y, False)

    goal = (45, 45)
    flow = FlowField2D(grid)
    flow.build(goal)

    # Cria 5.000 entidades no pool
    pool = SimulationEntityPool(initial_capacity=5000)
    for i in range(5000):
        # Espalhadas nas primeiras colunas
        wx = float((i % 20) * 32.0 + 16.0)
        wy = float(((i // 20) % 45) * 32.0 + 16.0)
        pool.create(position=(wx, wy))

    assert pool.alive_count == 5000

    # Simula 10 ticks de movimento onde todas as 5.000 entidades leem o mesmo FlowField em O(1)
    dt = 0.016
    speed = 50.0

    px = pool.position_x
    py = pool.position_y
    vx = pool.velocity_x
    vy = pool.velocity_y

    t0 = time.perf_counter()
    for _ in range(10):
        for idx in pool.iter_alive_indices():
            dx, dy = flow.get_direction_world(px[idx], py[idx])
            vx[idx] = dx * speed
            vy[idx] = dy * speed
            px[idx] += vx[idx] * dt
            py[idx] += vy[idx] * dt
    duration = time.perf_counter() - t0

    # 10 ticks para 5.000 entidades = 50.000 consultas ao FlowField
    assert duration < 1.0  # Muito rápido e sem alocações
