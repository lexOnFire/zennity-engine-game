"""Nós de partículas para Logic Graph - Partículas 100% visual."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('create_particle_system')
def execute_create_particle_system(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Cria um sistema de partículas em uma posição."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        x = float(properties.get("x", 0.0))
        y = float(properties.get("y", 0.0))
        particle_type = str(properties.get("particle_type", "spark"))  # spark, smoke, fire, etc
        quantity = int(properties.get("quantity", 10))
        lifetime = float(properties.get("lifetime", 1.0))
        speed = float(properties.get("speed", 100.0))

        if hasattr(game, "create_particle_system"):
            system_id = game.create_particle_system(
                x, y, particle_type, quantity, lifetime, speed
            )
            runtime._store(node_id, "system_id", system_id)
            return ["exec_created"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em create_particle_system: {e}")
        return ["exec_failure"]


@registry.register_executor('emit_particles')
def execute_emit_particles(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Emite partículas de um sistema existente."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        system_id = properties.get("system_id", "")
        quantity = int(properties.get("quantity", 10))

        if system_id and hasattr(game, "emit_particles"):
            game.emit_particles(system_id, quantity)
            return ["exec_emitting"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em emit_particles: {e}")
        return ["exec_failure"]


@registry.register_executor('stop_particles')
def execute_stop_particles(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Para a emissão de partículas."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        system_id = properties.get("system_id", "")
        destroy = bool(properties.get("destroy", False))  # Destruir imediatamente?

        if system_id and hasattr(game, "stop_particles"):
            game.stop_particles(system_id, destroy)
            return ["exec_stopped"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em stop_particles: {e}")
        return ["exec_failure"]
