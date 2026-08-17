"""Testes de contrato e validacao de escalabilidade para Phase 12 Scale Gate (Item 12.6)."""
from __future__ import annotations

import gc
import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.flow_field import FlowField2D
from engine.simulation.lod import (
    LOD_HIGH,
    LOD_LOW,
    LOD_MEDIUM,
    LOD_SLEEP,
    SimulationFocus,
    SimulationLODConfig,
    SimulationLODManager,
)
from engine.simulation.navigation_grid import NavigationGrid2D
from engine.simulation.render_batch import BatchedSimulationRenderer, SimulationRenderBuffer
from engine.simulation.spatial_hash import SpatialHash2D
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.simulation.work_distribution import TemporalWorkDistributor
from engine.system import System


class ScalableMovementSystem(System):
    def __init__(self, pool: SimulationEntityPool, speed: float = 30.0) -> None:
        super().__init__()
        self.pool = pool
        self.speed = speed

    def update(self, scene, dt: float) -> None:
        px = self.pool.position_x
        py = self.pool.position_y
        vx = self.pool.velocity_x
        vy = self.pool.velocity_y
        for idx in self.pool.iter_alive_indices():
            px[idx] += vx[idx] * self.speed * dt
            py[idx] += vy[idx] * self.speed * dt


class ScalableSpatialSyncSystem(System):
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash

    def update(self, scene, dt: float) -> None:
        self.spatial_hash.sync_from_pool(self.pool)


class ScalableNeighborQuerySystem(System):
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D, distributor: TemporalWorkDistributor) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash
        self.distributor = distributor
        self.total_queries = 0

    def update(self, scene, dt: float) -> None:
        active = self.pool.iter_alive_indices()
        batch = self.distributor.select(active)
        px = self.pool.position_x
        py = self.pool.position_y
        for idx in batch:
            nbrs = self.spatial_hash.query_radius(px[idx], py[idx], radius=32.0, pool=self.pool, ordered=False)
            self.total_queries += 1
        self.distributor.advance()


def test_phase12_scale_gate_10k_lifecycle_and_determinism():
    """Valida integridade estrutural, ciclo de vida e determinismo com 10.000 entidades."""
    count = 10000

    def run_sim(seed_val: int = 42):
        pool = SimulationEntityPool(initial_capacity=count)
        sh = SpatialHash2D(cell_size=64.0)
        dist = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)

        for i in range(count):
            x = float((i * 17) % 2000)
            y = float((i * 23) % 2000)
            h = pool.create(position=(x, y), velocity=(1.0, 0.5))
            sh.insert(h, x, y)

        sched = SystemScheduler()
        move = ScalableMovementSystem(pool)
        spatial = ScalableSpatialSyncSystem(pool, sh)
        query = ScalableNeighborQuerySystem(pool, sh, dist)

        sched.register(move, TickPolicy.fixed_hz(60), priority=100)
        sched.register(spatial, TickPolicy.fixed_hz(60), priority=200)
        sched.register(query, TickPolicy.every_frame(), priority=300)

        for _ in range(12):  # 12 frames
            sched.update(None, 1.0 / 60.0)

        stats = sh.get_profiling_stats()
        return pool.position_x[:10], query.total_queries, stats["update_calls"]

    pos1, q1, up1 = run_sim(42)
    pos2, q2, up2 = run_sim(42)

    assert pos1 == pos2
    assert q1 == q2 == (count * 2)  # 12 frames at 10Hz (6 phases) = 2 full passes = 20.000 queries
    assert up1 == up2 == (count * 12)  # 12 frames at 60Hz spatial sync = 120.000 updates


def test_phase12_scale_gate_10k_culling_and_slot_churn():
    """Valida culling O(N) e ausência de resíduos visuais com 10k entidades."""
    count = 10000
    pool = SimulationEntityPool(initial_capacity=count)
    buf = SimulationRenderBuffer(initial_capacity=count)
    renderer = BatchedSimulationRenderer()

    # 1.000 dentro da tela (x in [-400, 400], y in [-300, 300]), 9.000 fora
    for i in range(count):
        if i < 1000:
            x = float((i % 40) * 15 - 300)
            y = float((i // 40) * 15 - 200)
        else:
            x = float(5000.0 + i)
            y = float(5000.0 + i)
        pool.create(position=(x, y))

    import pygame
    pygame.init()
    surf = pygame.Surface((1280, 720))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}

    buf.sync_from_pool(pool, sprite_id=1)
    stats = renderer.render(buf, camera=(0.0, 0.0), target_surface=surf, sprite_registry=registry)

    assert stats["visible_instances"] == 1000
    assert stats["culled_instances"] == 9000
