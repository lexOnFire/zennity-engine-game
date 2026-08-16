"""Testes de integração entre SystemScheduler (11.1) e SimulationEntityPool (11.2)."""
from __future__ import annotations

import time
import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.system import System


class MovementSimulationSystem(System):
    """Sistema sintético de movimento em alta frequência (60Hz)."""
    def __init__(self, pool: SimulationEntityPool) -> None:
        super().__init__()
        self.pool = pool
        self.moves = 0

    def update(self, scene, dt: float) -> None:
        self.moves += 1
        px = self.pool.position_x
        py = self.pool.position_y
        vx = self.pool.velocity_x
        vy = self.pool.velocity_y

        for idx in self.pool.iter_alive_indices():
            px[idx] += vx[idx] * dt
            py[idx] += vy[idx] * dt


class DecisionSimulationSystem(System):
    """Sistema sintético de decisão/estado em baixa frequência (10Hz)."""
    def __init__(self, pool: SimulationEntityPool) -> None:
        super().__init__()
        self.pool = pool
        self.decisions = 0

    def update(self, scene, dt: float) -> None:
        self.decisions += 1
        states = self.pool.state
        for idx in self.pool.iter_alive_indices():
            states[idx] = (states[idx] + 1) % 10


def test_scheduler_and_pool_multirate_integration():
    pool = SimulationEntityPool(initial_capacity=1024)
    for i in range(1000):
        pool.create(position=(0.0, 0.0), velocity=(10.0, 5.0), state=0)

    scheduler = SystemScheduler()
    move_sys = MovementSimulationSystem(pool)
    dec_sys = DecisionSimulationSystem(pool)

    # Move a 60Hz, Decisões a 10Hz
    scheduler.register(move_sys, TickPolicy.fixed_hz(60), priority=100)
    scheduler.register(dec_sys, TickPolicy.fixed_hz(10), priority=200)

    # Simula 1 segundo com frames de 1/60s
    dt = 1.0 / 60.0
    for _ in range(60):
        scheduler.update(None, dt)

    assert move_sys.moves == 60
    assert dec_sys.decisions == 10

    # Verifica posições após 60 ticks de 1/60s (total 1.0s de movimento)
    idx_0 = pool.iter_alive_indices()[0]
    assert pytest.approx(pool.position_x[idx_0], 0.01) == 10.0
    assert pytest.approx(pool.position_y[idx_0], 0.01) == 5.0

    # Estado modificado 10 vezes a 10Hz
    assert pool.state[idx_0] == 0  # (0 + 10) % 10 == 0


def test_benchmark_scaling_report():
    """Gera medições de benchmark para 100, 1000, 5000 e 10000 entidades."""
    counts = [100, 1000, 5000, 10000]
    results = {}

    for count in counts:
        # Create
        t0 = time.perf_counter()
        pool = SimulationEntityPool(initial_capacity=count)
        handles = [pool.create(position=(float(i), float(i)), velocity=(1.0, 1.0)) for i in range(count)]
        create_time = time.perf_counter() - t0

        # Movement iteration (100 frames)
        t0 = time.perf_counter()
        px = pool.position_x
        py = pool.position_y
        vx = pool.velocity_x
        vy = pool.velocity_y
        dt = 0.016
        for _ in range(100):
            for idx in pool.iter_alive_indices():
                px[idx] += vx[idx] * dt
                py[idx] += vy[idx] * dt
        move_time = time.perf_counter() - t0

        # Destroy half
        t0 = time.perf_counter()
        for h in handles[:count // 2]:
            pool.destroy(h)
        destroy_time = time.perf_counter() - t0

        # Recreate
        t0 = time.perf_counter()
        for i in range(count // 2):
            pool.create(position=(0.0, 0.0))
        recreate_time = time.perf_counter() - t0

        results[count] = {
            "create_s": create_time,
            "move_100_frames_s": move_time,
            "destroy_half_s": destroy_time,
            "recreate_s": recreate_time,
        }

    assert results[10000]["create_s"] < 1.0
    assert results[10000]["move_100_frames_s"] < 2.0
