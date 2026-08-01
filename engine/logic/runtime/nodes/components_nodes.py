from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry

@registry.register_executor('add_component')
def execute_add_component(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    component_properties = properties.get("properties", {})
    target.add_component(
        str(properties.get("component", "BoxCollider")),
        component_properties if isinstance(component_properties, Mapping) else {},
    )
    return ["next"]

@registry.register_executor('remove_component')
def execute_remove_component(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    target.remove_component(str(properties.get("component", "BoxCollider")))
    return ["next"]

