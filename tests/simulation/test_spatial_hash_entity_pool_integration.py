"""Testes de integração entre SpatialHash2D, SimulationEntityPool e oráculo de força bruta."""
from __future__ import annotations

import random
import time
import pytest
from engine.simulation.entity_pool import SimulationEntityPool
from engine.simulation.spatial_hash import SpatialHash2D


def test_spatial_hash_vs_brute_force_oracle():
    rng = random.Random(12345)
    pool = SimulationEntityPool(initial_capacity=1024)
    sh = SpatialHash2D(cell_size=64.0)

    # Cria 1000 entidades aleatórias em [-500, 500]
    handles = []
    for _ in range(1000):
        x = rng.uniform(-500.0, 500.0)
        y = rng.uniform(-500.0, 500.0)
        h = pool.create(position=(x, y))
        handles.append(h)
        sh.insert(h, x, y)

    # Testa 20 consultas de raio contra ground truth de força bruta
    for _ in range(20):
        qx = rng.uniform(-400.0, 400.0)
        qy = rng.uniform(-400.0, 400.0)
        r = rng.uniform(20.0, 100.0)
        r2 = r * r

        # Força bruta
        expected = []
        for h in handles:
            if pool.is_alive(h):
                idx = h.index
                dx = pool.position_x[idx] - qx
                dy = pool.position_y[idx] - qy
                if (dx * dx + dy * dy) <= r2:
                    expected.append(h)
        expected.sort(key=lambda h: (h.index, h.generation))

        # SpatialHash2D integrado com o pool
        actual = sh.query_radius(qx, qy, r, pool=pool, ordered=True)

        assert actual == expected


def test_stale_handle_safety_in_hash():
    pool = SimulationEntityPool(initial_capacity=10)
    sh = SpatialHash2D(cell_size=64.0)

    h1 = pool.create(position=(10.0, 10.0))
    sh.insert(h1, 10.0, 10.0)

    # Destrói no pool, mas deixa propositalmente no hash para simular bug de caller
    pool.destroy(h1)

    # Reutiliza o mesmo slot para h2
    h2 = pool.create(position=(10.0, 10.0))

    # Consulta por raio não deve retornar o handle morto h1 nem h2 através de h1
    results = sh.query_radius(10.0, 10.0, radius=20.0, pool=pool)
    assert h1 not in results
    assert h2 not in results  # h2 ainda não foi inserido no hash
