"""Testes unitários e de histerese do sistema de Simulation LOD (Phase 12 - Item 12.2)."""
from __future__ import annotations

import pytest
from engine.simulation.entity_pool import EntityHandle, SimulationEntityPool
from engine.simulation.lod import (
    LOD_HIGH,
    LOD_LOW,
    LOD_MEDIUM,
    LOD_SLEEP,
    SimulationFocus,
    SimulationLODConfig,
    SimulationLODManager,
)


def test_simulation_lod_config_validation():
    # Válido
    cfg = SimulationLODConfig(high_distance=100.0, medium_distance=300.0, low_distance=600.0, hysteresis_margin=20.0)
    assert cfg.high_distance == 100.0
    assert cfg.medium_distance == 300.0

    # Inválidos
    with pytest.raises(ValueError):
        SimulationLODConfig(high_distance=300.0, medium_distance=100.0, low_distance=600.0)

    with pytest.raises(ValueError):
        SimulationLODConfig(high_distance=100.0, medium_distance=300.0, low_distance=600.0, hysteresis_margin=250.0)

    with pytest.raises(ValueError):
        SimulationLODConfig(high_distance=-10.0, medium_distance=100.0, low_distance=200.0)


def test_simulation_focus_creation_and_repositioning():
    f = SimulationFocus(10.0, 20.0, enabled=True)
    assert f.x == 10.0
    assert f.y == 20.0
    assert f.enabled is True

    f.set_position(50.0, -100.0)
    assert f.x == 50.0
    assert f.y == -100.0


def test_lod_classification_and_distance_bands():
    pool = SimulationEntityPool(initial_capacity=10)
    cfg = SimulationLODConfig(high_distance=100.0, medium_distance=300.0, low_distance=600.0, hysteresis_margin=20.0)
    mgr = SimulationLODManager(config=cfg, initial_capacity=10)
    focus = SimulationFocus(0.0, 0.0, enabled=True)

    # Cria entidades em diferentes distâncias
    h_high = pool.create(position=(50.0, 0.0))       # dist = 50 -> HIGH
    h_med = pool.create(position=(200.0, 0.0))       # dist = 200 -> MEDIUM
    h_low = pool.create(position=(450.0, 0.0))       # dist = 450 -> LOW
    h_sleep = pool.create(position=(1000.0, 0.0))    # dist = 1000 -> SLEEP

    mgr.classify(pool, focus)

    assert mgr.get_tier(h_high) == LOD_HIGH
    assert mgr.get_tier(h_med) == LOD_MEDIUM
    assert mgr.get_tier(h_low) == LOD_LOW
    assert mgr.get_tier(h_sleep) == LOD_SLEEP

    stats = mgr.get_stats()
    assert stats["tier_counts"]["high"] == 1
    assert stats["tier_counts"]["medium"] == 1
    assert stats["tier_counts"]["low"] == 1
    assert stats["tier_counts"]["sleep"] == 1


def test_lod_hysteresis_and_no_thrashing():
    pool = SimulationEntityPool(initial_capacity=10)
    cfg = SimulationLODConfig(high_distance=100.0, medium_distance=300.0, low_distance=600.0, hysteresis_margin=20.0)
    mgr = SimulationLODManager(config=cfg, initial_capacity=10)
    focus = SimulationFocus(0.0, 0.0, enabled=True)

    h = pool.create(position=(90.0, 0.0))
    mgr.classify(pool, focus)
    assert mgr.get_tier(h) == LOD_HIGH

    # Move para 105 (ultrapassou 100, mas está abaixo de high_demote 100 + 20 = 120)
    pool.position_x[h.index] = 105.0
    mgr.classify(pool, focus)
    assert mgr.get_tier(h) == LOD_HIGH  # Permanece HIGH pela histerese

    # Move para 125 (ultrapassou 120 -> demote para MEDIUM)
    pool.position_x[h.index] = 125.0
    mgr.classify(pool, focus)
    assert mgr.get_tier(h) == LOD_MEDIUM

    # Move de volta para 95 (abaixo de 100, mas acima de high_promote 100 - 20 = 80)
    pool.position_x[h.index] = 95.0
    mgr.classify(pool, focus)
    assert mgr.get_tier(h) == LOD_MEDIUM  # Permanece MEDIUM pela histerese

    # Move de volta para 75 (abaixo de 80 -> promote para HIGH)
    pool.position_x[h.index] = 75.0
    mgr.classify(pool, focus)
    assert mgr.get_tier(h) == LOD_HIGH


def test_teleport_and_multiple_tier_skip():
    pool = SimulationEntityPool(initial_capacity=10)
    cfg = SimulationLODConfig(high_distance=100.0, medium_distance=300.0, low_distance=600.0, hysteresis_margin=20.0)
    mgr = SimulationLODManager(config=cfg, initial_capacity=10)
    focus = SimulationFocus(0.0, 0.0, enabled=True)

    h = pool.create(position=(50.0, 0.0))
    mgr.classify(pool, focus)
    assert mgr.get_tier(h) == LOD_HIGH

    # Teleporta diretamente para 2000 (HIGH -> SLEEP direto)
    pool.position_x[h.index] = 2000.0
    mgr.classify(pool, focus)
    assert mgr.get_tier(h) == LOD_SLEEP

    # Teleporta diretamente de volta para 10 (SLEEP -> HIGH direto)
    pool.position_x[h.index] = 10.0
    mgr.classify(pool, focus)
    assert mgr.get_tier(h) == LOD_HIGH


def test_no_focus_all_high_backward_compatibility():
    pool = SimulationEntityPool(initial_capacity=10)
    mgr = SimulationLODManager(initial_capacity=10)

    h1 = pool.create(position=(50.0, 0.0))
    h2 = pool.create(position=(5000.0, 5000.0))

    # Sem focus
    mgr.classify(pool, focus=None)
    assert mgr.get_tier(h1) == LOD_HIGH
    assert mgr.get_tier(h2) == LOD_HIGH

    # Focus desabilitado
    focus = SimulationFocus(0.0, 0.0, enabled=False)
    mgr.classify(pool, focus=focus)
    assert mgr.get_tier(h1) == LOD_HIGH
    assert mgr.get_tier(h2) == LOD_HIGH


def test_generation_safety_and_slot_reuse():
    pool = SimulationEntityPool(initial_capacity=10)
    cfg = SimulationLODConfig(high_distance=100.0, medium_distance=300.0, low_distance=600.0, hysteresis_margin=20.0)
    mgr = SimulationLODManager(config=cfg, initial_capacity=10)
    focus = SimulationFocus(0.0, 0.0, enabled=True)

    # Cria entidade distante (SLEEP)
    h_old = pool.create(position=(2000.0, 0.0))
    mgr.classify(pool, focus)
    assert mgr.get_tier(h_old) == LOD_SLEEP

    # Destrói e recria no mesmo slot uma entidade próxima (HIGH)
    slot_idx = h_old.index
    pool.destroy(h_old)
    h_new = pool.create(position=(20.0, 0.0))
    assert h_new.index == slot_idx
    assert h_new.generation > h_old.generation

    # Classificação atualiza o slot para HIGH
    mgr.classify(pool, focus)
    assert mgr.get_tier(h_new) == LOD_HIGH

    # Handle antigo stale não reflete a nova entidade viva
    assert mgr.get_tier(h_old) == LOD_HIGH  # Stale handle cai no fallback seguro
