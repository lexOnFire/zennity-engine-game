"""Testes de integração entre NavigationGrid2D, AStarPathfinder, EntityPool e SystemScheduler."""
from __future__ import annotations

import time
import pytest
from engine.simulation.astar import AStarPathfinder
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.navigation_grid import NavigationGrid2D
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.system import System


class NavigationDecisionSystem(System):
    """Calcula caminhos para entidades a 10Hz."""
    def __init__(self, pool: SimulationEntityPool, grid: NavigationGrid2D) -> None:
        super().__init__()
        self.pool = pool
        self.grid = grid
        self.paths_calculated = 0
        self.entity_targets = {}  # idx -> path

    def update(self, scene, dt: float) -> None:
        for idx in self.pool.iter_alive_indices():
            if idx not in self.entity_targets:
                # Converte mundo -> célula
                cx, cy = self.grid.world_to_cell(self.pool.position_x[idx], self.pool.position_y[idx])
                goal = (self.grid.width - 1, self.grid.height - 1)
                path = AStarPathfinder.find_path(self.grid, (cx, cy), goal)
                self.entity_targets[idx] = path
                self.paths_calculated += 1


class NavigationMovementSystem(System):
    """Move entidades ao longo do caminho a 60Hz."""
    def __init__(self, pool: SimulationEntityPool, grid: NavigationGrid2D, decision_sys: NavigationDecisionSystem) -> None:
        super().__init__()
        self.pool = pool
        self.grid = grid
        self.decision_sys = decision_sys
        self.steps_taken = 0

    def update(self, scene, dt: float) -> None:
        self.steps_taken += 1
        px = self.pool.position_x
        py = self.pool.position_y

        for idx in self.pool.iter_alive_indices():
            path = self.decision_sys.entity_targets.get(idx)
            if path and len(path) > 1:
                next_cell = path[1]
                target_x, target_y = self.grid.cell_to_world(next_cell[0], next_cell[1])
                # Move levemente em direção ao waypoint
                px[idx] += (target_x - px[idx]) * dt * 5.0
                py[idx] += (target_y - py[idx]) * dt * 5.0


def test_navigation_multirate_scheduler_integration():
    grid = NavigationGrid2D(width=20, height=20, cell_size=32.0)
    pool = SimulationEntityPool(initial_capacity=100)

    # Cria 10 entidades leves
    for i in range(10):
        pool.create(position=(16.0, 16.0))

    dec_sys = NavigationDecisionSystem(pool, grid)
    move_sys = NavigationMovementSystem(pool, grid, dec_sys)

    scheduler = SystemScheduler()
    scheduler.register(dec_sys, TickPolicy.fixed_hz(10), priority=100)
    scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=200)

    # Simula 1.0s (60 ticks a 60Hz, 10 ticks a 10Hz)
    dt = 1.0 / 60.0
    for _ in range(60):
        scheduler.update(None, dt)

    assert dec_sys.paths_calculated == 10
    assert move_sys.steps_taken == 60


def test_astar_scale_benchmark_report():
    """Mede desempenho do A* em grids de diferentes tamanhos."""
    sizes = [(25, 25), (50, 50), (100, 100)]
    results = {}

    for w, h in sizes:
        grid = NavigationGrid2D(width=w, height=h)
        # Adiciona algumas barreiras determinísticas
        for y in range(h // 4, 3 * h // 4):
            grid.set_walkable(w // 2, y, False)

        start = (0, 0)
        goal = (w - 1, h - 1)

        t0 = time.perf_counter()
        path = AStarPathfinder.find_path(grid, start, goal)
        duration = time.perf_counter() - t0

        results[f"{w}x{h}"] = {
            "duration_s": duration,
            "path_length": len(path),
            "found": len(path) > 0,
        }

    assert results["100x100"]["found"] is True
    assert results["100x100"]["duration_s"] < 0.1  # Deve ser muito rápido em 100x100
