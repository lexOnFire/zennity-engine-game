"""Testes de semântica de custos e equivalência de terreno ponderado do FlowField2D."""
from __future__ import annotations

import pytest
from engine.simulation.flow_field import FlowField2D
from engine.simulation.navigation_grid import NavigationGrid2D


def test_flow_field_weighted_cost_detour():
    grid = NavigationGrid2D(width=5, height=5)
    # Linha direta de (0,1) até (3,1) com custo muito alto (10.0)
    for x in range(1, 4):
        grid.set_cost(x, 1, 10.0)

    flow = FlowField2D(grid)
    flow.build((4, 1))

    # A partir de (0, 1), o FlowField deve direcionar para o terreno barato (y=0 ou y=2) em vez da linha direta cara
    dir_0_1 = flow.get_direction(0, 1)
    assert dir_0_1 in {(0, -1), (0, 1)}  # Desvio para cima ou para baixo!


def test_flow_field_cost_mutation_and_rebuild():
    grid = NavigationGrid2D(width=5, height=5)
    flow = FlowField2D(grid)
    flow.build((4, 4))

    # Custo inicial padrão
    init_cost_0_0 = flow.get_integration(0, 0)

    # Aumenta o custo de várias células no caminho
    for x in range(5):
        grid.set_cost(x, 2, 4.0)

    assert flow.is_stale() is True

    # Rebuild
    flow.rebuild()
    assert flow.is_stale() is False
    assert flow.get_integration(0, 0) > init_cost_0_0
