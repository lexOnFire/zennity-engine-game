from __future__ import annotations

import uuid
from typing import Any

import numpy as np

from engine.core.component import Transform
from engine.core.component_registry import component_registry
from engine.game_object import GameObject


def _copy_optional_attr(source: Any, target: Any, name: str) -> None:
    if hasattr(source, name):
        value = getattr(source, name)
        if isinstance(value, np.ndarray):
            value = value.copy()
        elif isinstance(value, list):
            value = list(value)
        elif isinstance(value, dict):
            value = dict(value)
        setattr(target, name, value)


def _clone_component(component: Any) -> Any:
    if hasattr(component, "serialize"):
        clone = component_registry.create(component.serialize())
    else:
        clone = type(component)()
    if hasattr(clone, "id"):
        clone.id = str(uuid.uuid4())
    if hasattr(clone, "_started"):
        clone._started = False
    if hasattr(clone, "game_object"):
        clone.game_object = None
    return clone


def clone_game_object(source: GameObject) -> GameObject:
    """Create a fully detached runtime copy of a GameObject tree."""
    clone = GameObject(
        name=str(getattr(source, "name", "GameObject")),
        tag=str(getattr(source, "tag", "Untagged")),
    )
    clone.runtime_source_id = str(getattr(source, "id", ""))

    for attr in (
        "layer",
        "active",
        "enabled",
        "is_static",
        "mesh_type",
        "sprite_path",
        "asset_uuid",
        "color",
        "material",
        "prefab_uuid",
        "scripts",
        "script_path",
    ):
        _copy_optional_attr(source, clone, attr)

    clone.transform.position = np.array(source.transform.position, dtype=np.float32).copy()
    clone.transform.rotation = np.array(source.transform.rotation, dtype=np.float32).copy()
    clone.transform.scale = np.array(source.transform.scale, dtype=np.float32).copy()
    clone.transform.id = str(uuid.uuid4())
    clone.transform._started = False

    for component in getattr(source, "components", []):
        if isinstance(component, Transform) or component is getattr(source, "transform", None):
            continue
        clone.add_component(_clone_component(component))

    for child in getattr(source, "children", []):
        clone.add_child(clone_game_object(child))

    return clone
