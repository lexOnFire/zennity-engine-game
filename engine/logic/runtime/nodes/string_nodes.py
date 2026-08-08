from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry

@registry.register_evaluator('join_text')
def evaluate_join_text(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    left = runtime._read_input(node_id, "a", properties.get("a", ""), game, dt, branch)
    right = runtime._read_input(node_id, "b", properties.get("b", ""), game, dt, branch)
    value = f"{left}{right}"
    return value

@registry.register_evaluator('to_text')
def evaluate_to_text(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    val = runtime._read_input(node_id, "value", properties.get("value", "100"), game, dt, branch)
    if val is None or str(val).strip() in {"None", "none", ""}:
        val = properties.get("value", "100")
    if val is None or str(val).strip() in {"None", "none", ""}:
        val = "100"
    res = str(val)
    runtime._store(node_id, "value", res)
    return res

