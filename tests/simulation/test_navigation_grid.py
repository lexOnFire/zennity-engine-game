"""Testes unitários para NavigationGrid2D (Phase 11 - Item 11.4)."""
from __future__ import annotations

import pytest
from engine.simulation.navigation_grid import NavigationGrid2D


def test_navigation_grid_creation_and_bounds():
    grid = NavigationGrid2D(width=10, height=20, cell_size=16.0)
    assert grid.width == 10
    assert grid.height == 20
    assert grid.cell_size == 16.0
    assert grid.revision == 0

    assert grid.in_bounds(0, 0) is True
    assert grid.in_bounds(9, 19) is True
    assert grid.in_bounds(10, 20) is False
    assert grid.in_bounds(-1, 0) is False

    # Validação de argumentos
    with pytest.raises(ValueError):
        NavigationGrid2D(0, 10)
    with pytest.raises(ValueError):
        NavigationGrid2D(10, -5)
    with pytest.raises(ValueError):
        NavigationGrid2D(10, 10, cell_size=0)


def test_world_to_cell_and_cell_to_world():
    grid = NavigationGrid2D(width=10, height=10, cell_size=32.0)

    # Conversão de mundo para célula
    assert grid.world_to_cell(0.0, 0.0) == (0, 0)
    assert grid.world_to_cell(31.9, 31.9) == (0, 0)
    assert grid.world_to_cell(32.0, 64.0) == (1, 2)
    assert grid.world_to_cell(-1.0, 10.0) == (-1, 0)

    # Centro exato da célula
    assert grid.cell_to_world(0, 0) == (16.0, 16.0)
    assert grid.cell_to_world(1, 2) == (48.0, 80.0)


def test_walkability_mutation_and_revision():
    grid = NavigationGrid2D(width=5, height=5)
    assert grid.is_walkable(2, 2) is True
    assert grid.revision == 0

    # Bloqueia célula (mutação real incrementa revision)
    grid.set_walkable(2, 2, False)
    assert grid.is_walkable(2, 2) is False
    assert grid.revision == 1

    # No-op mutation não incrementa revision
    grid.set_walkable(2, 2, False)
    assert grid.revision == 1

    # Fora dos limites
    assert grid.is_walkable(10, 10) is False
    with pytest.raises(IndexError):
        grid.set_walkable(10, 10, False)


def test_cost_mutation_and_validation():
    grid = NavigationGrid2D(width=5, height=5)
    assert grid.get_cost(1, 1) == 1.0

    # Define custo de terreno elevado
    grid.set_cost(1, 1, 5.5)
    assert grid.get_cost(1, 1) == 5.5
    assert grid.revision == 1

    # Rejeição de custos inválidos (< 1.0, NaN, Inf)
    with pytest.raises(ValueError):
        grid.set_cost(1, 1, 0.5)
    with pytest.raises(ValueError):
        grid.set_cost(1, 1, -1.0)
    with pytest.raises(ValueError):
        grid.set_cost(1, 1, float("nan"))


def test_neighbors_4_way():
    grid = NavigationGrid2D(width=3, height=3)
    # Vizinhos do centro (1, 1): (1,0), (1,2), (2,1), (0,1)
    nbrs = list(grid.neighbors(1, 1))
    assert set(nbrs) == {(1, 0), (1, 2), (2, 1), (0, 1)}

    # Bloqueia o de cima (1, 0)
    grid.set_walkable(1, 0, False)
    nbrs = list(grid.neighbors(1, 1))
    assert set(nbrs) == {(1, 2), (2, 1), (0, 1)}

    # Desbloqueia (1, 0)
    grid.set_walkable(1, 0, True)

    # Vizinhos de um canto (0, 0) respeitam bounds
    corner_nbrs = list(grid.neighbors(0, 0))
    assert set(corner_nbrs) == {(0, 1), (1, 0)}
