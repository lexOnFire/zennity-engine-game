"""Testes de equivalência de custo e alcance de destino entre FlowField2D e AStarPathfinder."""
from __future__ import annotations

import random
import pytest
from engine.simulation.astar import AStarPathfinder
from engine.simulation.flow_field import FlowField2D
from engine.simulation.navigation_grid import NavigationGrid2D


def test_flow_field_vs_astar_cost_equivalence():
    rng = random.Random(42)
    grid = NavigationGrid2D(width=12, height=12)

    # Obstáculos e custos randômicos
    for cx in range(12):
        for cy in range(12):
            if rng.random() < 0.2:
                grid.set_walkable(cx, cy, False)
            elif rng.random() < 0.25:
                grid.set_cost(cx, cy, rng.uniform(2.0, 6.0))

    goal = (11, 11)
    grid.set_walkable(goal[0], goal[1], True)

    flow = FlowField2D(grid)
    flow.build(goal)

    # Para múltiplos pontos de partida navegáveis:
    for _ in range(25):
        start = (rng.randint(0, 11), rng.randint(0, 11))
        if not grid.is_walkable(start[0], start[1]):
            continue

        astar_path = AStarPathfinder.find_path(grid, start, goal)
        flow_integration = flow.get_integration(start[0], start[1])

        if not astar_path:
            assert flow_integration == float("inf")
        else:
            astar_cost = sum(grid.get_cost(c[0], c[1]) for c in astar_path[1:])
            assert pytest.approx(flow_integration, 0.001) == astar_cost


def test_flow_field_path_following_reaches_goal():
    grid = NavigationGrid2D(width=10, height=10)
    # Adiciona algumas barreiras internas
    for y in range(2, 8):
        grid.set_walkable(5, y, False)

    goal = (9, 9)
    flow = FlowField2D(grid)
    flow.build(goal)

    start = (0, 0)
    current = start
    steps = 0
    max_steps = 100

    visited = [current]
    while current != goal and steps < max_steps:
        dx, dy = flow.get_direction(current[0], current[1])
        assert (dx, dy) != (0, 0), "Parou em célula intermediária sem direção!"
        current = (current[0] + dx, current[1] + dy)
        assert grid.is_walkable(current[0], current[1]), "Atravessou célula bloqueada!"
        visited.append(current)
        steps += 1

    assert current == goal
    assert steps < max_steps, "Entrou em loop infinito ou excedeu passos máximos!"
