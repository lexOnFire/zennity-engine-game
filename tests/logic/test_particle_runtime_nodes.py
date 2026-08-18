"""Testes dos nós de runtime de partículas (Pre-Phase 13 Sprint R2)."""
from __future__ import annotations

from types import SimpleNamespace
import pytest

from engine.core.scene import Scene
from engine.logic.runtime.nodes.particle_nodes import (
    execute_create_particle_system,
    execute_emit_particles,
    execute_stop_particles,
)


def test_particle_nodes_lifecycle():
    """Valida create, emit e stop de partículas integradas à cena ativa."""
    scene = Scene("ParticleScene")
    game = SimpleNamespace(current_scene=scene)
    runtime = SimpleNamespace(
        _stored={},
        _store=lambda nid, k, v: runtime._stored.setdefault(nid, {}) .__setitem__(k, v),
    )

    # 1. Criação com sucesso na cena ativa
    create_node = {
        "id": "node_create",
        "properties": {
            "x": 100.0,
            "y": 200.0,
            "quantity": 20,
            "lifetime": 2.0,
            "speed": 150.0,
        },
    }
    ports = execute_create_particle_system(runtime, create_node, game, 0.016)
    assert ports == ["exec_created"]
    system_id = runtime._stored["node_create"]["system_id"]
    assert system_id.startswith("particle_sys_")
    assert len(scene.game_objects) == 1

    # 2. Emissão de partículas
    emit_node = {
        "id": "node_emit",
        "properties": {
            "system_id": system_id,
            "quantity": 10,
        },
    }
    emit_ports = execute_emit_particles(runtime, emit_node, game, 0.016)
    assert emit_ports == ["exec_emitting"]

    # 3. Emissão com ID inválido retorna exec_failure
    bad_emit = {
        "id": "node_bad_emit",
        "properties": {
            "system_id": "invalid_id_xyz",
            "quantity": 5,
        },
    }
    assert execute_emit_particles(runtime, bad_emit, game, 0.016) == ["exec_failure"]

    # 4. Stop emission (destroy=False)
    stop_node = {
        "id": "node_stop",
        "properties": {
            "system_id": system_id,
            "destroy": False,
        },
    }
    assert execute_stop_particles(runtime, stop_node, game, 0.016) == ["exec_stopped"]

    # 5. Stop and Destroy (destroy=True) remove o GameObject da cena
    destroy_node = {
        "id": "node_destroy",
        "properties": {
            "system_id": system_id,
            "destroy": True,
        },
    }
    assert execute_stop_particles(runtime, destroy_node, game, 0.016) == ["exec_stopped"]
    assert len(scene.game_objects) == 0


def test_particle_create_without_scene_fails():
    """Valida que create_particle_system falha explicitamente sem cena ativa."""
    game = SimpleNamespace(current_scene=None, scene=None)
    runtime = SimpleNamespace(_stored={}, _store=lambda n, k, v: None)

    node = {"id": "n1", "properties": {}}
    assert execute_create_particle_system(runtime, node, game, 0.016) == ["exec_failure"]
