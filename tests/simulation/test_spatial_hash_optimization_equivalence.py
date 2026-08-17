"""Testes de equivalência, limites e otimização do SpatialHash2D (Phase 12 - Item 12.3)."""
from __future__ import annotations

import math
import pytest
from engine.simulation.entity_pool import EntityHandle, SimulationEntityPool
from engine.simulation.spatial_hash import SpatialHash2D


def test_same_cell_fast_path_equivalence():
    sh = SpatialHash2D(cell_size=64.0)
    pool = SimulationEntityPool(initial_capacity=10)

    h1 = pool.create(position=(10.0, 10.0))
    sh.insert(h1, 10.0, 10.0)

    # 1. Update para mesma célula (15, 15) -> célula (0, 0)
    sh.update(h1, 15.0, 15.0)

    stats = sh.get_profiling_stats()
    assert stats["update_calls"] == 1
    assert stats["same_cell_updates"] == 1
    assert stats["cell_transitions"] == 0
    assert stats["bucket_mutations"] == 2  # Apenas as 2 mutações do insert inicial

    # Entidade continua na célula correta
    assert sh.query_cell(0, 0) == (h1,)


def test_cell_transition_and_empty_cell_cleanup():
    sh = SpatialHash2D(cell_size=64.0)
    pool = SimulationEntityPool(initial_capacity=10)

    h1 = pool.create(position=(10.0, 10.0))
    sh.insert(h1, 10.0, 10.0)
    assert sh.cell_count == 1

    # Transição para célula (1, 1) -> (80.0, 80.0)
    sh.update(h1, 80.0, 80.0)

    stats = sh.get_profiling_stats()
    assert stats["update_calls"] == 1
    assert stats["cell_transitions"] == 1
    assert stats["bucket_mutations"] > 2

    # Célula (0, 0) deve ser deletada por estar vazia
    assert sh.query_cell(0, 0) == ()
    assert sh.cell_count == 1
    assert sh.query_cell(1, 1) == (h1,)


def test_positive_and_negative_cell_boundaries():
    sh = SpatialHash2D(cell_size=64.0)
    pool = SimulationEntityPool(initial_capacity=10)

    # Limites positivos
    assert sh.get_cell_coords(63.999, 63.999) == (0, 0)
    assert sh.get_cell_coords(64.0, 64.0) == (1, 1)
    assert sh.get_cell_coords(64.001, 64.001) == (1, 1)

    # Limites negativos
    assert sh.get_cell_coords(-0.001, -0.001) == (-1, -1)
    assert sh.get_cell_coords(-64.0, -64.0) == (-1, -1)
    assert sh.get_cell_coords(-64.001, -64.001) == (-2, -2)

    # Teste de update atravessando limite negativo
    h = pool.create(position=(-0.001, -0.001))
    sh.insert(h, -0.001, -0.001)
    assert sh.query_cell(-1, -1) == (h,)

    sh.update(h, -65.0, -65.0)
    assert sh.query_cell(-1, -1) == ()
    assert sh.query_cell(-2, -2) == (h,)


def test_nan_inf_validation_preserved():
    sh = SpatialHash2D(cell_size=64.0)
    pool = SimulationEntityPool(initial_capacity=10)
    h = pool.create(position=(10.0, 10.0))
    sh.insert(h, 10.0, 10.0)

    with pytest.raises(ValueError):
        sh.update(h, float("nan"), 10.0)

    with pytest.raises(ValueError):
        sh.update(h, 10.0, float("inf"))

    with pytest.raises(ValueError):
        sh.update(h, "invalid", 10.0)  # type: ignore


def test_bulk_sync_from_pool_equivalence_with_individual_updates():
    count = 200
    pool = SimulationEntityPool(initial_capacity=count)
    sh_indiv = SpatialHash2D(cell_size=64.0)
    sh_bulk = SpatialHash2D(cell_size=64.0)

    handles = []
    for i in range(count):
        x = float(i * 15 - 500)
        y = float(i * 12 - 400)
        h = pool.create(position=(x, y))
        handles.append(h)
        sh_indiv.insert(h, x, y)
        sh_bulk.insert(h, x, y)

    # Move entidades no pool
    for i, h in enumerate(handles):
        # Algumas movem dentro da célula, outras cruzam
        dx = 5.0 if i % 2 == 0 else 80.0
        dy = 4.0 if i % 2 == 0 else 90.0
        pool.position_x[h.index] += dx
        pool.position_y[h.index] += dy

    # Atualiza sh_indiv via loop individual
    for h in handles:
        sh_indiv.update(h, pool.position_x[h.index], pool.position_y[h.index])

    # Atualiza sh_bulk via sync_from_pool
    sh_bulk.sync_from_pool(pool)

    # Valida equivalência exata de células e entidades
    assert sh_indiv.cell_count == sh_bulk.cell_count
    assert sh_indiv.entity_count == sh_bulk.entity_count

    # Valida queries idênticas
    res_indiv = sh_indiv.query_radius(0.0, 0.0, radius=300.0, pool=pool, ordered=True)
    res_bulk = sh_bulk.query_radius(0.0, 0.0, radius=300.0, pool=pool, ordered=True)
    assert res_indiv == res_bulk

    # Oráculo de força bruta
    bf_res = []
    r2 = 300.0 * 300.0
    for h in handles:
        idx = h.index
        x = pool.position_x[idx]
        y = pool.position_y[idx]
        if (x * x + y * y) <= r2:
            bf_res.append(h)
    bf_res.sort(key=lambda item: item.index)

    assert res_bulk == bf_res
