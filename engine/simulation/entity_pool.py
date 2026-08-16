"""engine/simulation/entity_pool.py
────────────────────────────────────────────────────────────────
Pool de entidades leves de simulação baseado em Structure of Arrays (SoA).

Oferece:
  - EntityHandle(index, generation) imutável e hashable
  - Armazenamento contíguo em vetores primitivos para escala
  - Alocação/desalocação O(1) com free-list
  - Iteração densa O(N_alive) com swap-remove O(1)
  - Prevenção estrita de stale handles por geração
  - Desacoplamento total de Qt, GameObject, LogicGraph, Blackboard e Threads.
"""
from __future__ import annotations

from typing import Any, Iterator, List, NamedTuple, Optional, Tuple


class EntityHandle(NamedTuple):
    """
    Identificador estável e imutável para uma entidade de simulação.
    Composto pelo índice do slot e o número de geração.
    """
    index: int
    generation: int

    def __repr__(self) -> str:
        return f"EntityHandle(idx={self.index}, gen={self.generation})"


class SimulationEntityPool:
    """
    Pool de entidades leves para simulação em massa usando Structure of Arrays (SoA).
    """

    def __init__(self, initial_capacity: int = 1024) -> None:
        if initial_capacity < 1:
            raise ValueError("initial_capacity deve ser >= 1")

        self._capacity: int = initial_capacity
        self._alive_count: int = 0

        # Structure of Arrays (SoA)
        self.position_x: List[float] = [0.0] * self._capacity
        self.position_y: List[float] = [0.0] * self._capacity
        self.velocity_x: List[float] = [0.0] * self._capacity
        self.velocity_y: List[float] = [0.0] * self._capacity
        self.state: List[int] = [0] * self._capacity
        self.flags: List[int] = [0] * self._capacity
        self.generation: List[int] = [1] * self._capacity
        self.alive: List[bool] = [False] * self._capacity

        # Free-list para reaproveitamento O(1) de slots
        self._free_indices: List[int] = list(range(self._capacity - 1, -1, -1))

        # Packed active list com mapa reverso para swap-remove O(1)
        self._active_indices: List[int] = []
        self._active_map: List[int] = [-1] * self._capacity

    @property
    def capacity(self) -> int:
        """Capacidade total de slots alocados."""
        return self._capacity

    @property
    def alive_count(self) -> int:
        """Número de entidades ativas/vivas no pool."""
        return self._alive_count

    def _grow(self) -> None:
        """Dobra a capacidade interna dos vetores."""
        old_cap = self._capacity
        new_cap = old_cap * 2
        additional = new_cap - old_cap

        self.position_x.extend([0.0] * additional)
        self.position_y.extend([0.0] * additional)
        self.velocity_x.extend([0.0] * additional)
        self.velocity_y.extend([0.0] * additional)
        self.state.extend([0] * additional)
        self.flags.extend([0] * additional)
        self.generation.extend([1] * additional)
        self.alive.extend([False] * additional)
        self._active_map.extend([-1] * additional)

        # Adiciona novos slots à free-list
        for i in range(new_cap - 1, old_cap - 1, -1):
            self._free_indices.append(i)

        self._capacity = new_cap

    def create(
        self,
        position: Tuple[float, float] = (0.0, 0.0),
        velocity: Tuple[float, float] = (0.0, 0.0),
        state: int = 0,
        flags: int = 0,
    ) -> EntityHandle:
        """Cria uma entidade leve e retorna seu EntityHandle em O(1) amortizado."""
        if not self._free_indices:
            self._grow()

        idx = self._free_indices.pop()
        gen = self.generation[idx]

        # Inicializa valores (reseta dados de reuso anterior)
        self.position_x[idx] = float(position[0])
        self.position_y[idx] = float(position[1])
        self.velocity_x[idx] = float(velocity[0])
        self.velocity_y[idx] = float(velocity[1])
        self.state[idx] = int(state)
        self.flags[idx] = int(flags)
        self.alive[idx] = True

        # Adiciona na lista densa de ativos em O(1)
        active_pos = len(self._active_indices)
        self._active_indices.append(idx)
        self._active_map[idx] = active_pos
        self._alive_count += 1

        return EntityHandle(index=idx, generation=gen)

    def is_alive(self, handle: EntityHandle) -> bool:
        """Verifica se o handle é válido e a entidade está viva em O(1)."""
        idx = handle.index
        if idx < 0 or idx >= self._capacity:
            return False
        if not self.alive[idx]:
            return False
        return self.generation[idx] == handle.generation

    def destroy(self, handle: EntityHandle) -> bool:
        """Destrói uma entidade em O(1) estrito usando swap-remove."""
        if not self.is_alive(handle):
            return False

        idx = handle.index
        self.alive[idx] = False
        self.generation[idx] += 1  # Invalida stale handles

        # Swap-remove da lista de ativos em O(1)
        active_pos = self._active_map[idx]
        last_idx = self._active_indices.pop()
        if active_pos < len(self._active_indices):
            self._active_indices[active_pos] = last_idx
            self._active_map[last_idx] = active_pos
        self._active_map[idx] = -1

        # Retorna slot para a free-list
        self._free_indices.append(idx)
        self._alive_count -= 1
        return True

    def clear(self) -> None:
        """Invalida todas as entidades vivas e reseta a lista de ativos."""
        for idx in self._active_indices:
            self.alive[idx] = False
            self.generation[idx] += 1
            self._active_map[idx] = -1
            self._free_indices.append(idx)

        self._active_indices.clear()
        self._alive_count = 0

    def iter_alive_indices(self) -> List[int]:
        """Retorna lista contígua de índices ativos para loops de alta performance."""
        return self._active_indices

    def iter_alive_handles(self) -> Iterator[EntityHandle]:
        """Gera handles para todas as entidades vivas."""
        for idx in self._active_indices:
            yield EntityHandle(index=idx, generation=self.generation[idx])

    def get_position(self, handle: EntityHandle) -> Tuple[float, float]:
        if not self.is_alive(handle):
            raise KeyError(f"Handle inválido ou entidade morta: {handle}")
        idx = handle.index
        return self.position_x[idx], self.position_y[idx]

    def set_position(self, handle: EntityHandle, x: float, y: float) -> None:
        if not self.is_alive(handle):
            raise KeyError(f"Handle inválido ou entidade morta: {handle}")
        idx = handle.index
        self.position_x[idx] = float(x)
        self.position_y[idx] = float(y)

    def get_velocity(self, handle: EntityHandle) -> Tuple[float, float]:
        if not self.is_alive(handle):
            raise KeyError(f"Handle inválido ou entidade morta: {handle}")
        idx = handle.index
        return self.velocity_x[idx], self.velocity_y[idx]

    def set_velocity(self, handle: EntityHandle, vx: float, vy: float) -> None:
        if not self.is_alive(handle):
            raise KeyError(f"Handle inválido ou entidade morta: {handle}")
        idx = handle.index
        self.velocity_x[idx] = float(vx)
        self.velocity_y[idx] = float(vy)
