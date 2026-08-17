"""Testes de integracao entre TemporalWorkDistributor, SpatialHash2D e SystemScheduler (Phase 12 - Item 12.5)."""
from __future__ import annotations

import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.lod import (
    LOD_HIGH,
    LOD_LOW,
    LOD_MEDIUM,
    LOD_SLEEP,
    SimulationFocus,
    SimulationLODConfig,
    SimulationLODManager,
)
from engine.simulation.spatial_hash import SpatialHash2D
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.simulation.work_distribution import TemporalWorkDistributor
from engine.system import System


class DistributedNeighborQuerySystem(System):
    """
    Sistema que executa consultas espaciais de vizinhança distribuídas no tempo a cada frame.
    """

    def __init__(
        self,
        pool: SimulationEntityPool,
        spatial_hash: SpatialHash2D,
        distributor: TemporalWorkDistributor,
    ) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash
        self.distributor = distributor
        self.total_queries_executed = 0
        self.total_neighbors_found = 0
        self.queries_per_frame: list[int] = []

    def update(self, scene, dt: float) -> None:
        active_indices = self.pool.iter_alive_indices()
        batch = self.distributor.select(active_indices)

        self.queries_per_frame.append(len(batch))
        px = self.pool.position_x
        py = self.pool.position_y

        for idx in batch:
            nbrs = self.spatial_hash.query_radius(px[idx], py[idx], radius=50.0, pool=self.pool, ordered=False)
            self.total_queries_executed += 1
            self.total_neighbors_found += len(nbrs)

        self.distributor.advance()


def test_distributed_query_work_conservation_and_spike_smoothing():
    count = 600
    pool = SimulationEntityPool(initial_capacity=count)
    sh = SpatialHash2D(cell_size=64.0)

    for i in range(count):
        h = pool.create(position=(float(i * 10), float(i * 10)))
        sh.insert(h, float(i * 10), float(i * 10))

    # 1. Baseline Burst (10Hz em SystemScheduler -> 100% da população a cada 6 frames)
    class BurstNeighborQuerySystem(System):
        def __init__(self) -> None:
            super().__init__()
            self.total_queries = 0
            self.queries_per_frame: list[int] = []

        def update(self, scene, dt: float) -> None:
            active = pool.iter_alive_indices()
            self.queries_per_frame.append(len(active))
            self.total_queries += len(active)

    sched_burst = SystemScheduler()
    burst_sys = BurstNeighborQuerySystem()
    sched_burst.register(burst_sys, TickPolicy.fixed_hz(10))

    for _ in range(60):
        sched_burst.update(None, 1.0 / 60.0)

    # 2. Distributed (60Hz base com 6 phases)
    distributor = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
    sched_dist = SystemScheduler()
    dist_sys = DistributedNeighborQuerySystem(pool, sh, distributor)
    sched_dist.register(dist_sys, TickPolicy.every_frame())

    for _ in range(60):
        sched_dist.update(None, 1.0 / 60.0)

    # Conservação total de trabalho: exatamente o mesmo número de consultas em 60 frames
    assert burst_sys.total_queries == dist_sys.total_queries_executed == 6000

    # Suavização de pico:
    # No burst: pico máximo de 600 queries por frame
    assert max(burst_sys.queries_per_frame) == 600
    # No distribuído: pico máximo de exatamente 100 queries por frame (6x menor!)
    assert max(dist_sys.queries_per_frame) == 100
    assert min(dist_sys.queries_per_frame) == 100


def test_distributed_query_with_simulation_lod_tiers():
    count = 1000
    pool = SimulationEntityPool(initial_capacity=count)
    for i in range(count):
        pool.create(position=(float(i * 2), float(i * 2)))

    focus = SimulationFocus(0.0, 0.0)
    lod_cfg = SimulationLODConfig(high_distance=200.0, medium_distance=600.0, low_distance=1200.0)
    lod_mgr = SimulationLODManager(config=lod_cfg, initial_capacity=count)
    lod_mgr.classify(pool, focus)

    # Distribuidor para tier MEDIUM (20Hz -> 3 fases em 60Hz)
    dist_med = TemporalWorkDistributor(target_hz=20.0, base_hz=60.0)

    med_indices = lod_mgr.get_tier_indices(LOD_MEDIUM)
    total_med = len(med_indices)

    med_counts = {idx: 0 for idx in med_indices}

    for _ in range(60):  # 1 segundo
        batch = dist_med.select(med_indices)
        for idx in batch:
            med_counts[idx] += 1
        dist_med.advance()

    # Cada entidade medium recebeu exatamente 20 updates
    for idx, c in med_counts.items():
        assert c == 20
