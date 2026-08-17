"""engine/simulation/__init__.py
────────────────────────────────────────────────────────────────
Camada de simulação de alto desempenho da Zennity Engine.
"""
from __future__ import annotations

from engine.simulation.astar import AStarPathfinder
from engine.simulation.entity_pool import EntityHandle, SimulationEntityPool
from engine.simulation.flow_field import FlowField2D
from engine.simulation.lod import (
    LOD_HIGH,
    LOD_LOW,
    LOD_MEDIUM,
    LOD_SLEEP,
    TIER_NAMES,
    SimulationFocus,
    SimulationLODConfig,
    SimulationLODManager,
)
from engine.simulation.navigation_grid import NavigationGrid2D
from engine.simulation.render_batch import BatchedSimulationRenderer, SimulationRenderBuffer
from engine.simulation.spatial_hash import SpatialHash2D
from engine.simulation.system_scheduler import SystemScheduler, TickPolicy

__all__ = [
    "SystemScheduler",
    "TickPolicy",
    "EntityHandle",
    "SimulationEntityPool",
    "SpatialHash2D",
    "NavigationGrid2D",
    "AStarPathfinder",
    "FlowField2D",
    "SimulationRenderBuffer",
    "BatchedSimulationRenderer",
    "SimulationFocus",
    "SimulationLODConfig",
    "SimulationLODManager",
    "LOD_HIGH",
    "LOD_MEDIUM",
    "LOD_LOW",
    "LOD_SLEEP",
    "TIER_NAMES",
]
