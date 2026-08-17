"""Testes de integração de Simulation LOD com SystemScheduler (Phase 12 - Item 12.2)."""
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
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.system import System


class LODDecisionSystem(System):
    """Sistema que processa entidades por tier em frequências diferentes."""

    def __init__(self, pool: SimulationEntityPool, lod_mgr: SimulationLODManager, tier: int) -> None:
        super().__init__()
        self.pool = pool
        self.lod_mgr = lod_mgr
        self.tier = tier
        self.updates_executed = 0

    def update(self, scene, dt: float) -> None:
        states = self.pool.state
        for idx in self.lod_mgr.iter_tier(self.tier):
            states[idx] += 1
            self.updates_executed += 1


class LODClassifierSystem(System):
    """Sistema que executa a classificação periódica de LOD."""

    def __init__(self, pool: SimulationEntityPool, lod_mgr: SimulationLODManager, focus: SimulationFocus) -> None:
        super().__init__()
        self.pool = pool
        self.lod_mgr = lod_mgr
        self.focus = focus
        self.classifications = 0

    def update(self, scene, dt: float) -> None:
        self.lod_mgr.classify(self.pool, self.focus)
        self.classifications += 1


def test_lod_scheduler_multirate_tier_dispatch():
    pool = SimulationEntityPool(initial_capacity=100)
    cfg = SimulationLODConfig(high_distance=100.0, medium_distance=300.0, low_distance=600.0, hysteresis_margin=20.0)
    lod_mgr = SimulationLODManager(config=cfg, initial_capacity=100)
    focus = SimulationFocus(0.0, 0.0, enabled=True)

    # 10 entidades HIGH (dist = 50)
    for _ in range(10):
        pool.create(position=(50.0, 0.0))

    # 10 entidades MEDIUM (dist = 200)
    for _ in range(10):
        pool.create(position=(200.0, 0.0))

    # 10 entidades LOW (dist = 450)
    for _ in range(10):
        pool.create(position=(450.0, 0.0))

    # 10 entidades SLEEP (dist = 1000)
    for _ in range(10):
        pool.create(position=(1000.0, 0.0))

    # Classificação inicial
    lod_mgr.classify(pool, focus)

    scheduler = SystemScheduler()
    sys_high = LODDecisionSystem(pool, lod_mgr, LOD_HIGH)
    sys_med = LODDecisionSystem(pool, lod_mgr, LOD_MEDIUM)
    sys_low = LODDecisionSystem(pool, lod_mgr, LOD_LOW)
    sys_classifier = LODClassifierSystem(pool, lod_mgr, focus)

    # Scheduler policies: High=60Hz, Medium=20Hz, Low=5Hz, Classifier=10Hz
    scheduler.register(sys_high, TickPolicy.fixed_hz(60), priority=100)
    scheduler.register(sys_med, TickPolicy.fixed_hz(20), priority=200)
    scheduler.register(sys_low, TickPolicy.fixed_hz(5), priority=300)
    scheduler.register(sys_classifier, TickPolicy.fixed_hz(10), priority=50)

    # Simula 1 segundo (60 frames a dt = 1/60s)
    for _ in range(60):
        scheduler.update(None, 1.0 / 60.0)

    # Verifica número de updates executados
    # HIGH (10 entidades x 60 ticks = ~600 updates)
    assert sys_high.updates_executed >= 580 and sys_high.updates_executed <= 620

    # MEDIUM (10 entidades x 20 ticks = ~200 updates)
    assert sys_med.updates_executed >= 190 and sys_med.updates_executed <= 210

    # LOW (10 entidades x 5 ticks = ~50 updates)
    assert sys_low.updates_executed >= 40 and sys_low.updates_executed <= 60

    # SLEEP (10 entidades x 0 ticks = 0 updates)
    sleep_indices = lod_mgr.get_tier_indices(LOD_SLEEP)
    assert len(sleep_indices) == 10
    for idx in sleep_indices:
        assert pool.state[idx] == 0  # Nenhum update recebido durante o segundo
