from __future__ import annotations
import math
import random
from typing import Any, Mapping
from engine.logic.runtime.registry import registry

@registry.register_evaluator('delta_time')
def evaluate_delta_time(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = float(dt)
    return value

@registry.register_evaluator('get_tag')
def evaluate_get_tag(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, branch)
    value = str(getattr(target, "tag", "Untagged"))
    return value

