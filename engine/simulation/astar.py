"""engine/simulation/astar.py
────────────────────────────────────────────────────────────────
Algoritmo A* determinístico e ótimo sobre NavigationGrid2D.

Oferece:
  - Fila de prioridades com heapq e desempate estável
  - Heurística Manhattan admissível com custo mínimo garantido (>= 1.0)
  - Limite opcional de expansões (search budget)
  - Retorno de caminho ótimo em lista de GridCoord de start até goal.
"""
from __future__ import annotations

import heapq
from typing import Any, Dict, List, Optional, Set, Tuple
from engine.simulation.navigation_grid import GridCoord, NavigationGrid2D


class AStarPathfinder:
    """
    Localizador de caminhos A* determinístico sobre grades 2D.
    """

    @staticmethod
    def _heuristic(a: GridCoord, b: GridCoord) -> float:
        """Heurística Manhattan admissível para movimentação em 4 direções."""
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    @classmethod
    def find_path(
        cls,
        grid: NavigationGrid2D,
        start: GridCoord,
        goal: GridCoord,
        max_expansions: Optional[int] = None,
    ) -> List[GridCoord]:
        """
        Encontra o caminho ótimo de menor custo entre 'start' e 'goal'.
        Retorna lista de GridCoord de start até goal, ou [] se inalcançável.
        """
        # Validações preliminares
        if not grid.is_walkable(start[0], start[1]) or not grid.is_walkable(goal[0], goal[1]):
            return []

        if start == goal:
            return [start]

        if max_expansions is not None and max_expansions <= 0:
            raise ValueError(f"max_expansions deve ser positivo se fornecido: {max_expansions}")

        # Open Set: tuplas (f_score, h_score, insertion_counter, coord)
        open_set: List[Tuple[float, float, int, GridCoord]] = []
        insertion_counter = 0

        h_start = cls._heuristic(start, goal)
        heapq.heappush(open_set, (h_start, h_start, insertion_counter, start))
        insertion_counter += 1

        came_from: Dict[GridCoord, GridCoord] = {}
        g_score: Dict[GridCoord, float] = {start: 0.0}
        closed_set: Set[GridCoord] = set()

        expansions = 0

        while open_set:
            if max_expansions is not None and expansions >= max_expansions:
                return []  # Search budget estourado

            current_f, current_h, _, current = heapq.heappop(open_set)

            if current in closed_set:
                continue

            if current == goal:
                # Reconstrói o caminho de start até goal
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path

            closed_set.add(current)
            expansions += 1
            current_g = g_score[current]

            for neighbor in grid.neighbors(current[0], current[1]):
                if neighbor in closed_set:
                    continue

                # Custo de travessia para entrar na célula vizinha
                step_cost = grid.get_cost(neighbor[0], neighbor[1])
                tentative_g = current_g + step_cost

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = cls._heuristic(neighbor, goal)
                    f = tentative_g + h
                    heapq.heappush(open_set, (f, h, insertion_counter, neighbor))
                    insertion_counter += 1

        return []
