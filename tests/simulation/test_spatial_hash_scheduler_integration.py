"""Testes de integração entre SystemScheduler, SimulationEntityPool e SpatialHash2D."""
from __future__ import annotations

import random
import time
import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.spatial_hash import SpatialHash2D
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.system import System


class SpatialMovementSystem(System):
    """Atualiza posições e sincroniza com o SpatialHash em 60Hz."""
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash

    def update(self, scene, dt: float) -> None:
        px = self.pool.position_x
        py = self.pool.position_y
        vx = self.pool.velocity_x
        vy = self.pool.velocity_y

        for idx in self.pool.iter_alive_indices():
            px[idx] += vx[idx] * dt
            py[idx] += vy[idx] * dt
            # Handle da entidade
            h = self.pool.iter_alive_handles()  # ou constrói via idx
            from engine.simulation.entity_pool import EntityHandle
            handle = EntityHandle(idx, self.pool.generation[idx])
            self.spatial_hash.update(handle, px[idx], py[idx])


class SpatialQuerySystem(System):
    """Executa consultas de vizinhança a 10Hz."""
    def __init__(self, pool: SimulationEntityPool, spatial_hash: SpatialHash2D) -> None:
        super().__init__()
        self.pool = pool
        self.spatial_hash = spatial_hash
        self.query_count = 0
        self.total_neighbors_found = 0

    def update(self, scene, dt: float) -> None:
        self.query_count += 1
        # Consulta vizinhos ao redor da origem (0, 0) com raio 50.0
        neighbors = self.spatial_hash.query_radius(0.0, 0.0, radius=50.0, pool=self.pool)
        self.total_neighbors_found += len(neighbors)


def test_three_way_system_integration():
    pool = SimulationEntityPool(initial_capacity=1024)
    sh = SpatialHash2D(cell_size=64.0)

    for i in range(500):
        h = pool.create(position=(float(i % 50), float(i % 50)), velocity=(1.0, 0.0))
        sh.insert(h, float(i % 50), float(i % 50))

    scheduler = SystemScheduler()
    move_sys = SpatialMovementSystem(pool, sh)
    query_sys = SpatialQuerySystem(pool, sh)

    scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
    scheduler.register(query_sys, TickPolicy.fixed_hz(10), priority=200)

    # 1 segundo de simulação
    dt = 1.0 / 60.0
    for _ in range(60):
        scheduler.update(None, dt)

    assert query_sys.query_count == 10
    assert query_sys.total_neighbors_found > 0


def test_spatial_hash_benchmarks_and_speedup_report():
    rng = random.Random(42)
    counts = [100, 1000, 5000]
    results = {}

    for count in counts:
        pool = SimulationEntityPool(initial_capacity=count)
        sh = SpatialHash2D(cell_size=64.0)
        handles = []
        for _ in range(count):
            x = rng.uniform(-1000.0, 1000.0)
            y = rng.uniform(-1000.0, 1000.0)
            h = pool.create(position=(x, y))
            handles.append(h)
            sh.insert(h, x, y)

        # 50 queries com SpatialHash
        t0 = time.perf_counter()
        for _ in range(50):
            qx = rng.uniform(-800.0, 800.0)
            qy = rng.uniform(-800.0, 800.0)
            sh.query_radius(qx, qy, radius=50.0, pool=pool)
        sh_time = time.perf_counter() - t0

        # 50 queries com Brute Force
        t0 = time.perf_counter()
        r2 = 50.0 * 50.0
        for _ in range(50):
            qx = rng.uniform(-800.0, 800.0)
            qy = rng.uniform(-800.0, 800.0)
            bf_res = []
            for h in handles:
                idx = h.index
                dx = pool.position_x[idx] - qx
                dy = pool.position_y[idx] - qy
                if (dx * dx + dy * dy) <= r2:
                    bf_res.append(h)
        bf_time = time.perf_counter() - t0

        results[count] = {
            "spatial_hash_s": sh_time,
            "brute_force_s": bf_time,
            "speedup": (bf_time / sh_time) if sh_time > 0 else 1.0,
        }

    # Para 5000 entidades, o spatial hash deve ser significativamente mais rápido que brute force
    assert results[5000]["speedup"] > 2.0
