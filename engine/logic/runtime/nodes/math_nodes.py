from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry

@registry.register_evaluator(('add_number', 'subtract_number', 'multiply_number', 'divide_number'))
def evaluate_add_number_or_subtract_number_or_multiply_number_or_divide_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    raw_left = runtime._read_input(node_id, "a", properties.get("a", 0.0), game, dt, branch)
    raw_right = runtime._read_input(node_id, "b", properties.get("b", 0.0), game, dt, branch)
    try:
        left = float(raw_left) if raw_left is not None else 0.0
    except (TypeError, ValueError):
        left = 0.0
    try:
        right = float(raw_right) if raw_right is not None else 0.0
    except (TypeError, ValueError):
        right = 0.0
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

@registry.register_evaluator('absolute_number')
def evaluate_absolute_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    raw = runtime._read_input(node_id, "value", properties.get("value", 0.0), game, dt, branch)
    try:
        val = float(raw) if raw is not None else 0.0
    except (TypeError, ValueError):
        val = 0.0
    return abs(val)

@registry.register_evaluator('clamp_number')
def evaluate_clamp_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    raw_val = runtime._read_input(node_id, "value", properties.get("value", 0.0), game, dt, branch)
    raw_min = runtime._read_input(node_id, "minimum", properties.get("minimum", 0.0), game, dt, branch)
    raw_max = runtime._read_input(node_id, "maximum", properties.get("maximum", 1.0), game, dt, branch)
    try:
        raw = float(raw_val) if raw_val is not None else 0.0
    except (TypeError, ValueError):
        raw = 0.0
    try:
        minimum = float(raw_min) if raw_min is not None else 0.0
    except (TypeError, ValueError):
        minimum = 0.0
    try:
        maximum = float(raw_max) if raw_max is not None else 1.0
    except (TypeError, ValueError):
        maximum = 1.0
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    value = max(minimum, min(maximum, raw))
    return value

@registry.register_evaluator('random_number')
def evaluate_random_number(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    raw_min = runtime._read_input(node_id, "minimum", properties.get("minimum", 0.0), game, dt, branch)
    raw_max = runtime._read_input(node_id, "maximum", properties.get("maximum", 1.0), game, dt, branch)
    try:
        minimum = float(raw_min) if raw_min is not None else 0.0
    except (TypeError, ValueError):
        minimum = 0.0
    try:
        maximum = float(raw_max) if raw_max is not None else 1.0
    except (TypeError, ValueError):
        maximum = 1.0
    value = random.uniform(minimum, maximum)
    return value

