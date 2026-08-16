"""Módulo de simulação e agendamento da Zennity Engine."""
from __future__ import annotations

from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.simulation.entity_pool import EntityHandle, SimulationEntityPool
from engine.simulation.spatial_hash import SpatialHash2D

__all__ = [
    "EntityHandle",
    "SimulationEntityPool",
    "SpatialHash2D",
    "SystemScheduler",
    "TickPolicy",
]
