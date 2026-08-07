"""Nós de física para Logic Graph - Modify Rigidbody/Collider 100% visual."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('modify_rigidbody')
def execute_modify_rigidbody(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Modifica propriedades de um Rigidbody dinamicamente."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        target_name = str(properties.get("target", ""))
        property_name = str(properties.get("property", "velocity_x")).lower()
        value = properties.get("value", 0.0)

        if target_name and hasattr(game, "find_object"):
            target = game.find_object(target_name)
            if target and hasattr(target, "get_component"):
                from engine.physics.rigidbody import RigidBody

                rigidbody = target.get_component(RigidBody)
                if rigidbody:
                    if property_name == "velocity_x":
                        rigidbody.velocity = (float(value), rigidbody.velocity[1])
                    elif property_name == "velocity_y":
                        rigidbody.velocity = (rigidbody.velocity[0], float(value))
                    elif property_name == "velocity":
                        vel_parts = str(value).split(",")
                        if len(vel_parts) == 2:
                            rigidbody.velocity = (float(vel_parts[0]), float(vel_parts[1]))
                    elif property_name == "gravity_scale":
                        rigidbody.gravity_scale = float(value)
                    elif property_name == "mass":
                        rigidbody.mass = float(value)
                    elif property_name == "use_gravity":
                        rigidbody.use_gravity = bool(value)
                    elif property_name == "is_kinematic":
                        rigidbody.is_kinematic = bool(value)
                    elif property_name == "drag":
                        rigidbody.drag = float(value)
                    elif property_name == "angular_drag":
                        rigidbody.angular_drag = float(value)
                    elif property_name == "constraints":
                        rigidbody.constraints = str(value)

                    runtime._store(node_id, property_name, value)
                    return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro em modify_rigidbody: {e}")
        return ["failure"]


@registry.register_executor('modify_collider')
def execute_modify_collider(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Modifica propriedades de um Collider dinamicamente."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        target_name = str(properties.get("target", ""))
        property_name = str(properties.get("property", "enabled")).lower()
        value = properties.get("value", True)

        if target_name and hasattr(game, "find_object"):
            target = game.find_object(target_name)
            if target and hasattr(target, "get_component"):
                from engine.physics.collider import BoxCollider, CircleCollider

                # Tentar encontrar qualquer collider
                collider = target.get_component(BoxCollider)
                if not collider:
                    collider = target.get_component(CircleCollider)

                if collider:
                    if property_name == "enabled":
                        collider.enabled = bool(value)
                    elif property_name == "is_trigger":
                        collider.is_trigger = bool(value)
                    elif property_name == "width" and hasattr(collider, "width"):
                        collider.width = float(value)
                    elif property_name == "height" and hasattr(collider, "height"):
                        collider.height = float(value)
                    elif property_name == "radius" and hasattr(collider, "radius"):
                        collider.radius = float(value)
                    elif property_name == "offset_x":
                        collider.offset_x = float(value)
                    elif property_name == "offset_y":
                        collider.offset_y = float(value)

                    runtime._store(node_id, property_name, value)
                    return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro em modify_collider: {e}")
        return ["failure"]


@registry.register_executor('apply_force')
def execute_apply_force(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Aplica força a um Rigidbody."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        target_name = str(properties.get("target", ""))
        force_x = float(properties.get("force_x", 0.0))
        force_y = float(properties.get("force_y", 0.0))
        force_mode = str(properties.get("force_mode", "impulse")).lower()

        if target_name and hasattr(game, "find_object"):
            target = game.find_object(target_name)
            if target and hasattr(target, "get_component"):
                from engine.physics.rigidbody import RigidBody

                rigidbody = target.get_component(RigidBody)
                if rigidbody and hasattr(rigidbody, "apply_force"):
                    rigidbody.apply_force((force_x, force_y), force_mode)
                    runtime._store(node_id, "force_applied", True)
                    return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro em apply_force: {e}")
        return ["failure"]
