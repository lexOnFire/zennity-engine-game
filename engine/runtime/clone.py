from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import numpy as np

from engine.core.component import Transform
from engine.core.component_registry import component_registry
from engine.game_object import GameObject


_SKIP_COMPONENT_ATTRS = {"id", "game_object", "_started"}


def _is_runtime_resource(value: Any) -> bool:
    """Return True for objects that must not be copied into runtime clones."""
    module = type(value).__module__
    type_name = type(value).__name__
    if module.startswith("pygame"):
        return True
    if type_name in {"Surface", "Font", "Sound", "Clock"}:
        return True
    return False


def _safe_copy_value(value: Any) -> Any:
    if _is_runtime_resource(value):
        return None
    if isinstance(value, np.ndarray):
        return value.copy()
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, Path):
        return Path(value)
    if isinstance(value, tuple):
        return tuple(_safe_copy_value(item) for item in value if not _is_runtime_resource(item))
    if isinstance(value, list):
        return [_safe_copy_value(item) for item in value if not _is_runtime_resource(item)]
    if isinstance(value, dict):
        return {
            _safe_copy_value(key): _safe_copy_value(item)
            for key, item in value.items()
            if not _is_runtime_resource(key) and not _is_runtime_resource(item)
        }
    return value


def _copy_optional_attr(source: Any, target: Any, name: str) -> None:
    if hasattr(source, name):
        value = _safe_copy_value(getattr(source, name))
        if value is not None:
            setattr(target, name, value)


def _clone_component_by_constructor(component: Any) -> Any:
    clone = type(component)()
    for name, value in vars(component).items():
        if name in _SKIP_COMPONENT_ATTRS:
            continue
        if _is_runtime_resource(value):
            continue
        try:
            setattr(clone, name, _safe_copy_value(value))
        except Exception:
            continue
    return clone


def _clone_component(component: Any) -> Any:
    clone = None
    if hasattr(component, "serialize"):
        try:
            clone = component_registry.create(component.serialize())
        except Exception:
            clone = None
    if clone is None:
        try:
            clone = _clone_component_by_constructor(component)
        except Exception:
            clone = type(component)()
    if hasattr(clone, "id"):
        clone.id = str(uuid.uuid4())
    if hasattr(clone, "_started"):
        clone._started = False
    if hasattr(clone, "game_object"):
        clone.game_object = None
    for attr in (
        "sorting_layer", "order_in_layer", "color", "alpha", "flip_x", "flip_y",
    ):
        _copy_optional_attr(component, clone, attr)
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
