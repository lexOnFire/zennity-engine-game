from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry

@registry.register_executor('if_else')
def execute_if_else(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    raw = runtime._read_input(node_id, "condition", properties.get("condition", False), game, dt, set())
    condition = runtime._condition(raw)
    runtime._store(node_id, "value", condition)
    return ["true" if condition else "false"]

@registry.register_executor('restart_scene')
def execute_restart_scene(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    game.restart()
    return []

@registry.register_executor('once')
def execute_once(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    state = runtime._node_state.setdefault(node_id, {"executed": False})
    if bool(state["executed"]):
        return ["blocked"]
    state["executed"] = True
    return ["next"]

@registry.register_executor('cooldown')
def execute_cooldown(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    seconds = max(0.0, float(runtime._read_input(node_id, "seconds", properties.get("seconds", 1.0), game, dt, set())))
    state = runtime._node_state.setdefault(node_id, {"remaining": 0.0})
    remaining = max(0.0, float(state.get("remaining", 0.0)) - max(0.0, float(dt)))
    if remaining > 0.0:
        state["remaining"] = remaining
        return ["blocked"]
    state["remaining"] = seconds
    return ["next"]

@registry.register_evaluator('if_else')
def evaluate_if_else(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    raw = runtime._read_input(node_id, "condition", properties.get("condition", False), game, dt, branch)
    value = runtime._condition(raw)
    return value

