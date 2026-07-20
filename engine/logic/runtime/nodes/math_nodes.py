from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry

@registry.register_evaluator(('add_number', 'subtract_number', 'multiply_number', 'divide_number'))
def evaluate_add_number_or_subtract_number_or_multiply_number_or_divide_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    left = float(runtime._read_input(node_id, "a", properties.get("a", 0.0), game, dt, branch))
    right = float(runtime._read_input(node_id, "b", properties.get("b", 0.0), game, dt, branch))
    if node_type == "add_number":
        value = left + right
    elif node_type == "subtract_number":
        value = left - right
    elif node_type == "multiply_number":
        value = left * right
    else:
        if right == 0.0:
            raise RuntimeError("Divisão por zero.")
        value = left / right
    return value

@registry.register_evaluator('add_number')
def evaluate_add_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = left + right
    return value

@registry.register_evaluator('subtract_number')
def evaluate_subtract_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = left - right
    return value

@registry.register_evaluator('multiply_number')
def evaluate_multiply_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = left * right
    return value

@registry.register_evaluator('absolute_number')
def evaluate_absolute_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = abs(float(runtime._read_input(node_id, "value", properties.get("value", 0.0), game, dt, branch)))
    return value

@registry.register_evaluator('clamp_number')
def evaluate_clamp_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    raw = float(runtime._read_input(node_id, "value", properties.get("value", 0.0), game, dt, branch))
    minimum = float(runtime._read_input(node_id, "minimum", properties.get("minimum", 0.0), game, dt, branch))
    maximum = float(runtime._read_input(node_id, "maximum", properties.get("maximum", 1.0), game, dt, branch))
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    value = max(minimum, min(maximum, raw))
    return value

@registry.register_evaluator('random_number')
def evaluate_random_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    minimum = float(runtime._read_input(node_id, "minimum", properties.get("minimum", 0.0), game, dt, branch))
    maximum = float(runtime._read_input(node_id, "maximum", properties.get("maximum", 1.0), game, dt, branch))
    value = random.uniform(minimum, maximum)
    return value

