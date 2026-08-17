"""Testes unitários e de contratos de TemporalWorkDistributor (Phase 12 - Item 12.5)."""
from __future__ import annotations

import pytest
from engine.simulation.work_distribution import TemporalWorkDistributor


def test_work_distributor_config_validation():
    # Sucesso para frequências válidas
    d = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
    assert d.phase_count == 6
    assert d.current_phase == 0

    d5 = TemporalWorkDistributor(target_hz=5.0, base_hz=60.0)
    assert d5.phase_count == 12

    d1 = TemporalWorkDistributor(target_hz=1.0, base_hz=60.0)
    assert d1.phase_count == 60

    d20 = TemporalWorkDistributor(target_hz=20.0, base_hz=60.0)
    assert d20.phase_count == 3

    # Erros de validação
    with pytest.raises(ValueError):
        TemporalWorkDistributor(target_hz=0.0)

    with pytest.raises(ValueError):
        TemporalWorkDistributor(target_hz=-10.0)

    with pytest.raises(ValueError):
        TemporalWorkDistributor(target_hz=120.0, base_hz=60.0)

    with pytest.raises(ValueError):
        TemporalWorkDistributor(target_hz=float("nan"))


def test_work_distributor_selection_and_fairness():
    # 600 entidades, 10Hz em base 60Hz (6 fases)
    d = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
    entities = list(range(600))

    counts = [0] * 600

    for frame in range(60):  # 1 segundo = 60 frames = 10 ciclos completos de 6 fases
        selected = d.select(entities)
        # Cada frame deve processar exatamente 100 entidades
        assert len(selected) == 100
        for idx in selected:
            counts[idx] += 1
        d.advance()

    # Cada entidade deve ter sido selecionada exatamente 10 vezes (10Hz exato)
    for idx in range(600):
        assert counts[idx] == 10


def test_work_distributor_5hz_and_1hz_conservation():
    # 5Hz em 60 frames (12 fases) -> 5 updates por entidade
    d5 = TemporalWorkDistributor(target_hz=5.0, base_hz=60.0)
    entities = list(range(120))
    counts5 = [0] * 120

    for _ in range(60):
        selected = d5.select(entities)
        assert len(selected) == 10
        for idx in selected:
            counts5[idx] += 1
        d5.advance()

    for idx in range(120):
        assert counts5[idx] == 5

    # 1Hz em 60 frames (60 fases) -> 1 update por entidade
    d1 = TemporalWorkDistributor(target_hz=1.0, base_hz=60.0)
    counts1 = [0] * 120

    for _ in range(60):
        selected = d1.select(entities)
        assert len(selected) == 2
        for idx in selected:
            counts1[idx] += 1
        d1.advance()

    for idx in range(120):
        assert counts1[idx] == 1


def test_work_distributor_dynamic_population_and_slot_reuse():
    d = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)

    # Inicia com 10 entidades
    entities = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    # Destrói entidades 2 e 5
    entities.remove(2)
    entities.remove(5)

    # Cria nova entidade reutilizando slot 2
    entities.append(2)
    entities.append(10)

    phase_0 = d.select(entities, phase=0)  # idx % 6 == 0 -> [0, 6]
    assert set(phase_0) == {0, 6}

    phase_2 = d.select(entities, phase=2)  # idx % 6 == 2 -> [2, 8]
    assert set(phase_2) == {2, 8}


def test_work_distributor_determinism_and_reset():
    d = TemporalWorkDistributor(target_hz=10.0, base_hz=60.0)
    entities = list(range(100))

    run1 = []
    for _ in range(12):
        run1.append(d.select(entities))
        d.advance()

    d.reset()
    run2 = []
    for _ in range(12):
        run2.append(d.select(entities))
        d.advance()

    assert run1 == run2
