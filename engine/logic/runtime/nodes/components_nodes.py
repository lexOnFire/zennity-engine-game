from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry

COMPONENT_NODE_TYPES = {
    "add_sprite_renderer": "SpriteRenderer",
    "add_animator": "Animator2D",
    "add_rigidbody": "RigidBody2D",
    "add_box_collider": "BoxCollider",
    "add_circle_collider": "CircleCollider",
    "add_camera": "Camera2D",
    "add_audio_source": "AudioSource",
    "add_ui_canvas": "Canvas",
    "add_ui_text": "UIText",
    "add_ui_image": "UIImage",
    "add_ui_button": "UIButton",
}


@registry.register_executor(("add_component", *COMPONENT_NODE_TYPES))
def execute_add_component(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    component = COMPONENT_NODE_TYPES.get(
        node_type, str(properties.get("component", "BoxCollider"))
    )
    component_properties = (
        properties.get("properties", {})
        if node_type == "add_component"
        else properties
    )
    target.add_component(
        component,
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

