"""Testes de integração entre SystemScheduler, SimulationEntityPool e FlowField2D com benchmarks de performance."""
from __future__ import annotations

import random
import time
import pytest
from engine.simulation.astar import AStarPathfinder
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.flow_field import FlowField2D
from engine.simulation.navigation_grid import NavigationGrid2D
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.system import System


class FlowMovementSystem(System):
    """Atualiza a posição das entidades a 60Hz utilizando o FlowField compartilhado."""
    def __init__(self, pool: SimulationEntityPool, flow: FlowField2D, speed: float = 60.0) -> None:
        super().__init__()
        self.pool = pool
        self.flow = flow
        self.speed = speed
        self.ticks = 0

    def update(self, scene, dt: float) -> None:
        self.ticks += 1
        px = self.pool.position_x
        py = self.pool.position_y
        vx = self.pool.velocity_x
        vy = self.pool.velocity_y

        for idx in self.pool.iter_alive_indices():
            dx, dy = self.flow.get_direction_world(px[idx], py[idx])
            vx[idx] = dx * self.speed
            vy[idx] = dy * self.speed
            px[idx] += vx[idx] * dt
            py[idx] += vy[idx] * dt


class FlowRebuildSystem(System):
    """Verifica e reconstrói o FlowField caso esteja desatualizado (1Hz ou 5Hz)."""
    def __init__(self, flow: FlowField2D) -> None:
        super().__init__()
        self.flow = flow
        self.rebuild_count = 0

    def update(self, scene, dt: float) -> None:
        if self.flow.is_stale():
            self.flow.rebuild()
            self.rebuild_count += 1


def test_scheduler_flow_field_multirate_integration():
    grid = NavigationGrid2D(width=20, height=20, cell_size=32.0)
    flow = FlowField2D(grid)
    flow.build((19, 19))

    pool = SimulationEntityPool(initial_capacity=100)
    for _ in range(50):
        pool.create(position=(32.0, 32.0))

    move_sys = FlowMovementSystem(pool, flow)
    rebuild_sys = FlowRebuildSystem(flow)

    scheduler = SystemScheduler()
    scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
    scheduler.register(rebuild_sys, TickPolicy.fixed_hz(5), priority=200)

    # 1 segundo de simulação
    dt = 1.0 / 60.0
    for _ in range(60):
        scheduler.update(None, dt)

    assert move_sys.ticks == 60
    assert rebuild_sys.rebuild_count == 0  # Grid não foi alterado

    # Muta o grid
    grid.set_walkable(10, 10, False)
    assert flow.is_stale() is True

    # Mais 1 segundo -> rebuild system deve reconstruir o field
    for _ in range(60):
        scheduler.update(None, dt)

    assert rebuild_sys.rebuild_count == 1
    assert flow.is_stale() is False


def test_flow_field_vs_astar_benchmark_report():
    """Benchmark comparativo entre N A* individuais vs 1 FlowField build + N O(1) lookups."""
    grid = NavigationGrid2D(width=50, height=50)
    # Adiciona alguns obstáculos
    for y in range(10, 40):
        grid.set_walkable(25, y, False)

    goal = (45, 45)
    agent_counts = [100, 500, 1000]
    results = {}

    rng = random.Random(42)
    starts = []
    for _ in range(1000):
        sx = rng.randint(0, 20)
        sy = rng.randint(0, 45)
        starts.append((sx, sy))

    for count in agent_counts:
        test_starts = starts[:count]

        # 1. FlowField: 1 build + N lookups
        t0 = time.perf_counter()
        flow = FlowField2D(grid)
        flow.build(goal)
        build_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        for s in test_starts:
            _ = flow.get_direction(s[0], s[1])
        lookup_time = time.perf_counter() - t0
        flow_total = build_time + lookup_time

        # 2. A*: N pathfinding calls
        t0 = time.perf_counter()
        for s in test_starts:
            _ = AStarPathfinder.find_path(grid, s, goal)
        astar_total = time.perf_counter() - t0

        results[count] = {
            "flow_build_s": build_time,
            "flow_lookup_s": lookup_time,
            "flow_total_s": flow_total,
            "astar_total_s": astar_total,
            "speedup": astar_total / flow_total if flow_total > 0 else 1.0,
        }

    # Para 1000 agentes indo para o mesmo goal, FlowField deve apresentar speedup massivo (> 10x)
    assert results[1000]["speedup"] > 5.0
