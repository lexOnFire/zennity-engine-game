"""Nós de física para Logic Graph - Modify Rigidbody/Collider 100% visual."""
from __future__ import annotations

import numpy as np
from typing import Any, Mapping
from ..registry import registry

# Phase 5B.1: Property schema for type-safe modifications
RIGIDBODY_PROPERTIES = {
    "mass": float,
    "gravity_scale": float,
    "drag": float,
    "use_gravity": bool,
    "is_kinematic": bool,
    "velocity_x": float,
    "velocity_y": float,
}


def _resolve_rigidbody(target: Any, game: Any) -> tuple[Any, str | None]:
    """Resolve a RigidBody component from a target name.

    Returns:
        (rigidbody, error_message) where error_message is None on success
    """
    if not target:
        return None, "Target name is empty"

    if not hasattr(game, "find_object"):
        return None, "Game object doesn't support find_object"

    game_obj = game.find_object(str(target))
    if not game_obj:
        return None, f"GameObject '{target}' not found"

    if not hasattr(game_obj, "get_component"):
        return None, f"GameObject '{target}' doesn't support get_component"

    from engine.physics.rigidbody import RigidBody
    rigidbody = game_obj.get_component(RigidBody)

    if not rigidbody:
        return None, f"GameObject '{target}' has no RigidBody component"

    return rigidbody, None


@registry.register_executor('modify_rigidbody')
def execute_modify_rigidbody(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Phase 5B.1: Modify RigidBody properties with type safety and validation."""
    node_id = str(node['id'])
    node_properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    target_name = str(node_properties.get("target", "")).strip()
    property_name = str(node_properties.get("property", "")).strip().lower()
    value = node_properties.get("value", 0.0)

    # Validate property is in schema
    if property_name not in RIGIDBODY_PROPERTIES:
        return ["failure"]

    # Resolve target
    rigidbody, error = _resolve_rigidbody(target_name, game)
    if error or not rigidbody:
        return ["failure"]

    try:
        expected_type = RIGIDBODY_PROPERTIES[property_name]

        if property_name == "mass":
            rigidbody.mass = float(value)
        elif property_name == "gravity_scale":
            rigidbody.gravity_scale = float(value)
        elif property_name == "drag":
            rigidbody.drag = float(value)
        elif property_name == "use_gravity":
            rigidbody.use_gravity = bool(value)
        elif property_name == "is_kinematic":
            rigidbody.is_kinematic = bool(value)
        elif property_name == "velocity_x":
            # Phase 5B.1: Type safety - velocity is numpy array, not tuple
            rigidbody.velocity[0] = float(value)
        elif property_name == "velocity_y":
            rigidbody.velocity[1] = float(value)

        # Verify velocity is still numpy array after modification
        if property_name.startswith("velocity"):
            assert isinstance(rigidbody.velocity, np.ndarray), \
                f"velocity corrupted: expected np.ndarray, got {type(rigidbody.velocity)}"

        runtime._store(node_id, property_name, value)
        return ["success"]

    except (ValueError, TypeError, AssertionError):
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
    """Phase 5B.1: Apply force/impulse to RigidBody with mode validation."""
    node_id = str(node['id'])
    node_properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    target_name = str(node_properties.get("target", "")).strip()
    force_x = float(node_properties.get("force_x", 0.0))
    force_y = float(node_properties.get("force_y", 0.0))
    force_mode = str(node_properties.get("force_mode", "impulse")).strip().lower()

    # Validate force mode
    if force_mode not in ("force", "impulse"):
        return ["failure"]

    # Resolve target
    rigidbody, error = _resolve_rigidbody(target_name, game)
    if error or not rigidbody:
        return ["failure"]

    try:
        if force_mode == "force":
            rigidbody.add_force(force_x, force_y)
        elif force_mode == "impulse":
            rigidbody.add_impulse(force_x, force_y)

        runtime._store(node_id, "force_applied", True)
        return ["success"]

    except (ValueError, TypeError, AttributeError):
        return ["failure"]


# Phase 5B.1: Getter evaluators (pure data nodes)
@registry.register_evaluator('get_rigidbody_velocity_x')
def evaluate_get_rigidbody_velocity_x(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Evaluate RigidBody velocity X component."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    rigidbody, error = _resolve_rigidbody(target_name, game)
    if error or not rigidbody:
        return 0.0

    try:
        return float(rigidbody.velocity[0])
    except (IndexError, TypeError):
        return 0.0


@registry.register_evaluator('get_rigidbody_velocity_y')
def evaluate_get_rigidbody_velocity_y(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Evaluate RigidBody velocity Y component."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    rigidbody, error = _resolve_rigidbody(target_name, game)
    if error or not rigidbody:
        return 0.0

    try:
        return float(rigidbody.velocity[1])
    except (IndexError, TypeError):
        return 0.0


@registry.register_evaluator('get_rigidbody_mass')
def evaluate_get_rigidbody_mass(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Evaluate RigidBody mass."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    rigidbody, error = _resolve_rigidbody(target_name, game)
    if error or not rigidbody:
        return 1.0

    return float(rigidbody.mass)


@registry.register_evaluator('get_rigidbody_gravity_scale')
def evaluate_get_rigidbody_gravity_scale(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Evaluate RigidBody gravity scale."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    rigidbody, error = _resolve_rigidbody(target_name, game)
    if error or not rigidbody:
        return 1.0

    return float(rigidbody.gravity_scale)


@registry.register_evaluator('get_rigidbody_use_gravity')
def evaluate_get_rigidbody_use_gravity(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Evaluate RigidBody use gravity flag."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    rigidbody, error = _resolve_rigidbody(target_name, game)
    if error or not rigidbody:
        return True

    return bool(rigidbody.use_gravity)


@registry.register_evaluator('get_rigidbody_is_kinematic')
def evaluate_get_rigidbody_is_kinematic(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Evaluate RigidBody kinematic flag."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target_name = str(properties.get("target", "")).strip()

    rigidbody, error = _resolve_rigidbody(target_name, game)
    if error or not rigidbody:
        return False

    return bool(rigidbody.is_kinematic)


# Phase 5B.2: Collision/Trigger Event Data Pins
@registry.register_evaluator(('on_collision_enter', 'on_collision_exit', 'on_trigger_enter', 'on_trigger_exit'))
def evaluate_physics_event_nodes(runtime, node_id: str, port_id: str, node: Mapping[str, Any], game: Any, dt: float, visited: set) -> Any:
    """Evaluate data outputs from physics event nodes."""
    port_id = str(port_id)

    if port_id == "self_object":
        return runtime.values.get((node_id, "self_object"))
    elif port_id == "other_object":
        return runtime.values.get((node_id, "other_object"))
    elif port_id == "self_collider":
        return runtime.values.get((node_id, "self_collider"))
    elif port_id == "other_collider":
        return runtime.values.get((node_id, "other_collider"))
    elif port_id == "is_trigger":
        return runtime.values.get((node_id, "is_trigger"), False)
    else:
        # Fallback for "other" (backward compatibility)
        return runtime.values.get((node_id, "other"))
