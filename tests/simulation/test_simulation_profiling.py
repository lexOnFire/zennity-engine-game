"""Testes de profiling e contadores de trabalho da simulação (Phase 12 - Item 12.1)."""
from __future__ import annotations

import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.spatial_hash import SpatialHash2D
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.system import System


def test_spatial_hash_profiling_counters():
    sh = SpatialHash2D(cell_size=50.0)
    pool = SimulationEntityPool(initial_capacity=10)

    h1 = pool.create(position=(10.0, 10.0))
    h2 = pool.create(position=(20.0, 20.0))

    # Inserts
    sh.insert(h1, 10.0, 10.0)
    sh.insert(h2, 20.0, 20.0)

    # Updates: same cell vs cell transition
    # (10, 10) -> (15, 15) está na mesma célula (0, 0)
    sh.update(h1, 15.0, 15.0)
    # (20, 20) -> (80, 80) atravessa para a célula (1, 1)
    sh.update(h2, 80.0, 80.0)

    # Query
    res = sh.query_radius(15.0, 15.0, radius=20.0, pool=pool)
    assert len(res) == 1

    # Remove
    sh.remove(h1)

    stats = sh.get_profiling_stats()
    assert stats["insert_calls"] == 2
    assert stats["update_calls"] == 2
    assert stats["same_cell_updates"] == 1
    assert stats["cell_transitions"] == 1
    assert stats["query_calls"] == 1
    assert stats["candidate_entities_evaluated"] >= 1
    assert stats["remove_calls"] == 1

    # Reset
    sh.reset_profiling_stats()
    reset_stats = sh.get_profiling_stats()
    assert reset_stats["update_calls"] == 0
    assert reset_stats["same_cell_updates"] == 0
    assert reset_stats["cell_transitions"] == 0
    # Assegura que a entidade restante continua indexada e funcional
    assert sh.entity_count == 1


class DummySys60(System):
    def update(self, scene, dt: float) -> None:
        pass


class DummySys10(System):
    def update(self, scene, dt: float) -> None:
        pass


def test_scheduler_frame_metrics_and_tick_coincidence():
    scheduler = SystemScheduler()
    s60 = DummySys60()
    s10 = DummySys10()

    scheduler.register(s60, TickPolicy.fixed_hz(60), priority=100)
    scheduler.register(s10, TickPolicy.fixed_hz(10), priority=200)

    # Executa frames com dt = 0.01666 (60Hz exato)
    coincidences = 0
    executed_frames = 0
    for _ in range(60):
        scheduler.update(None, 1.0 / 60.0)
        m = scheduler.get_last_frame_metrics()
        if m["systems_executed_this_frame"] > 0:
            executed_frames += 1
        if m["systems_executed_this_frame"] == 2:
            coincidences += 1

    assert executed_frames >= 50
    assert coincidences >= 5  # Coincide cerca de 10 vezes em 1 segundo
