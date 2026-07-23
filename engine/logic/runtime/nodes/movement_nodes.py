from __future__ import annotations
import math
from typing import Any, Mapping
from ..registry import registry

@registry.register_executor('move')
def execute_move(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    fallback = runtime.values.get("axis", 0.0)
    amount = float(runtime._read_input(node_id, "value", fallback, game, dt, set()))
    game.move(amount * float(properties.get("speed", 200.0)) * dt)
    return ["next"]

@registry.register_executor('move_by')
def execute_move_by(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    velocity_x = float(runtime._read_input(node_id, "x", properties.get("x", 100.0), game, dt, set()))
    velocity_y = float(runtime._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
    delta_x, delta_y = velocity_x * dt, velocity_y * dt
    if callable(getattr(target, "move", None)):
        target.move(delta_x, delta_y)
    else:
        target.x = float(target.x) + delta_x
        target.y = float(target.y) + delta_y
    return ["next"]

@registry.register_executor('start_continuous_motion')
def execute_start_continuous_motion(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    velocity_x = float(runtime._read_input(node_id, "x", properties.get("x", 100.0), game, dt, set()))
    velocity_y = float(runtime._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
    motion_name = str(properties.get("movement", "Movement")).strip() or "Movement"
    motion_key = f"{runtime.object_key}:{node_id}:{runtime._target_identity(target)}:{motion_name}"
    was_active = motion_key in runtime._persistent_motion
    previous = runtime._persistent_motion.get(motion_key, {})
    acceleration = max(0.0, float(properties.get("acceleration", 0.0)))
    state = {
        "target": target,
        "name": motion_name,
        "desired_x": velocity_x,
        "desired_y": velocity_y,
        "current_x": float(previous.get("current_x", 0.0 if acceleration else velocity_x)),
        "current_y": float(previous.get("current_y", 0.0 if acceleration else velocity_y)),
        "space": "local" if str(properties.get("space", "global")).lower() == "local" else "global",
        "acceleration": acceleration,
        "deceleration": max(0.0, float(properties.get("deceleration", 0.0))),
        "paused": False,
        "stopping": False,
        "graph": str(runtime.graph.get("name", "Logic Graph")),
    }
    runtime._persistent_motion[motion_key] = state
    runtime._store(node_id, "movement", motion_key)
    runtime._sync_motion_debug(motion_key, state)
    if not was_active:
        initial_x, initial_y = float(state["current_x"]), float(state["current_y"])
        if state["space"] == "local":
            radians = math.radians(float(getattr(target, "rotation", 0.0)))
            initial_x, initial_y = (
                initial_x * math.cos(radians) - initial_y * math.sin(radians),
                initial_x * math.sin(radians) + initial_y * math.cos(radians),
            )
        if initial_x or initial_y:
            runtime._move_target(target, initial_x, initial_y, dt)
    return ["next"]

@registry.register_executor('update_continuous_motion')
def execute_update_continuous_motion(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    movement = runtime._read_input(node_id, "movement", properties.get("movement", "Movement"), game, dt, set())
    velocity_x = float(runtime._read_input(node_id, "x", properties.get("x", 100.0), game, dt, set()))
    velocity_y = float(runtime._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
    for handle, state in runtime._motions_for(target, movement):
        state["desired_x"], state["desired_y"] = velocity_x, velocity_y
        state["acceleration"] = max(0.0, float(properties.get("acceleration", state.get("acceleration", 0.0))))
        state["stopping"] = False
        runtime._sync_motion_debug(handle, state)
    return ["next"]

@registry.register_executor(('pause_continuous_motion', 'resume_continuous_motion'))
def execute_pause_continuous_motion_or_resume_continuous_motion(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    movement = runtime._read_input(node_id, "movement", properties.get("movement", "Movement"), game, dt, set())
    paused = node_type == "pause_continuous_motion"
    for handle, state in runtime._motions_for(target, movement):
        state["paused"] = paused
        state["stopping"] = False
        runtime._sync_motion_debug(handle, state)
    return ["next"]

@registry.register_executor('stop_continuous_motion')
def execute_stop_continuous_motion(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    movement = runtime._read_input(node_id, "movement", properties.get("movement", ""), game, dt, set())
    matches = runtime._motions_for(target, movement)
    if bool(properties.get("smooth", False)):
        for handle, state in matches:
            state["paused"] = False
            state["stopping"] = True
            runtime._sync_motion_debug(handle, state)
    else:
        for handle, state in matches:
            runtime._persistent_motion.pop(handle, None)
            runtime._remove_motion_debug(state.get("target"), handle)
    return ["next"]

@registry.register_executor('get_continuous_motion')
def execute_get_continuous_motion(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    movement = runtime._read_input(node_id, "movement", properties.get("movement", "Movement"), game, dt, set())
    matches = runtime._motions_for(target, movement)
    state = matches[0][1] if matches else {}
    current_x = float(state.get("current_x", 0.0))
    current_y = float(state.get("current_y", 0.0))
    runtime._store(node_id, "x", current_x)
    runtime._store(node_id, "y", current_y)
    runtime._store(node_id, "speed", math.hypot(current_x, current_y))
    runtime._store(node_id, "paused", bool(state.get("paused", False)))
    runtime._store(node_id, "active", bool(matches))
    return ["next"]

@registry.register_executor('patrol_axis')
def execute_patrol_axis(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    axis = str(properties.get("axis", "Y")).strip().lower()
    axis = "x" if axis == "x" else "y"
    minimum = float(runtime._read_input(node_id, "minimum", properties.get("minimum", -100.0), game, dt, set()))
    maximum = float(runtime._read_input(node_id, "maximum", properties.get("maximum", 100.0), game, dt, set()))
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    speed = abs(float(runtime._read_input(node_id, "speed", properties.get("speed", 100.0), game, dt, set())))
    current = float(getattr(target, axis))
    state = runtime._node_state.setdefault(node_id, {"direction": 1.0})
    direction = float(state.get("direction", 1.0))
    if current >= maximum:
        direction = -1.0
    elif current <= minimum:
        direction = 1.0
    next_position = max(minimum, min(maximum, current + direction * speed * dt))
    delta = next_position - current
    if callable(getattr(target, "move", None)):
        target.move(delta if axis == "x" else 0.0, delta if axis == "y" else 0.0)
    else:
        setattr(target, axis, next_position)
    override_physics = getattr(target, "override_physics_axis", None)
    if callable(override_physics):
        override_physics(axis)
    state["direction"] = direction
    runtime._store(node_id, "direction", direction)
    runtime._store(node_id, "position", next_position)
    return ["next"]

@registry.register_executor('jump')
def execute_jump(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    force = float(runtime._read_input(node_id, "force", properties.get("force", 420.0), game, dt, set()))
    game.jump(force)
    return ["next"]

@registry.register_evaluator('get_position')
def evaluate_get_position(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, branch)
    value = float(target.x if port == "x" else target.y)
    return value

