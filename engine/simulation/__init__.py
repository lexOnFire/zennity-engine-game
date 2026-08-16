"""Módulo de simulação e agendamento da Zennity Engine."""
from __future__ import annotations

from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.simulation.entity_pool import EntityHandle, SimulationEntityPool

__all__ = [
    "EntityHandle",
    "SimulationEntityPool",
    "SystemScheduler",
    "TickPolicy",
]
