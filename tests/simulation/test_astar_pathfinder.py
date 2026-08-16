"""Testes unitários e oráculo de otimalidade para AStarPathfinder (Phase 11 - Item 11.4)."""
from __future__ import annotations

import heapq
import random
import pytest
from engine.simulation.astar import AStarPathfinder
from engine.simulation.navigation_grid import GridCoord, NavigationGrid2D


def _dijkstra_oracle(grid: NavigationGrid2D, start: GridCoord, goal: GridCoord) -> Tuple[Optional[float], List[GridCoord]]:
    """Oráculo de Dijkstra simples e confiável para provar otimalidade do A* em testes."""
    if not grid.is_walkable(start[0], start[1]) or not grid.is_walkable(goal[0], goal[1]):
        return None, []

    if start == goal:
        return 0.0, [start]

    dist = {start: 0.0}
    came_from = {}
    pq = [(0.0, 0, start)]
    counter = 0

    while pq:
        d, _, u = heapq.heappop(pq)
        if d > dist.get(u, float("inf")):
            continue

        if u == goal:
            path = [u]
            while u in came_from:
                u = came_from[u]
                path.append(u)
            path.reverse()
            return d, path

        for v in grid.neighbors(u[0], u[1]):
            cost = grid.get_cost(v[0], v[1])
            new_dist = d + cost
            if new_dist < dist.get(v, float("inf")):
                dist[v] = new_dist
                came_from[v] = u
                counter += 1
                heapq.heappush(pq, (new_dist, counter, v))

    return None, []


def test_astar_straight_and_start_equal_goal():
    grid = NavigationGrid2D(width=5, height=5)
    # Start == Goal
    assert AStarPathfinder.find_path(grid, (2, 2), (2, 2)) == [(2, 2)]

    # Linha reta simples
    path = AStarPathfinder.find_path(grid, (0, 0), (3, 0))
    assert path == [(0, 0), (1, 0), (2, 0), (3, 0)]


def test_astar_blocked_wall_and_no_path():
    grid = NavigationGrid2D(width=5, height=5)
    # Parede vertical cortando o grid na coluna 2 exceto em y=4
    for y in range(4):
        grid.set_walkable(2, y, False)

    # Encontra caminho contornando por baixo (y=4)
    path = AStarPathfinder.find_path(grid, (0, 0), (4, 0))
    assert len(path) > 0
    assert (2, 4) in path  # Passou pela abertura!

    # Fecha a abertura completamente
    grid.set_walkable(2, 4, False)
    assert AStarPathfinder.find_path(grid, (0, 0), (4, 0)) == []


def test_astar_weighted_terrain_optimality():
    grid = NavigationGrid2D(width=5, height=5)
    # Linha direta de (0,1) até (3,1) tem custo alto 10.0
    for x in range(1, 4):
        grid.set_cost(x, 1, 10.0)

    # A* deve desviar pelo caminho mais longo em passos (y=0 ou y=2 com custo 1.0) para minimizar custo total
    path = AStarPathfinder.find_path(grid, (0, 1), (4, 1))
    assert len(path) > 0
    # Não deve passar pelas 3 células caras simultaneamente
    expensive_count = sum(1 for c in path if c in {(1, 1), (2, 1), (3, 1)})
    assert expensive_count == 0


def test_astar_vs_dijkstra_oracle_random_grids():
    """Valida 30 cenários randômicos provando que o custo do A* é 100% ótimo igual ao Dijkstra."""
    rng = random.Random(12345)
    for _ in range(30):
        w, h = rng.randint(8, 15), rng.randint(8, 15)
        grid = NavigationGrid2D(width=w, height=h)

        # Adiciona alguns obstáculos e pesos randômicos
        for cx in range(w):
            for cy in range(h):
                if rng.random() < 0.2:
                    grid.set_walkable(cx, cy, False)
                elif rng.random() < 0.3:
                    grid.set_cost(cx, cy, rng.uniform(2.0, 8.0))

        start = (rng.randint(0, w - 1), rng.randint(0, h - 1))
        goal = (rng.randint(0, w - 1), rng.randint(0, h - 1))

        if not grid.is_walkable(start[0], start[1]) or not grid.is_walkable(goal[0], goal[1]):
            continue

        d_cost, d_path = _dijkstra_oracle(grid, start, goal)
        a_path = AStarPathfinder.find_path(grid, start, goal)

        if d_cost is None:
            assert a_path == []
        else:
            assert len(a_path) > 0
            # Calcula custo do path do A*
            a_cost = sum(grid.get_cost(c[0], c[1]) for c in a_path[1:])
            assert pytest.approx(a_cost, 0.001) == d_cost


def test_astar_search_budget():
    grid = NavigationGrid2D(width=20, height=20)
    # Busca longa com budget muito pequeno deve abortar e retornar []
    path = AStarPathfinder.find_path(grid, (0, 0), (19, 19), max_expansions=5)
    assert path == []
