"""Módulo de simulação, navegação, agendamento e renderização em lote da Zennity Engine."""
from __future__ import annotations

from engine.simulation.system_scheduler import SystemScheduler, TickPolicy
from engine.simulation.entity_pool import EntityHandle, SimulationEntityPool
from engine.simulation.spatial_hash import SpatialHash2D
from engine.simulation.navigation_grid import GridCoord, NavigationGrid2D
from engine.simulation.astar import AStarPathfinder
from engine.simulation.flow_field import FlowField2D
from engine.simulation.render_batch import BatchedSimulationRenderer, SimulationRenderBuffer

__all__ = [
    "AStarPathfinder",
    "BatchedSimulationRenderer",
    "EntityHandle",
    "FlowField2D",
    "GridCoord",
    "NavigationGrid2D",
    "SimulationEntityPool",
    "SimulationRenderBuffer",
    "SpatialHash2D",
    "SystemScheduler",
    "TickPolicy",
]
