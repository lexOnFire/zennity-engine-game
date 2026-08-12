from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry

# PHASE 9 recovery item 4.2: the play_animation and stop_animation executors
# that used to live here were the losing half of a split brain. They assumed
# ``game.animator`` existed on the game object itself and ignored ``target``;
# animation_nodes resolves the real Animator component and has a failure path.
# Only one executor may own a node id.

@registry.register_executor('play_animation_asset')
def execute_play_animation_asset(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    path = str(runtime._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
    if path:
        game.play_animation_asset(path)
    return ["next"]

@registry.register_executor('play_sound')
def execute_play_sound(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    path = str(runtime._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
    if path:
        game.play_sound(path)
    return ["next"]

@registry.register_executor('set_sprite')
def execute_set_sprite(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    path = str(runtime._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
    if path:
        target.set_sprite(path)
    return ["next"]

@registry.register_executor('start_texture_scroll')
def execute_start_texture_scroll(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    path = str(runtime._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
    speed_x = float(runtime._read_input(node_id, "speed_x", properties.get("speed_x", 0.0), game, dt, set()))
    speed_y = float(runtime._read_input(node_id, "speed_y", properties.get("speed_y", 80.0), game, dt, set()))
    target.start_texture_scroll(
        speed_x,
        speed_y,
        repeat_x=bool(properties.get("repeat_x", False)),
        repeat_y=bool(properties.get("repeat_y", True)),
        parallax=float(properties.get("parallax", 1.0)),
        image_path=path,
        send_to_background=bool(properties.get("send_to_background", True)),
    )
    return ["next"]

@registry.register_executor('stop_texture_scroll')
def execute_stop_texture_scroll(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    target.stop_texture_scroll(reset=bool(properties.get("reset", False)))
    return ["next"]

@registry.register_executor('set_position')
def execute_set_position(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    target.x = float(runtime._read_input(node_id, "x", properties.get("x", 0.0), game, dt, set()))
    target.y = float(runtime._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
    return ["next"]

@registry.register_executor('rotate')
def execute_rotate(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    degrees = float(runtime._read_input(node_id, "degrees", properties.get("degrees", 90.0), game, dt, set()))
    target.rotation += degrees
    return ["next"]

@registry.register_executor('set_active')
def execute_set_active(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    target.active = bool(runtime._read_input(node_id, "active", properties.get("active", True), game, dt, set()))
    return ["next"]

@registry.register_executor('destroy_object')
def execute_destroy_object(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    target.destroy()
    return []

@registry.register_executor('destroy_after_time')
def execute_destroy_after_time(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    seconds = float(runtime._read_input(node_id, "seconds", properties.get("seconds", 2.0), game, dt, set()))
    target.destroy_after(seconds)
    return ["next"]

@registry.register_executor('log_message')
def execute_log_message(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    # "message" é o nome legado da property (ver NODE_DEFINITIONS["log_message"]);
    # aceito como fallback para assets criados antes do alinhamento com o pino "text".
    fallback = properties.get("text", properties.get("message", "Mensagem"))
    text = runtime._read_input(node_id, "text", fallback, game, dt, set())
    game.log(str(text))
    return ["next"]

@registry.register_executor('start_behavior_tree')
def execute_start_behavior_tree(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, set())
    raw_path = runtime._read_input(node_id, "path", properties.get("path", ""), game, dt, set())
    path = "" if raw_path is None else str(raw_path).strip()
    if hasattr(target, "start_behavior_tree"):
        target.start_behavior_tree(path)
    elif hasattr(game, "start_behavior_tree"):
        game.start_behavior_tree(path)
    return ["next"]

