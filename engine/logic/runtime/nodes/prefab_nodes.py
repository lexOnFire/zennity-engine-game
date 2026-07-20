from __future__ import annotations
import math
import random
from typing import Any, Mapping
from engine.logic.runtime.registry import registry

@registry.register_executor('create_object')
def execute_create_object(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    if not runtime._spawn_allowed(game, node_id, properties):
        runtime._store(node_id, "object", None)
        return ["limit_reached"]
    name = str(runtime._read_input(node_id, "name", properties.get("name", "NovoObjeto"), game, dt, set()))
    x = float(runtime._read_input(node_id, "x", properties.get("x", 0.0), game, dt, set()))
    y = float(runtime._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
    if bool(properties.get("relative", False)):
        x += float(game.x)
        y += float(game.y)
    inherit_source = bool(properties.get("inherit_source", True))
    if inherit_source and callable(getattr(game, "clone_object", None)):
        source = (
            runtime._read_input(node_id, "source", game, game, dt, set())
            if (node_id, "source") in runtime.incoming
            else game
        )
        if bool(properties.get("use_pool", False)) and callable(getattr(game, "clone_object_from_pool", None)):
            created = game.clone_object_from_pool(source, name, runtime._spawn_group(node_id))
        else:
            created = game.clone_object(source, name)
        created.x = x
        created.y = y
        created_data = getattr(created, "obj", None)
        if isinstance(created_data, dict) and not bool(properties.get("inherit_logic", False)):
            created_data["logic_graphs"] = []
    else:
        create_values = {
            "name": name, "x": x, "y": y,
            "width": float(properties.get("width", 64.0)),
            "height": float(properties.get("height", 64.0)),
            "color": str(properties.get("color", "#58a6ff")),
            "texture": str(properties.get("texture", "")),
            "tag": str(properties.get("tag", "Untagged")),
        }
        if bool(properties.get("use_pool", False)) and callable(getattr(game, "create_object_from_pool", None)):
            created = game.create_object_from_pool(runtime._spawn_group(node_id), **create_values)
        else:
            created = game.create_object(**create_values)
    runtime._store(node_id, "object", created)
    runtime._node_state.setdefault(node_id, {})["flow_target"] = created
    runtime._configure_spawned(game, created, node_id, properties, dt)
    return ["next"]

@registry.register_executor('create_prefab')
def execute_create_prefab(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    if not runtime._spawn_allowed(game, node_id, properties):
        runtime._store(node_id, "object", None)
        return ["limit_reached"]
    path = str(properties.get("path", "")).strip()
    if not path:
        raise RuntimeError("Escolha um arquivo .zprefab.")
    override_position = bool(properties.get("override_position", True))
    x = float(runtime._read_input(node_id, "x", properties.get("x", 0.0), game, dt, set())) if override_position else None
    y = float(runtime._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set())) if override_position else None
    if override_position and bool(properties.get("relative", False)):
        x = float(x or 0.0) + float(game.x)
        y = float(y or 0.0) + float(game.y)
    rotation = (
        float(runtime._read_input(node_id, "rotation", properties.get("rotation", 0.0), game, dt, set()))
        if bool(properties.get("override_rotation", False)) else None
    )
    width = (
        float(runtime._read_input(node_id, "width", properties.get("width", 64.0), game, dt, set()))
        if bool(properties.get("override_scale", False)) else None
    )
    height = (
        float(runtime._read_input(node_id, "height", properties.get("height", 64.0), game, dt, set()))
        if bool(properties.get("override_scale", False)) else None
    )
    exposed = properties.get("exposed_properties", [])
    defaults = properties.get("parameters", {}) if isinstance(properties.get("parameters"), Mapping) else {}
    parameters: dict[str, Any] = {}
    if isinstance(exposed, list):
        for definition in exposed:
            if not isinstance(definition, Mapping):
                continue
            name = str(definition.get("name", "")).strip()
            if not name:
                continue
            port = str(definition.get("port", f"param_{name}"))
            parameters[name] = runtime._read_input(
                node_id, port, defaults.get(name, definition.get("default")), game, dt, set()
            )
    prefab_options = {
        "rotation": rotation, "width": width, "height": height,
        "include_camera": bool(properties.get("include_camera", False)),
        "include_audio": bool(properties.get("include_audio", False)),
        "include_logic": bool(properties.get("include_logic", False)),
        "parameters": parameters,
    }
    if bool(properties.get("use_pool", True)) and callable(getattr(game, "create_prefab_from_pool", None)):
        created = game.create_prefab_from_pool(
            path, x, y, runtime._spawn_group(node_id), **prefab_options
        )
    else:
        created = game.create_prefab(path, x, y, **prefab_options)
    runtime._store(node_id, "object", created)
    runtime._store(node_id, "parameters", parameters)
    runtime._node_state.setdefault(node_id, {})["flow_target"] = created
    lifecycle_properties = dict(properties)
    if isinstance(exposed, list):
        for definition in exposed:
            if not isinstance(definition, Mapping):
                continue
            semantic = str(definition.get("semantic", ""))
            name = str(definition.get("name", ""))
            if semantic in {"lifetime", "max_distance", "max_instances"} and name in parameters:
                lifecycle_properties[semantic] = parameters[name]
    runtime._configure_spawned(game, created, node_id, lifecycle_properties, dt)
    return ["next"]

@registry.register_executor('clone_object')
def execute_clone_object(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    if not runtime._spawn_allowed(game, node_id, properties):
        runtime._store(node_id, "object", None)
        return ["limit_reached"]
    target = runtime._read_target(node_id, game, dt, set())
    name = str(runtime._read_input(node_id, "name", properties.get("name", ""), game, dt, set()))
    if bool(properties.get("use_pool", False)) and callable(getattr(game, "clone_object_from_pool", None)):
        created = game.clone_object_from_pool(target, name, runtime._spawn_group(node_id))
    else:
        created = game.clone_object(target, name)
    runtime._store(node_id, "object", created)
    runtime._node_state.setdefault(node_id, {})["flow_target"] = created
    runtime._configure_spawned(game, created, node_id, properties, dt)
    return ["next"]

@registry.register_evaluator('get_prefab_parameter')
def evaluate_get_prefab_parameter(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, branch)
    getter = getattr(target, "prefab_parameter", None)
    name = str(properties.get("name", "speed"))
    value = getter(name, properties.get("default")) if callable(getter) else properties.get("default")
    return value

@registry.register_evaluator(('create_object', 'create_prefab', 'clone_object'))
def evaluate_create_object_or_create_prefab_or_clone_object(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = runtime.values.get((node_id, "object"))
    return value

