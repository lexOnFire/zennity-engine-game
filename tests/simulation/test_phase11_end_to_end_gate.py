"""tests/simulation/test_phase11_end_to_end_gate.py
────────────────────────────────────────────────────────────────
Teste final de integração e validação de ponta a ponta da Phase 11.

Valida a integração completa e determinística de:
  - SystemScheduler (11.1)
  - SimulationEntityPool (11.2)
  - SpatialHash2D (11.3)
  - NavigationGrid2D + AStarPathfinder (11.4)
  - FlowField2D (11.5)
  - SimulationRenderBuffer + BatchedSimulationRenderer (11.6)

Garante que 100% dos fluxos operam conjuntamente em harmonia arquitetural
sem criação de GameObjects, Components, LogicGraphs ou UUIDs individuais.
"""
from __future__ import annotations

import pygame
import pytest
from engine.simulation import (
    AStarPathfinder,
    BatchedSimulationRenderer,
    EntityHandle,
    FlowField2D,
    NavigationGrid2D,
    SimulationEntityPool,
    SimulationRenderBuffer,
    SpatialHash2D,
    SystemScheduler,
    TickPolicy,
)
from engine.system import System


class EndToEndAgentMovementSystem(System):
    def __init__(self, pool: SimulationEntityPool, flow: FlowField2D) -> None:
        super().__init__()
        self.pool = pool
        self.flow = flow
        self.steps = 0

    def update(self, scene, dt: float) -> None:
        self.steps += 1
        px = self.pool.position_x
        py = self.pool.position_y
        vx = self.pool.velocity_x
        vy = self.pool.velocity_y
        for idx in self.pool.iter_alive_indices():
            dx, dy = self.flow.get_direction_world(px[idx], py[idx])
            vx[idx] = dx * 100.0
            vy[idx] = dy * 100.0
            px[idx] += vx[idx] * dt
            py[idx] += vy[idx] * dt


class EndToEndSpatialSyncSystem(System):
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash

    def update(self, scene, dt: float) -> None:
        px = self.pool.position_x
        py = self.pool.position_y
        for idx in self.pool.iter_alive_indices():
            h = EntityHandle(idx, self.pool.generation[idx])
            self.spatial_hash.update(h, px[idx], py[idx])


def test_phase11_end_to_end_integrated_pipeline():
    pygame.init()
    target_surf = pygame.Surface((800, 600))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}

    # 1. Navigation Grid + Obstáculos
    grid = NavigationGrid2D(width=40, height=40, cell_size=20.0)
    for y in range(10, 30):
        grid.set_walkable(20, y, False)

    # 2. A* e FlowField para o mesmo destino
    goal = (35, 35)
    astar_path = AStarPathfinder.find_path(grid, (5, 5), goal)
    assert astar_path is not None
    assert len(astar_path) > 0

    flow = FlowField2D(grid)
    flow.build(goal)
    assert not flow.is_stale()

    # 3. EntityPool com 500 entidades
    pool = SimulationEntityPool(initial_capacity=500)
    sh = SpatialHash2D(cell_size=40.0)

    for i in range(500):
        wx = float((i % 20) * 15 + 20)
        wy = float((i // 20) * 15 + 20)
        h = pool.create(position=(wx, wy), velocity=(1.0, 1.0))
        sh.insert(h, wx, wy)

    assert pool.alive_count == 500

    # 4. Agendamento Multi-Taxa (Move 60Hz + Spatial 60Hz)
    scheduler = SystemScheduler()
    move_sys = EndToEndAgentMovementSystem(pool, flow)
    spatial_sys = EndToEndSpatialSyncSystem(pool, sh)

    scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
    scheduler.register(spatial_sys, TickPolicy.fixed_hz(60), priority=200)

    buf = SimulationRenderBuffer(initial_capacity=500)
    renderer = BatchedSimulationRenderer()

    # 5. Executa 30 frames de simulação integrada
    dt = 1.0 / 60.0
    for _ in range(30):
        scheduler.update(None, dt)
        buf.sync_from_pool(pool, sprite_id=1)
        stats = renderer.render(buf, camera=(400.0, 400.0), target_surface=target_surf, sprite_registry=registry)
        assert stats["submitted_instances"] == 500
        assert stats["visible_instances"] > 0
        assert stats["draw_operations"] == stats["visible_instances"]

    assert move_sys.steps == 30

    # 6. Consultas de vizinhança espaciais
    sample_res = sh.query_radius(200.0, 200.0, radius=50.0, pool=pool)
    assert isinstance(sample_res, list)

    # 7. Invariantes de Isolamento Arquitetural
    for idx in pool.iter_alive_indices():
        # Assegura que nenhum objeto pesado foi criado
        assert not hasattr(pool, "game_objects")
        assert not hasattr(pool, "logic_graphs")
        assert not hasattr(pool, "components")
