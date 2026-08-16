"""engine/simulation/navigation_grid.py
────────────────────────────────────────────────────────────────
Grade lógica densa e delimitada para navegação 2D em simulações.

Oferece:
  - Dimensões explícitas (width, height) e cell_size configurável
  - Armazenamento contíguo para navegabilidade e custos de travessia
  - Conversão de coordenadas de mundo <-> grade (centro exato da célula)
  - Vizinhança determinística em 4 direções (N, S, E, W)
  - Contador de revisão de mutações para sincronização eficiente
  - Desacoplamento total de Qt, GameObject, Physics, LogicGraph e Threads.
"""
from __future__ import annotations

import math
from typing import Iterator, List, Optional, Tuple

GridCoord = Tuple[int, int]


class NavigationGrid2D:
    """
    Grade bidimensional densa e delimitada para pathfinding.
    """

    def __init__(
        self,
        width: int,
        height: int,
        cell_size: float = 32.0,
        default_walkable: bool = True,
        default_cost: float = 1.0,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError(f"Dimensões do grid devem ser estritamente positivas: width={width}, height={height}")
        if not isinstance(cell_size, (int, float)) or math.isnan(cell_size) or math.isinf(cell_size) or cell_size <= 0.0:
            raise ValueError(f"cell_size deve ser numérico e > 0: {cell_size}")
        if default_cost < 1.0 or math.isnan(default_cost) or math.isinf(default_cost):
            raise ValueError(f"default_cost deve ser >= 1.0: {default_cost}")

        self.width: int = int(width)
        self.height: int = int(height)
        self.cell_size: float = float(cell_size)
        self._inv_cell_size: float = 1.0 / self.cell_size

        self.revision: int = 0
        total_cells = self.width * self.height

        # Armazenamento contíguo linear: idx = cy * width + cx
        self._walkable: List[bool] = [bool(default_walkable)] * total_cells
        self._cost: List[float] = [float(default_cost)] * total_cells

    def in_bounds(self, cx: int, cy: int) -> bool:
        """Verifica se as coordenadas de célula estão dentro dos limites do grid."""
        return 0 <= cx < self.width and 0 <= cy < self.height

    def _index(self, cx: int, cy: int) -> int:
        return cy * self.width + cx

    def world_to_cell(self, x: float, y: float) -> GridCoord:
        """Mapeia posição contínua do mundo (x, y) para a célula inteira (cx, cy)."""
        return math.floor(x * self._inv_cell_size), math.floor(y * self._inv_cell_size)

    def cell_to_world(self, cx: int, cy: int) -> Tuple[float, float]:
        """Retorna o centro exato no mundo da célula (cx, cy)."""
        return (cx + 0.5) * self.cell_size, (cy + 0.5) * self.cell_size

    def is_walkable(self, cx: int, cy: int) -> bool:
        """Retorna se a célula é transitável. Fora dos limites retorna False."""
        if not self.in_bounds(cx, cy):
            return False
        return self._walkable[self._index(cx, cy)]

    def set_walkable(self, cx: int, cy: int, value: bool) -> None:
        """Define a transitabilidade de uma célula. Fora dos limites lança IndexError."""
        if not self.in_bounds(cx, cy):
            raise IndexError(f"Célula fora dos limites do grid: ({cx}, {cy}) para grid de {self.width}x{self.height}")

        idx = self._index(cx, cy)
        val = bool(value)
        if self._walkable[idx] != val:
            self._walkable[idx] = val
            self.revision += 1

    def get_cost(self, cx: int, cy: int) -> float:
        """Retorna o custo de travessia para entrar na célula (cx, cy)."""
        if not self.in_bounds(cx, cy):
            raise IndexError(f"Célula fora dos limites: ({cx}, {cy})")
        return self._cost[self._index(cx, cy)]

    def set_cost(self, cx: int, cy: int, cost: float) -> None:
        """Define o custo de travessia para entrar na célula (cx, cy). Requer cost >= 1.0."""
        if not self.in_bounds(cx, cy):
            raise IndexError(f"Célula fora dos limites: ({cx}, {cy})")
        if not isinstance(cost, (int, float)) or math.isnan(cost) or math.isinf(cost) or cost < 1.0:
            raise ValueError(f"Custo de travessia deve ser numérico e >= 1.0. Recebido: {cost}")

        idx = self._index(cx, cy)
        c = float(cost)
        if self._cost[idx] != c:
            self._cost[idx] = c
            self.revision += 1

    def neighbors(self, cx: int, cy: int) -> Iterator[GridCoord]:
        """Gera vizinhos transitáveis em 4 direções (N, S, E, W)."""
        # Ordem fixa: Norte, Sul, Leste, Oeste
        candidates = ((cx, cy - 1), (cx, cy + 1), (cx + 1, cy), (cx - 1, cy))
        for nx, ny in candidates:
            if self.is_walkable(nx, ny):
                yield nx, ny
