"""engine/simulation/flow_field.py
────────────────────────────────────────────────────────────────
Infraestrutura de navegação coletiva baseada em FlowField 2D.

Oferece:
  - Cálculo de Integration Field ponderado (Dijkstra reverso via heapq)
  - Geração de Direction Field discreto (4-way) com desempate determinístico
  - Consultas em O(1) estrito por coordenadas discretas ou mundo contínuo
  - Rastreamento estrito de revisão (is_stale) sem reconstrução oculta em consultas
  - Desacoplamento total de Qt, GameObject, Physics, LogicGraph e Threads.
"""
from __future__ import annotations

import heapq
import math
from typing import List, Optional, Tuple
from engine.simulation.navigation_grid import GridCoord, NavigationGrid2D

Direction = Tuple[int, int]


class FlowField2D:
    """
    Campo de fluxo e navegação vetorial derivado de um NavigationGrid2D.
    """

    def __init__(self, grid: NavigationGrid2D) -> None:
        self.grid: NavigationGrid2D = grid
        self._goal: Optional[GridCoord] = None
        self._grid_revision: int = -1
        self._is_valid: bool = False

        total_cells = self.grid.width * self.grid.height
        # Integration field: menor custo acumulado até o goal (math.inf = inalcançável/bloqueado)
        self._integration: List[float] = [math.inf] * total_cells
        # Direction field: vetor discreto unitário 4-way apontando para o melhor vizinho
        self._directions: List[Direction] = [(0, 0)] * total_cells

    @property
    def goal(self) -> Optional[GridCoord]:
        """Objetivo atualmente registrado."""
        return self._goal

    @property
    def grid_revision(self) -> int:
        """Revisão do grid capturada no último build."""
        return self._grid_revision

    @property
    def is_valid(self) -> bool:
        """Indica se o field foi construído com sucesso."""
        return self._is_valid

    def is_stale(self) -> bool:
        """Indica se o field está desatualizado em relação à revisão atual do grid."""
        if not self._is_valid:
            return True
        return self.grid.revision != self._grid_revision

    def _index(self, cx: int, cy: int) -> int:
        return cy * self.grid.width + cx

    def build(self, goal: GridCoord) -> None:
        """
        Calcula o Integration Field e o Direction Field para o objetivo informado.
        Lança ValueError se o goal for inválido ou não transitável.
        """
        gx, gy = goal
        if not self.grid.in_bounds(gx, gy):
            raise ValueError(f"Goal fora dos limites do grid: ({gx}, {gy})")
        if not self.grid.is_walkable(gx, gy):
            raise ValueError(f"Goal está em uma célula bloqueada/não transitável: ({gx}, {gy})")

        self._goal = (gx, gy)
        self._grid_revision = self.grid.revision
        w = self.grid.width
        h = self.grid.height
        total_cells = w * h

        # Reseta arrays lineares
        self._integration = [math.inf] * total_cells
        self._directions = [(0, 0)] * total_cells

        # 1. Integration Field: Dijkstra reverso a partir do goal
        # Na propagação reversa:
        # Se estamos na célula 'curr' (com integration cost I(curr)) e expandimos para o vizinho 'nbr',
        # mover de 'nbr' para 'curr' adiciona o custo de ENTRAR em 'curr' (grid.get_cost(curr)).
        # Portanto: I(nbr) = I(curr) + grid.get_cost(curr).
        # Para o goal, I(goal) = 0.0.
        goal_idx = self._index(gx, gy)
        self._integration[goal_idx] = 0.0

        pq: List[Tuple[float, int, int, int]] = []
        insertion_counter = 0
        heapq.heappush(pq, (0.0, insertion_counter, gx, gy))
        insertion_counter += 1

        while pq:
            cost, _, cx, cy = heapq.heappop(pq)
            idx = self._index(cx, cy)
            if cost > self._integration[idx]:
                continue

            # Custo de entrar na célula atual vindo de um vizinho
            step_cost = self.grid.get_cost(cx, cy)

            # Inspeciona os 4 vizinhos (N, S, E, W)
            candidates = ((cx, cy - 1), (cx, cy + 1), (cx + 1, cy), (cx - 1, cy))
            for nx, ny in candidates:
                if not self.grid.is_walkable(nx, ny):
                    continue

                n_idx = self._index(nx, ny)
                tentative_cost = cost + step_cost
                if tentative_cost < self._integration[n_idx]:
                    self._integration[n_idx] = tentative_cost
                    heapq.heappush(pq, (tentative_cost, insertion_counter, nx, ny))
                    insertion_counter += 1

        # 2. Direction Field: Para cada célula navegável, aponta para o vizinho que minimiza (I(nbr) + get_cost(nbr))
        # Ordem fixa determinística de avaliação de vizinhos: N, S, E, W
        neighbor_offsets = ((0, -1), (0, 1), (1, 0), (-1, 0))

        for cy in range(h):
            for cx in range(w):
                if (cx, cy) == (gx, gy):
                    # No goal a direção é repouso (0, 0)
                    self._directions[self._index(cx, cy)] = (0, 0)
                    continue

                idx = self._index(cx, cy)
                current_integration = self._integration[idx]
                if math.isinf(current_integration):
                    # Inalcançável ou bloqueada
                    self._directions[idx] = (0, 0)
                    continue

                best_dir: Direction = (0, 0)
                best_cost = math.inf

                for dx, dy in neighbor_offsets:
                    nx, ny = cx + dx, cy + dy
                    if self.grid.in_bounds(nx, ny) and self.grid.is_walkable(nx, ny):
                        n_idx = self._index(nx, ny)
                        n_integration = self._integration[n_idx]
                        if not math.isinf(n_integration):
                            # Custo total para chegar ao goal passando pelo vizinho:
                            # custo de entrar no vizinho + custo acumulado do vizinho até o goal
                            total_path_cost = n_integration + self.grid.get_cost(nx, ny)
                            if total_path_cost < best_cost:
                                best_cost = total_path_cost
                                best_dir = (dx, dy)

                self._directions[idx] = best_dir

        self._is_valid = True

    def rebuild(self) -> None:
        """Reconstrói o FlowField utilizando o goal registrado."""
        if self._goal is None:
            raise RuntimeError("Nenhum goal registrado para rebuild.")
        self.build(self._goal)

    def get_integration(self, cx: int, cy: int) -> float:
        """Retorna o custo acumulado de integração da célula (cx, cy) em O(1)."""
        if not self._is_valid or not self.grid.in_bounds(cx, cy):
            return math.inf
        return self._integration[self._index(cx, cy)]

    def get_direction(self, cx: int, cy: int) -> Direction:
        """Retorna o vetor de direção 4-way da célula (cx, cy) em O(1)."""
        if not self._is_valid or not self.grid.in_bounds(cx, cy):
            return (0, 0)
        return self._directions[self._index(cx, cy)]

    def get_direction_world(self, x: float, y: float) -> Direction:
        """Converte a posição contínua de mundo para célula e retorna a direção em O(1)."""
        cx, cy = self.grid.world_to_cell(x, y)
        return self.get_direction(cx, cy)
