"""Testes unitários e semânticos para FlowField2D (Phase 11 - Item 11.5)."""
from __future__ import annotations

import math
import pytest
from engine.simulation.flow_field import FlowField2D
from engine.simulation.navigation_grid import NavigationGrid2D


def test_flow_field_build_goal_and_bounds_validation():
    grid = NavigationGrid2D(width=10, height=10)
    flow = FlowField2D(grid)

    assert flow.is_valid is False
    assert flow.is_stale() is True

    # Goal fora dos limites
    with pytest.raises(ValueError, match="fora dos limites"):
        flow.build((15, 5))

    # Goal bloqueado
    grid.set_walkable(5, 5, False)
    with pytest.raises(ValueError, match="bloqueada"):
        flow.build((5, 5))

    # Build válido
    grid.set_walkable(5, 5, True)
    flow.build((5, 5))
    assert flow.is_valid is True
    assert flow.is_stale() is False
    assert flow.goal == (5, 5)

    # Goal integration == 0 e direction == (0, 0)
    assert flow.get_integration(5, 5) == 0.0
    assert flow.get_direction(5, 5) == (0, 0)


def test_flow_field_straight_corridor_and_obstacles():
    # Grid 5x1 (corredor horizontal) com goal em (4, 0)
    grid = NavigationGrid2D(width=5, height=1)
    flow = FlowField2D(grid)
    flow.build((4, 0))

    # De (0,0) até (3,0) a direção deve ser apontar para a direita (+1, 0)
    for x in range(4):
        assert flow.get_direction(x, 0) == (1, 0)
        assert flow.get_integration(x, 0) == float(4 - x)

    # Goal (4,0)
    assert flow.get_direction(4, 0) == (0, 0)
    assert flow.get_integration(4, 0) == 0.0


def test_flow_field_wall_navigation_and_unreachable():
    grid = NavigationGrid2D(width=5, height=5)
    # Parede em x=2 com abertura em y=4
    for y in range(4):
        grid.set_walkable(2, y, False)

    flow = FlowField2D(grid)
    flow.build((4, 0))

    # A célula (0, 0) deve apontar para baixo (0, 1) para contornar a parede pela abertura
    assert flow.get_direction(0, 0) == (0, 1)

    # Bloqueia a abertura em (2, 4) -> (0, 0) torna-se inalcançável
    grid.set_walkable(2, 4, False)
    assert flow.is_stale() is True

    # Rebuild
    flow.rebuild()
    assert flow.is_stale() is False
    assert math.isinf(flow.get_integration(0, 0))
    assert flow.get_direction(0, 0) == (0, 0)


def test_flow_field_stale_detection_and_no_hidden_rebuild():
    grid = NavigationGrid2D(width=5, height=5)
    flow = FlowField2D(grid)
    flow.build((4, 4))
    assert flow.is_stale() is False

    # Mutação no grid
    grid.set_walkable(2, 2, False)
    assert flow.is_stale() is True

    # Consulta NÃO dispara rebuild oculto
    assert flow.grid_revision != grid.revision
    _ = flow.get_direction(0, 0)
    assert flow.is_stale() is True  # Permanece stale até rebuild explícito!

    flow.rebuild()
    assert flow.is_stale() is False
    assert flow.grid_revision == grid.revision


def test_flow_field_determinism():
    grid = NavigationGrid2D(width=10, height=10)
    flow1 = FlowField2D(grid)
    flow2 = FlowField2D(grid)

    flow1.build((9, 9))
    flow2.build((9, 9))

    for cy in range(10):
        for cx in range(10):
            assert flow1.get_integration(cx, cy) == flow2.get_integration(cx, cy)
            assert flow1.get_direction(cx, cy) == flow2.get_direction(cx, cy)
