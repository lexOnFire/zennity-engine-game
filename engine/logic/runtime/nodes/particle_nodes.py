"""Nós de partículas para Logic Graph - Partículas 100% visual."""
from __future__ import annotations

import uuid
from typing import Any, Mapping
from engine.core.game_object import GameObject
from engine.graphics.particles import ParticleSystem
from ..registry import registry


def _resolve_active_scene(game: Any) -> Any | None:
    """Obtém a cena ativa a partir do objeto game ou SceneManager."""
    if hasattr(game, "current_scene") and game.current_scene is not None:
        return game.current_scene
    if hasattr(game, "scene") and game.scene is not None:
        return game.scene
    try:
        from engine.core.scene_manager import SceneManager
        return SceneManager.get_active_scene()
    except Exception:
        return None


@registry.register_executor('create_particle_system')
def execute_create_particle_system(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Cria um sistema de partículas em uma posição e registra na cena ativa."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        if hasattr(game, "create_particle_system"):
            system_id = game.create_particle_system(
                float(properties.get("x", 0.0)),
                float(properties.get("y", 0.0)),
                str(properties.get("particle_type", "spark")),
                int(properties.get("quantity", 10)),
                float(properties.get("lifetime", 1.0)),
                float(properties.get("speed", 100.0)),
            )
            runtime._store(node_id, "system_id", system_id)
            return ["exec_created"]

        scene = _resolve_active_scene(game)
        if scene is None:
            return ["exec_failure"]

        x = float(properties.get("x", 0.0))
        y = float(properties.get("y", 0.0))
        quantity = int(properties.get("quantity", 10))
        lifetime = float(properties.get("lifetime", 1.0))
        speed = float(properties.get("speed", 100.0))

        system_id = f"particle_sys_{uuid.uuid4().hex[:8]}"
        go = GameObject(name=f"ParticleEmitter_{system_id}")
        go.transform.position = (x, y, 0.0)

        ps = ParticleSystem(
            emission_rate=0.0,
            lifetime=lifetime,
            speed=speed,
        )
        go.add_component(ps)
        scene.add_game_object(go)

        if not hasattr(runtime, "_particle_systems"):
            runtime._particle_systems = {}
        runtime._particle_systems[system_id] = (go, ps)

        runtime._store(node_id, "system_id", system_id)
        return ["exec_created"]
    except Exception as e:
        print(f"Erro em create_particle_system: {e}")
        return ["exec_failure"]


@registry.register_executor('emit_particles')
def execute_emit_particles(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Emite partículas de um sistema existente."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        system_id = str(properties.get("system_id", "") or "")
        quantity = int(properties.get("quantity", 10))

        if not system_id:
            return ["exec_failure"]

        if hasattr(game, "emit_particles"):
            game.emit_particles(system_id, quantity)
            return ["exec_emitting"]

        if hasattr(runtime, "_particle_systems") and system_id in runtime._particle_systems:
            go, ps = runtime._particle_systems[system_id]
            if go is not None and ps is not None:
                ps.emit(quantity)
                return ["exec_emitting"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em emit_particles: {e}")
        return ["exec_failure"]


@registry.register_executor('stop_particles')
def execute_stop_particles(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Para a emissão de partículas ou destrói o sistema."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        system_id = str(properties.get("system_id", "") or "")
        destroy = bool(properties.get("destroy", False))

        if not system_id:
            return ["exec_failure"]

        if hasattr(game, "stop_particles"):
            game.stop_particles(system_id, destroy)
            return ["exec_stopped"]

        if hasattr(runtime, "_particle_systems") and system_id in runtime._particle_systems:
            go, ps = runtime._particle_systems[system_id]
            if destroy:
                scene = _resolve_active_scene(game)
                if scene is not None and hasattr(scene, "remove_game_object") and go is not None:
                    try:
                        scene.remove_game_object(go)
                    except Exception:
                        pass
                del runtime._particle_systems[system_id]
            else:
                if ps is not None:
                    ps.emission_rate = 0.0
            return ["exec_stopped"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em stop_particles: {e}")
        return ["exec_failure"]
