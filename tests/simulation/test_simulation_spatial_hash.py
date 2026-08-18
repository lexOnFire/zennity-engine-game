"""Testes unitários para SpatialHash2D (Phase 11 - Item 11.3)."""
from __future__ import annotations

import math
import pytest
from engine.simulation.spatial_hash import SpatialHash2D


def test_spatial_hash_cell_size_validation():
    # Valid
    sh = SpatialHash2D(cell_size=64.0)
    assert sh.cell_size == 64.0
    assert sh.entity_count == 0
    assert sh.cell_count == 0

    # Invalid
    with pytest.raises(ValueError):
        SpatialHash2D(0)
    with pytest.raises(ValueError):
        SpatialHash2D(-10.0)
    with pytest.raises(ValueError):
        SpatialHash2D(float("nan"))
    with pytest.raises(ValueError):
        SpatialHash2D(float("inf"))
    with pytest.raises(ValueError):
        SpatialHash2D("invalid")  # type: ignore


def test_spatial_hash_floor_mapping_and_negative_coords():
    sh = SpatialHash2D(cell_size=64.0)

    # Positivos e bordas
    assert sh.get_cell_coords(0.0, 0.0) == (0, 0)
    assert sh.get_cell_coords(63.999, 10.0) == (0, 0)
    assert sh.get_cell_coords(64.0, 10.0) == (1, 0)

    # Negativos usando math.floor
    assert sh.get_cell_coords(-0.001, -0.001) == (-1, -1)
    assert sh.get_cell_coords(-64.0, -10.0) == (-1, -1)
    assert sh.get_cell_coords(-64.001, -10.0) == (-2, -1)


def test_insert_update_same_cell_and_cross_cell():
    sh = SpatialHash2D(cell_size=64.0)

    sh.insert("E1", 10.0, 10.0)
    assert sh.entity_count == 1
    assert sh.cell_count == 1
    assert sh.query_cell(0, 0) == ("E1",)

    # Duplicação rejeitada
    with pytest.raises(ValueError, match="já indexada"):
        sh.insert("E1", 20.0, 20.0)

    # Update na mesma célula (0, 0)
    sh.update("E1", 20.0, 20.0)
    assert sh.cell_count == 1
    assert sh.query_cell(0, 0) == ("E1",)

    # Update cruzando para outra célula (1, 1)
    sh.update("E1", 70.0, 70.0)
    assert sh.cell_count == 1  # Célula antiga (0, 0) foi limpa!
    assert sh.query_cell(0, 0) == ()
    assert sh.query_cell(1, 1) == ("E1",)


def test_remove_and_empty_cell_cleanup():
    sh = SpatialHash2D(cell_size=64.0)
    sh.insert("E1", 10.0, 10.0)
    sh.insert("E2", 15.0, 15.0)
    assert sh.entity_count == 2
    assert sh.cell_count == 1

    # Remove E1
    assert sh.remove("E1") is True
    assert sh.entity_count == 1
    assert sh.cell_count == 1

    # Remove E2 (esvazia célula)
    assert sh.remove("E2") is True
    assert sh.entity_count == 0
    assert sh.cell_count == 0  # Célula limpa!

    # Remove inexistente
    assert sh.remove("E_NOT_FOUND") is False


def test_query_radius_and_rect_candidate_filtering():
    sh = SpatialHash2D(cell_size=50.0)
    # Insere 4 entidades
    sh.insert("Center", 0.0, 0.0)
    sh.insert("Near", 5.0, 0.0)
    sh.insert("Far_In_Same_Cell", 40.0, 40.0)  # dist ~ 56.5
    sh.insert("Far_Other_Cell", 100.0, 100.0)

    # Posições para position_provider
    positions = {
        "Center": (0.0, 0.0),
        "Near": (5.0, 0.0),
        "Far_In_Same_Cell": (40.0, 40.0),
        "Far_Other_Cell": (100.0, 100.0),
    }

    # Consulta por raio de 10.0 em (0, 0)
    results = sh.query_radius(0.0, 0.0, radius=10.0, position_provider=lambda e: positions[e])
    assert set(results) == {"Center", "Near"}
    assert "Far_In_Same_Cell" not in results  # Filtrada geometricamente!
    assert "Far_Other_Cell" not in results


def test_clear_and_stats():
    sh = SpatialHash2D(cell_size=64.0)
    sh.insert("E1", 0.0, 0.0)
    sh.insert("E2", 10.0, 0.0)
    sh.insert("E3", 100.0, 100.0)

    st = sh.stats()
    assert st["entity_count"] == 3
    assert st["cell_count"] == 2
    assert st["max_cell_population"] == 2

    sh.clear()
    assert sh.entity_count == 0
    assert sh.cell_count == 0
