from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry
from engine.logic.contracts import sole_flow_output

@registry.register_executor(('input_axis', 'read_key_axis'))
def execute_input_axis(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    runtime._evaluate_output(node_id, "value", game, dt, set())
    # ``input_axis`` and ``read_key_axis`` share this executor but declare
    # different flow outputs (``next`` and ``exec_done``).  Returning either
    # spelling unconditionally leaves the other node's only pin unreachable, so
    # the contract of the node actually running decides.
    return [sole_flow_output(node_type, default="next")]

@registry.register_executor('key_pressed')
def execute_key_pressed(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    pressed = bool(runtime._evaluate_output(node_id, "value", game, dt, set()))
    return ["true" if pressed else "false"]

@registry.register_executor('key_held')
def execute_key_held(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    pressed = bool(runtime._evaluate_output(node_id, "value", game, dt, set()))
    return ["true" if pressed else "false"]

@registry.register_executor('is_grounded')
def execute_is_grounded(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    grounded = bool(runtime._evaluate_output(node_id, "value", game, dt, set()))
    return ["true" if grounded else "false"]

@registry.register_executor('compare_number')
def execute_compare_number(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    condition = bool(runtime._evaluate_output(node_id, "value", game, dt, set()))
    return ["true" if condition else "false"]

@registry.register_executor('compare_text')
def execute_compare_text(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    condition = bool(runtime._evaluate_output(node_id, "value", game, dt, set()))
    return ["true" if condition else "false"]

@registry.register_evaluator(('input_axis', 'read_key_axis'))
def evaluate_input_axis(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    negative = str(properties.get("negative", "A")).lower()
    positive = str(properties.get("positive", "D")).lower()
    value = float(game.axis(negative, positive))
    runtime.values["axis"] = value
    return value

@registry.register_evaluator('key_pressed')
def evaluate_key_pressed(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = bool(game.key_pressed(str(properties.get("key", "space")).lower()))
    return value

@registry.register_evaluator('key_held')
def evaluate_key_held(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = bool(game.key(str(properties.get("key", "space")).lower()))
    return value

@registry.register_evaluator('is_grounded')
def evaluate_is_grounded(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = bool(game.grounded)
    return value

@registry.register_evaluator('compare_number')
def evaluate_compare_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    left = runtime._read_input(node_id, "value", runtime.values.get("axis", 0.0), game, dt, branch)
    value = runtime._compare(left, properties.get("operator", ">"), properties.get("value", 0.0))
    return value

@registry.register_evaluator('compare_text')
def evaluate_compare_text(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    left = runtime._read_input(node_id, "value", "", game, dt, branch)
    right = str(properties.get("value", ""))
    operator = str(properties.get("operator", "=="))
    equal = str(left).casefold() == right.casefold()
    value = not equal if operator == "!=" else equal
    return value

