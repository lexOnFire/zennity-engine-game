"""engine/simulation/spatial_hash.py
────────────────────────────────────────────────────────────────
Particionamento espacial genérico em 2D baseado em Spatial Hashing.

Oferece:
  - Mapeamento uniforme e esparso sem world bounds obrigatório
  - Suporte completo a coordenadas positivas, negativas e fracionárias
  - Inserção, remoção e atualização de células em O(1) amortizado/médio
  - Same-cell inline fast-path com eliminação de alocação de tuplas temporárias
  - sync_from_pool / update_many: sincronização em lote (bulk) de alta velocidade
  - Consultas de célula, retângulo e raio (candidatos e filtragem exata)
  - Integração com SimulationEntityPool com proteção a stale handles
  - Contadores de trabalho e mutação de buckets granulares e passivos
  - Desacoplamento total de Qt, GameObject, Physics, LogicGraph e Threads.
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple, Union

# Tipo genérico para coordenadas de célula
CellCoord = Tuple[int, int]


class SpatialHash2D:
    """
    Estrutura esparsa de indexação espacial em 2D com contadores de profiling integrados.
    """

    def __init__(self, cell_size: float = 64.0) -> None:
        if not isinstance(cell_size, (int, float)):
            raise ValueError(f"cell_size deve ser numérico. Recebido: {type(cell_size).__name__}")
        if math.isnan(cell_size) or math.isinf(cell_size):
            raise ValueError(f"cell_size inválido (NaN ou Inf): {cell_size}")
        if cell_size <= 0.0:
            raise ValueError(f"cell_size deve ser estritamente positivo (> 0). Recebido: {cell_size}")

        self.cell_size: float = float(cell_size)
        self._inv_cell_size: float = 1.0 / self.cell_size

        # _cells: mapeia (cx, cy) -> set de identidades registradas
        self._cells: Dict[CellCoord, Set[Any]] = {}
        # _entity_cells: mapeia entidade -> sua (cx, cy) atual
        self._entity_cells: Dict[Any, CellCoord] = {}

        # Contadores de trabalho e profiling
        self._insert_calls: int = 0
        self._remove_calls: int = 0
        self._update_calls: int = 0
        self._same_cell_updates: int = 0
        self._cell_transitions: int = 0
        self._bucket_mutations: int = 0
        self._query_calls: int = 0
        self._candidate_entities_evaluated: int = 0
        self._bulk_sync_calls: int = 0
        self._bulk_entities_processed: int = 0

    @property
    def entity_count(self) -> int:
        """Número de entidades atualmente indexadas."""
        return len(self._entity_cells)

    @property
    def cell_count(self) -> int:
        """Número de células ativas/ocupadas."""
        return len(self._cells)

    def __len__(self) -> int:
        return len(self._entity_cells)

    def get_profiling_stats(self) -> Dict[str, int]:
        """Retorna uma cópia imutável dos contadores de profiling de trabalho espacial."""
        return {
            "insert_calls": self._insert_calls,
            "remove_calls": self._remove_calls,
            "update_calls": self._update_calls,
            "same_cell_updates": self._same_cell_updates,
            "cell_transitions": self._cell_transitions,
            "bucket_mutations": self._bucket_mutations,
            "query_calls": self._query_calls,
            "candidate_entities_evaluated": self._candidate_entities_evaluated,
            "bulk_sync_calls": self._bulk_sync_calls,
            "bulk_entities_processed": self._bulk_entities_processed,
        }

    def reset_profiling_stats(self) -> None:
        """Zera apenas as métricas de profiling sem alterar a estrutura espacial."""
        self._insert_calls = 0
        self._remove_calls = 0
        self._update_calls = 0
        self._same_cell_updates = 0
        self._cell_transitions = 0
        self._bucket_mutations = 0
        self._query_calls = 0
        self._candidate_entities_evaluated = 0
        self._bulk_sync_calls = 0
        self._bulk_entities_processed = 0

    def get_cell_coords(self, x: float, y: float) -> CellCoord:
        """Mapeia uma coordenada do mundo (x, y) para a célula (cx, cy) usando piso estrito."""
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError(f"Coordenadas devem ser numéricas: ({x}, {y})")
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            raise ValueError(f"Coordenadas inválidas (NaN ou Inf): ({x}, {y})")
        return math.floor(x * self._inv_cell_size), math.floor(y * self._inv_cell_size)

    def insert(self, entity: Any, x: float, y: float) -> None:
        """Insere uma entidade na posição (x, y) em O(1) médio."""
        self._insert_calls += 1
        if entity in self._entity_cells:
            raise ValueError(f"Entidade já indexada no SpatialHash2D: {entity}")

        cell = self.get_cell_coords(x, y)
        if cell not in self._cells:
            self._cells[cell] = set()
            self._bucket_mutations += 1
        self._cells[cell].add(entity)
        self._bucket_mutations += 1
        self._entity_cells[entity] = cell

    def remove(self, entity: Any) -> bool:
        """Remove uma entidade do hash em O(1) médio. Retorna False se não estiver indexada."""
        self._remove_calls += 1
        cell = self._entity_cells.pop(entity, None)
        if cell is None:
            return False

        cell_set = self._cells.get(cell)
        if cell_set is not None:
            cell_set.discard(entity)
            self._bucket_mutations += 1
            if not cell_set:
                del self._cells[cell]
                self._bucket_mutations += 1
        return True

    def update(self, entity: Any, x: float, y: float) -> None:
        """Atualiza a posição da entidade em O(1) médio com fast-path otimizado para same-cell."""
        self._update_calls += 1
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            raise ValueError(f"Coordenadas devem ser numéricas: ({x}, {y})")
        if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
            raise ValueError(f"Coordenadas inválidas (NaN ou Inf): ({x}, {y})")

        old_cell = self._entity_cells.get(entity)
        if old_cell is None:
            raise KeyError(f"Entidade não está indexada para update: {entity}")

        # Inline coordinate calculation sem alocação de tupla prévia
        new_cx = math.floor(x * self._inv_cell_size)
        new_cy = math.floor(y * self._inv_cell_size)

        old_cx, old_cy = old_cell
        if old_cx == new_cx and old_cy == new_cy:
            self._same_cell_updates += 1
            return

        self._cell_transitions += 1
        new_cell: CellCoord = (new_cx, new_cy)

        # Move entre células
        old_set = self._cells.get(old_cell)
        if old_set is not None:
            old_set.discard(entity)
            self._bucket_mutations += 1
            if not old_set:
                del self._cells[old_cell]
                self._bucket_mutations += 1

        new_set = self._cells.get(new_cell)
        if new_set is None:
            new_set = set()
            self._cells[new_cell] = new_set
            self._bucket_mutations += 1

        new_set.add(entity)
        self._bucket_mutations += 1
        self._entity_cells[entity] = new_cell

    def sync_from_pool(
        self,
        pool: Any,
        indices: Optional[Union[List[int], Iterator[int]]] = None,
    ) -> None:
        """
        Sincroniza um lote de entidades diretamente dos arrays contíguos de um SimulationEntityPool.
        Executa loop interno de alta velocidade minimizando dispatch overhead.
        """
        self._bulk_sync_calls += 1

        # Local bindings para velocidade máxima no loop
        px = pool.position_x
        py = pool.position_y
        gens = pool.generation
        inv_cell = self._inv_cell_size
        cells = self._cells
        entity_cells = self._entity_cells

        target_indices = indices if indices is not None else pool.iter_alive_indices()
        from engine.simulation.entity_pool import EntityHandle

        for idx in target_indices:
            self._update_calls += 1
            self._bulk_entities_processed += 1

            x = px[idx]
            y = py[idx]

            # Validação rápida de NaN / Inf
            if math.isnan(x) or math.isnan(y) or math.isinf(x) or math.isinf(y):
                raise ValueError(f"Coordenadas inválidas no pool: ({x}, {y}) no índice {idx}")

            handle = EntityHandle(idx, gens[idx])
            old_cell = entity_cells.get(handle)

            new_cx = math.floor(x * inv_cell)
            new_cy = math.floor(y * inv_cell)

            if old_cell is not None:
                old_cx, old_cy = old_cell
                if old_cx == new_cx and old_cy == new_cy:
                    self._same_cell_updates += 1
                    continue

                # Transição entre células
                self._cell_transitions += 1
                old_set = cells.get(old_cell)
                if old_set is not None:
                    old_set.discard(handle)
                    self._bucket_mutations += 1
                    if not old_set:
                        del cells[old_cell]
                        self._bucket_mutations += 1
            else:
                # Entidade recém-inserida via bulk sync
                self._insert_calls += 1

            new_cell = (new_cx, new_cy)
            new_set = cells.get(new_cell)
            if new_set is None:
                new_set = set()
                cells[new_cell] = new_set
                self._bucket_mutations += 1

            new_set.add(handle)
            self._bucket_mutations += 1
            entity_cells[handle] = new_cell

    def clear(self) -> None:
        """Limpa todas as células e entidades indexadas."""
        self._cells.clear()
        self._entity_cells.clear()

    def query_cell(self, cx: int, cy: int) -> Tuple[Any, ...]:
        """Retorna uma tupla segura de entidades ocupando a célula (cx, cy)."""
        self._query_calls += 1
        cell_set = self._cells.get((cx, cy))
        if not cell_set:
            return ()
        cands = tuple(cell_set)
        self._candidate_entities_evaluated += len(cands)
        return cands

    def query_rect_candidates(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        _count_query: bool = True,
    ) -> List[Any]:
        """Retorna candidatos das células intersectadas pelo retângulo delimitador."""
        if _count_query:
            self._query_calls += 1
        if min_x > max_x:
            min_x, max_x = max_x, min_x
        if min_y > max_y:
            min_y, max_y = max_y, min_y

        min_cx, min_cy = self.get_cell_coords(min_x, min_y)
        max_cx, max_cy = self.get_cell_coords(max_x, max_y)

        candidates: Set[Any] = set()
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                cell_set = self._cells.get((cx, cy))
                if cell_set:
                    candidates.update(cell_set)

        cand_list = list(candidates)
        self._candidate_entities_evaluated += len(cand_list)
        return cand_list

    def query_radius_candidates(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        _count_query: bool = True,
    ) -> List[Any]:
        """Retorna candidatos das células intersectadas pelo bounding box do raio."""
        if not isinstance(radius, (int, float)):
            raise ValueError(f"Raio deve ser numérico: {radius}")
        if math.isnan(radius) or math.isinf(radius):
            raise ValueError(f"Raio inválido (NaN ou Inf): {radius}")
        if radius < 0.0:
            raise ValueError(f"Raio não pode ser negativo: {radius}")

        return self.query_rect_candidates(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            _count_query=_count_query,
        )

    def query_radius(
        self,
        center_x: float,
        center_y: float,
        radius: float,
        pool: Optional[Any] = None,
        position_provider: Optional[Callable[[Any], Tuple[float, float]]] = None,
        ordered: bool = True,
    ) -> List[Any]:
        """
        Executa consulta por raio com filtragem euclidiana exata (dx^2 + dy^2 <= r^2).
        Se 'pool' for fornecido, utiliza SimulationEntityPool para obter posições e validar is_alive.
        """
        self._query_calls += 1
        candidates = self.query_radius_candidates(center_x, center_y, radius, _count_query=False)
        if not candidates:
            return []

        r2 = radius * radius
        results: List[Any] = []

        if pool is not None:
            px = pool.position_x
            py = pool.position_y
            for handle in candidates:
                if hasattr(pool, "is_alive") and not pool.is_alive(handle):
                    continue
                idx = getattr(handle, "index", handle)
                dx = px[idx] - center_x
                dy = py[idx] - center_y
                if (dx * dx + dy * dy) <= r2:
                    results.append(handle)
        elif position_provider is not None:
            for entity in candidates:
                ex, ey = position_provider(entity)
                dx = ex - center_x
                dy = ey - center_y
                if (dx * dx + dy * dy) <= r2:
                    results.append(entity)
        else:
            # Sem position provider, retorna candidatos desduplicados
            results = candidates

        if ordered:
            # Ordenação estável determinística
            def _sort_key(item: Any) -> Tuple[int, Any]:
                idx = getattr(item, "index", None)
                if isinstance(idx, int):
                    gen = getattr(item, "generation", 0)
                    return (0, (idx, gen if isinstance(gen, int) else 0))
                return (1, str(item))

            results.sort(key=_sort_key)

        return results

    def stats(self) -> Dict[str, Any]:
        """Retorna estatísticas leves do particionamento espacial."""
        populations = [len(s) for s in self._cells.values()]
        max_pop = max(populations) if populations else 0
        avg_pop = (sum(populations) / len(populations)) if populations else 0.0
        return {
            "entity_count": self.entity_count,
            "cell_count": self.cell_count,
            "max_cell_population": max_pop,
            "avg_cell_population": avg_pop,
            "cell_size": self.cell_size,
        }
