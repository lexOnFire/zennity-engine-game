"""Testes de integração com SystemScheduler e comparação de baseline GameObject."""
from __future__ import annotations

import time
import pygame
import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.render_batch import BatchedSimulationRenderer, SimulationRenderBuffer
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.system import System


class RenderSyncSimulationSystem(System):
    """Sincroniza o render buffer a cada frame (60Hz)."""
    def __init__(self, pool: SimulationEntityPool, buffer: SimulationRenderBuffer) -> None:
        super().__init__()
        self.pool = pool
        self.buffer = buffer
        self.syncs = 0

    def update(self, scene, dt: float) -> None:
        self.syncs += 1
        self.buffer.sync_from_pool(self.pool, sprite_id=1)


def test_scheduler_render_integration():
    pool = SimulationEntityPool(initial_capacity=100)
    for _ in range(50):
        pool.create(position=(0.0, 0.0))

    buf = SimulationRenderBuffer(initial_capacity=100)
    sync_sys = RenderSyncSimulationSystem(pool, buf)

    scheduler = SystemScheduler()
    scheduler.register(sync_sys, TickPolicy.every_frame(), priority=300)

    # 10 frames
    for _ in range(10):
        scheduler.update(None, 0.016)

    assert sync_sys.syncs == 10
    assert buf.count == 50
