"""Testes unitários para SimulationEntityPool e EntityHandle (Phase 11 - Item 11.2)."""
from __future__ import annotations

import pytest
from engine.simulation.entity_pool import EntityHandle, SimulationEntityPool


def test_entity_handle_immutability_and_hashing():
    h1 = EntityHandle(10, 1)
    h2 = EntityHandle(10, 1)
    h3 = EntityHandle(10, 2)

    assert h1 == h2
    assert h1 != h3
    assert hash(h1) == hash(h2)

    # Imutabilidade de NamedTuple
    with pytest.raises(AttributeError):
        h1.index = 20  # type: ignore

    # Uso em set e dict
    handle_set = {h1, h3}
    assert len(handle_set) == 2
    assert h2 in handle_set


def test_create_destroy_is_alive_and_slot_reuse():
    pool = SimulationEntityPool(initial_capacity=4)

    h1 = pool.create(position=(10.0, 20.0), velocity=(1.0, 2.0), state=1, flags=4)
    assert pool.is_alive(h1)
    assert pool.alive_count == 1

    # Destruição
    assert pool.destroy(h1) is True
    assert pool.is_alive(h1) is False
    assert pool.alive_count == 0

    # Double destroy retorna False e não corrompe free-list
    assert pool.destroy(h1) is False
    assert pool.alive_count == 0

    # Reuso do slot com geração incrementada
    h2 = pool.create(position=(0.0, 0.0))
    assert h2.index == h1.index
    assert h2.generation == h1.generation + 1
    assert pool.is_alive(h2) is True
    assert pool.is_alive(h1) is False  # Stale handle antigo é inválido!

    # Reseta valores para defaults ao reusar slot
    assert pool.position_x[h2.index] == 0.0
    assert pool.velocity_x[h2.index] == 0.0
    assert pool.state[h2.index] == 0
    assert pool.flags[h2.index] == 0


def test_capacity_growth():
    pool = SimulationEntityPool(initial_capacity=2)
    assert pool.capacity == 2

    h1 = pool.create()
    h2 = pool.create()
    assert pool.capacity == 2
    assert pool.alive_count == 2

    # Força crescimento
    h3 = pool.create()
    assert pool.capacity == 4
    assert pool.alive_count == 3
    assert pool.is_alive(h1)
    assert pool.is_alive(h2)
    assert pool.is_alive(h3)


def test_swap_remove_active_iteration():
    pool = SimulationEntityPool(initial_capacity=10)
    h1 = pool.create(position=(1.0, 0.0))
    h2 = pool.create(position=(2.0, 0.0))
    h3 = pool.create(position=(3.0, 0.0))

    assert set(pool.iter_alive_indices()) == {h1.index, h2.index, h3.index}

    # Destrói o do meio (h2) -> swap-remove deve mover o último para a posição de h2
    pool.destroy(h2)
    assert pool.alive_count == 2
    assert set(pool.iter_alive_indices()) == {h1.index, h3.index}
    assert pool.is_alive(h2) is False


def test_clear_invalidation():
    pool = SimulationEntityPool(initial_capacity=10)
    handles = [pool.create() for _ in range(5)]
    assert pool.alive_count == 5

    pool.clear()
    assert pool.alive_count == 0
    assert len(pool.iter_alive_indices()) == 0

    # Todos os handles antigos são inválidos
    for h in handles:
        assert pool.is_alive(h) is False


def test_scale_5000_entities_creation_and_movement():
    pool = SimulationEntityPool(initial_capacity=1024)
    handles = []
    for i in range(5000):
        h = pool.create(position=(float(i), float(i)), velocity=(1.0, 1.0))
        handles.append(h)

    assert pool.alive_count == 5000
    assert pool.capacity >= 5000

    # Simula movimento denso em lote usando índices ativos
    dt = 0.016
    px = pool.position_x
    py = pool.position_y
    vx = pool.velocity_x
    vy = pool.velocity_y

    for idx in pool.iter_alive_indices():
        px[idx] += vx[idx] * dt
        py[idx] += vy[idx] * dt

    assert px[handles[0].index] == 0.0 + 1.0 * dt
    assert px[handles[100].index] == 100.0 + 1.0 * dt
