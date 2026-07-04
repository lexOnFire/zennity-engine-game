from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from engine.game_object import GameObject
from engine.physics.collider import BoxCollider, CircleCollider
from engine.physics.rigidbody import RigidBody
from engine.scene.scene_format import DEFAULT_SCENE_NAME, ENGINE_VERSION, SCENE_FORMAT_VERSION


def _vector(value: Any, size: int, default: float) -> list[float]:
    if value is None:
        return [default for _ in range(size)]
    values = list(value)
    if len(values) < size:
        values.extend(default for _ in range(size - len(values)))
    return [float(item) for item in values[:size]]


def _get_scene_objects(scene: Any) -> list[Any]:
    objects = getattr(scene, "editable_objects", None)
    if objects is None:
        objects = getattr(scene, "game_objects", [])
    return list(objects)


def _component_by_class_name(obj: GameObject, *class_names: str) -> Any:
    names = set(class_names)
    for component in getattr(obj, "components", []):
        if type(component).__name__ in names:
            return component
    return None


def _serialize_collider(obj: GameObject) -> dict[str, Any] | None:
    box = _component_by_class_name(obj, "BoxCollider", "BoxCollider2D")
    if box is not None:
        return {
            "type": "box",
            "width": float(box.width),
            "height": float(box.height),
            "offset": [float(box.offset_x), float(box.offset_y)],
            "is_trigger": bool(box.is_trigger),
            "debug_draw": bool(box.debug_draw),
        }

    circle = _component_by_class_name(obj, "CircleCollider")
    if circle is not None:
        return {
            "type": "circle",
            "radius": float(circle.radius),
            "offset": [float(circle.offset_x), float(circle.offset_y)],
            "is_trigger": bool(circle.is_trigger),
            "debug_draw": bool(circle.debug_draw),
        }

    return None


def _serialize_rigidbody(obj: GameObject) -> dict[str, Any] | None:
    rigidbody = _component_by_class_name(obj, "RigidBody")
    if rigidbody is None:
        return None

    return {
        "mass": float(rigidbody.mass),
        "gravity_scale": float(rigidbody.gravity_scale),
        "drag": float(rigidbody.drag),
        "use_gravity": bool(rigidbody.use_gravity),
        "is_kinematic": bool(rigidbody.is_kinematic),
        "velocity": _vector(rigidbody.velocity, 2, 0.0),
        "acceleration": _vector(rigidbody.acceleration, 2, 0.0),
    }


def serialize_game_object(obj: GameObject) -> dict[str, Any]:
    """Serialize one GameObject into .zscene-compatible data."""
    transform = obj.transform
    rotation = _vector(transform.rotation, 3, 0.0)
    components: dict[str, Any] = {"scripts": list(getattr(obj, "scripts", []))}

    collider = _serialize_collider(obj)
    if collider is not None:
        components["collider"] = collider

    rigidbody = _serialize_rigidbody(obj)
    if rigidbody is not None:
        components["rigidbody"] = rigidbody

    object_id = str(getattr(obj, "id", getattr(obj, "uuid", "")))
    return {
        "id": object_id,
        "uuid": object_id,
        "name": str(getattr(obj, "name", "GameObject")),
        "tag": str(getattr(obj, "tag", "Untagged")),
        "layer": int(getattr(obj, "layer", 0)),
        "active": bool(getattr(obj, "active", True)),
        "enabled": bool(getattr(obj, "enabled", getattr(obj, "active", True))),
        "transform": {
            "position": _vector(transform.position, 3, 0.0),
            "rotation": rotation,
            "rz": float(getattr(transform, "rz", rotation[2])),
            "scale": _vector(transform.scale, 3, 1.0),
        },
        "visual": {
            "mesh_type": getattr(obj, "mesh_type", None),
            "sprite_path": getattr(obj, "sprite_path", None),
            "color": getattr(obj, "color", None),
            "material": getattr(obj, "material", None),
        },
        "components": components,
    }


def serialize_scene(scene: Any) -> dict[str, Any]:
    """Serialize a scene-like object into a JSON-ready dictionary."""
    return {
        "format_version": SCENE_FORMAT_VERSION,
        "scene_name": str(getattr(scene, "name", DEFAULT_SCENE_NAME)),
        "engine_version": ENGINE_VERSION,
        "objects": [serialize_game_object(obj) for obj in _get_scene_objects(scene)],
    }


def _deserialize_collider(data: dict[str, Any]) -> BoxCollider | CircleCollider | None:
    collider_type = str(data.get("type", "box")).lower()
    offset = _vector(data.get("offset", [data.get("offset_x", 0.0), data.get("offset_y", 0.0)]), 2, 0.0)

    if collider_type == "circle":
        return CircleCollider(
            radius=float(data.get("radius", 16.0)),
            offset_x=offset[0],
            offset_y=offset[1],
            is_trigger=bool(data.get("is_trigger", False)),
            debug_draw=bool(data.get("debug_draw", False)),
        )

    if collider_type in {"box", "aabb", "rect", "rectangle"}:
        return BoxCollider(
            width=float(data.get("width", 32.0)),
            height=float(data.get("height", 32.0)),
            offset_x=offset[0],
            offset_y=offset[1],
            is_trigger=bool(data.get("is_trigger", False)),
            debug_draw=bool(data.get("debug_draw", False)),
        )

    return None


def _deserialize_rigidbody(data: dict[str, Any]) -> RigidBody:
    rigidbody = RigidBody(
        mass=float(data.get("mass", 1.0)),
        gravity_scale=float(data.get("gravity_scale", 1.0)),
        drag=float(data.get("drag", 0.0)),
        use_gravity=bool(data.get("use_gravity", True)),
        is_kinematic=bool(data.get("is_kinematic", False)),
    )
    rigidbody.velocity = np.array(_vector(data.get("velocity"), 2, 0.0), dtype=np.float32)
    rigidbody.acceleration = np.array(_vector(data.get("acceleration"), 2, 0.0), dtype=np.float32)
    return rigidbody


def deserialize_game_object(data: dict[str, Any]) -> GameObject:
    """Build a GameObject from .zscene object data."""
    obj = GameObject(
        name=str(data.get("name", "GameObject")),
        tag=str(data.get("tag", "Untagged")),
    )

    object_id = data.get("id") or data.get("uuid")
    if object_id:
        obj._id = str(object_id)

    obj.layer = int(data.get("layer", 0))
    obj.active = bool(data.get("active", data.get("enabled", True)))
    obj.enabled = bool(data.get("enabled", obj.active))

    visual = data.get("visual", {}) or {}
    obj.mesh_type = visual.get("mesh_type")
    obj.sprite_path = visual.get("sprite_path")
    if visual.get("color") is not None:
        obj.color = visual.get("color")
    if visual.get("material") is not None:
        obj.material = visual.get("material")

    transform = data.get("transform", {}) or {}
    obj.transform.position = np.array(_vector(transform.get("position"), 3, 0.0), dtype=np.float32)
    rotation = _vector(transform.get("rotation"), 3, 0.0)
    if "rz" in transform:
        rotation[2] = float(transform["rz"])
    obj.transform.rotation = np.array(rotation, dtype=np.float32)
    obj.transform.scale = np.array(_vector(transform.get("scale"), 3, 1.0), dtype=np.float32)

    components = data.get("components", {}) or {}
    collider_data = components.get("collider")
    if isinstance(collider_data, dict):
        collider = _deserialize_collider(collider_data)
        if collider is not None:
            obj.add_component(collider)

    rigidbody_data = components.get("rigidbody")
    if isinstance(rigidbody_data, dict):
        obj.add_component(_deserialize_rigidbody(rigidbody_data))

    scripts = components.get("scripts")
    if isinstance(scripts, list):
        obj.scripts = list(scripts)

    return obj


def deserialize_scene(data: dict[str, Any]) -> dict[str, Any]:
    """Deserialize .zscene data into a scene data model."""
    return {
        "format_version": int(data.get("format_version", SCENE_FORMAT_VERSION)),
        "scene_name": str(data.get("scene_name", DEFAULT_SCENE_NAME)),
        "engine_version": str(data.get("engine_version", ENGINE_VERSION)),
        "objects": [
            deserialize_game_object(item)
            for item in data.get("objects", [])
            if isinstance(item, dict)
        ],
    }


def save_scene(scene: Any, path: str | Path) -> Path:
    """Save a scene-like object as a .zscene JSON file."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(serialize_scene(scene), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
