"""Tests de validação e integração end-to-end de toda a arquitetura da Phase 12.

Valida a invariante global de integração entre:
- SimulationEntityPool (SoA lifecycle)
- SimulationLOD / SimulationFocus (Tier categorization via SimulationLODManager)
- SpatialHash2D (Same-cell / Bulk synchronization & queries)
- TemporalWorkDistributor (Smooth load distribution & non-starvation)
- NavigationGrid2D / FlowField2D (Vector field pathfinding)
- SimulationRenderBuffer / BatchedSimulationRenderer (Culling & Blitting)
- SystemScheduler (Tick policies & execution order)
"""

import math
import random
import pytest
import pygame

from engine.simulation import (
    SimulationEntityPool,
    SpatialHash2D,
    NavigationGrid2D,
    FlowField2D,
    SimulationRenderBuffer,
    BatchedSimulationRenderer,
    SystemScheduler,
    TickPolicy,
    SimulationFocus,
    SimulationLODConfig,
    SimulationLODManager,
    LOD_HIGH,
    LOD_MEDIUM,
    LOD_LOW,
    LOD_SLEEP,
    TemporalWorkDistributor,
)


class E2EMovementSystem:
    def __init__(self, pool: SimulationEntityPool, flow: FlowField2D) -> None:
        self.pool = pool
        self.flow = flow
        self.total_moves = 0

    def update(self, scene, dt: float) -> None:
        px = self.pool.position_x
        py = self.pool.position_y
        vx = self.pool.velocity_x
        vy = self.pool.velocity_y

        for idx in self.pool.iter_alive_indices():
            dx, dy = self.flow.get_direction_world(px[idx], py[idx])
            vx[idx] = dx * 50.0
            vy[idx] = dy * 50.0
            px[idx] += vx[idx] * dt
            py[idx] += vy[idx] * dt
            self.total_moves += 1


class E2ESpatialSyncSystem:
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D) -> None:
        self.pool = pool
        self.spatial_hash = spatial_hash

    def update(self, scene, dt: float) -> None:
        self.spatial_hash.sync_from_pool(self.pool)


class E2ELODQuerySystem:
    def __init__(
        self,
        pool: SimulationEntityPool,
        spatial_hash: SpatialHash2D,
        lod_mgr: SimulationLODManager,
        focus: SimulationFocus,
        distributor: TemporalWorkDistributor,
    ) -> None:
        self.pool = pool
        self.spatial_hash = spatial_hash
        self.lod_mgr = lod_mgr
        self.focus = focus
        self.distributor = distributor
        self.queried_indices = set()
        self.total_neighbors_found = 0

    def update(self, scene, dt: float) -> None:
        # Classifica LOD
        self.lod_mgr.classify(self.pool, self.focus)

        # Filtra entidades que devem executar consultas neste frame (HIGH e MEDIUM)
        high_indices = self.lod_mgr.get_tier_indices(LOD_HIGH)
        med_indices = self.lod_mgr.get_tier_indices(LOD_MEDIUM)
        candidates = high_indices + med_indices

        batch = self.distributor.select(candidates)
        px = self.pool.position_x
        py = self.pool.position_y

        for idx in batch:
            self.queried_indices.add(idx)
            nbrs = self.spatial_hash.query_radius(px[idx], py[idx], radius=40.0, pool=self.pool, ordered=False)
            self.total_neighbors_found += len(nbrs)

        self.distributor.advance()


def test_phase12_end_to_end_full_pipeline_invariants():
    """Valida a integração completa sem premissas de hardware ou timing rígido."""
    pygame.init()
    target_surf = pygame.Surface((800, 600))
    sprite_surf = pygame.Surface((16, 16))
    registry = {1: sprite_surf}

    rng = random.Random(42)
    pop_size = 500
    world_size = 1000.0

    pool = SimulationEntityPool(initial_capacity=pop_size)
    sh = SpatialHash2D(cell_size=64.0)

    for _ in range(pop_size):
        wx = rng.uniform(32.0, world_size - 32.0)
        wy = rng.uniform(32.0, world_size - 32.0)
        h = pool.create((wx, wy), (0.0, 0.0))
        sh.insert(h, wx, wy)

    assert pool.alive_count == pop_size

    # Grid & FlowField
    grid = NavigationGrid2D(width=40, height=40, cell_size=25.0)
    for y in range(10, 30):
        grid.set_walkable(20, y, False)
    flow = FlowField2D(grid)
    flow.build((35, 35))

    # LOD & Focus
    focus = SimulationFocus(x=500.0, y=500.0, enabled=True)
    config = SimulationLODConfig(high_distance=150.0, medium_distance=300.0, low_distance=500.0, hysteresis_margin=20.0)
    lod_mgr = SimulationLODManager(config=config, initial_capacity=pop_size)

    # Work Distributor
    distributor = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)

    # Renderer & Buffer
    buf = SimulationRenderBuffer(initial_capacity=pop_size)
    renderer = BatchedSimulationRenderer()

    # Systems & Scheduler
    scheduler = SystemScheduler()
    move_sys = E2EMovementSystem(pool, flow)
    spatial_sys = E2ESpatialSyncSystem(pool, sh)
    query_sys = E2ELODQuerySystem(pool, sh, lod_mgr, focus, distributor)

    scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
    scheduler.register(spatial_sys, TickPolicy.fixed_hz(60), priority=200)
    scheduler.register(query_sys, TickPolicy.every_frame(), priority=300)

    # Executa 60 frames (~1 segundo de simulação)
    dt = 1.0 / 60.0
    for frame in range(60):
        scheduler.update(None, dt)
        buf.sync_from_pool(pool, sprite_id=1)
        stats = renderer.render(
            buf,
            camera=(500.0, 500.0),
            target_surface=target_surf,
            sprite_registry=registry,
        )

        # Invariantes a cada frame
        assert stats["submitted_instances"] == pop_size
        assert stats["visible_instances"] + stats["culled_instances"] == pop_size
        assert stats["visible_instances"] > 0

    # Invariantes finais de integração
    assert move_sys.total_moves == pop_size * 60
    assert len(query_sys.queried_indices) > 0

    # Valida distribuição de LOD
    stats = lod_mgr.get_stats()
    tier_counts = stats["tier_counts"]
    assert sum(tier_counts.values()) == pop_size
    assert tier_counts["high"] > 0
    assert tier_counts["medium"] > 0

    # Valida SpatialHash profiling & same-cell optimizations
    sh_stats = sh.get_profiling_stats()
    assert sh_stats["update_calls"] >= pop_size * 60
    same_pct = (sh_stats["same_cell_updates"] / sh_stats["update_calls"]) * 100.0
    assert same_pct > 90.0
    assert sh_stats["bulk_sync_calls"] == 60


def test_phase12_end_to_end_determinism_contract():
    """Garante que duas execuções end-to-end do pipeline produzem resultados idênticos."""
    def run_sim(seed: int):
        pygame.init()
        target_surf = pygame.Surface((800, 600))
        registry = {1: pygame.Surface((16, 16))}

        rng = random.Random(seed)
        pop_size = 200
        pool = SimulationEntityPool(initial_capacity=pop_size)
        sh = SpatialHash2D(cell_size=64.0)

        for _ in range(pop_size):
            wx = rng.uniform(50.0, 500.0)
            wy = rng.uniform(50.0, 500.0)
            h = pool.create((wx, wy), (0.0, 0.0))
            sh.insert(h, wx, wy)

        grid = NavigationGrid2D(width=30, height=30, cell_size=20.0)
        flow = FlowField2D(grid)
        flow.build((25, 25))

        focus = SimulationFocus(x=250.0, y=250.0, enabled=True)
        config = SimulationLODConfig(high_distance=100.0, medium_distance=200.0, low_distance=400.0, hysteresis_margin=20.0)
        lod_mgr = SimulationLODManager(config=config, initial_capacity=pop_size)
        distributor = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
        buf = SimulationRenderBuffer(initial_capacity=pop_size)
        renderer = BatchedSimulationRenderer()

        scheduler = SystemScheduler()
        move_sys = E2EMovementSystem(pool, flow)
        spatial_sys = E2ESpatialSyncSystem(pool, sh)
        query_sys = E2ELODQuerySystem(pool, sh, lod_mgr, focus, distributor)

        scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
        scheduler.register(spatial_sys, TickPolicy.fixed_hz(60), priority=200)
        scheduler.register(query_sys, TickPolicy.every_frame(), priority=300)

        dt = 1.0 / 60.0
        for _ in range(30):
            scheduler.update(None, dt)
            buf.sync_from_pool(pool, sprite_id=1)
            renderer.render(buf, camera=(250.0, 250.0), target_surface=target_surf, sprite_registry=registry)

        return (
            list(pool.position_x[:pop_size]),
            list(pool.position_y[:pop_size]),
            [lod_mgr.get_tier(i) for i in range(pop_size)],
            sh.get_profiling_stats(),
        )

    res1 = run_sim(12345)
    res2 = run_sim(12345)

    assert res1[0] == res2[0]  # pos X
    assert res1[1] == res2[1]  # pos Y
    assert res1[2] == res2[2]  # LOD tiers
    assert res1[3] == res2[3]  # SpatialHash stats
