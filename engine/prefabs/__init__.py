from __future__ import annotations

from engine.prefabs.prefab_serializer import serialize_prefab, deserialize_prefab
from engine.prefabs.prefab_loader import create_prefab_from_object, instantiate_prefab
from engine.prefabs.prefab_asset import (
    apply_exposed_properties,
    create_prefab_variant,
    load_prefab_asset,
    normalize_exposed_properties,
    resolve_prefab_parameters,
)
from engine.prefabs.prefab_overrides import (
    apply_prefab_overrides,
    build_prefab_overrides,
    override_paths,
    revert_prefab_instance,
    update_prefab_instance,
)

__all__ = [
    "serialize_prefab",
    "deserialize_prefab",
    "create_prefab_from_object",
    "instantiate_prefab",
    "apply_exposed_properties",
    "create_prefab_variant",
    "load_prefab_asset",
    "normalize_exposed_properties",
    "resolve_prefab_parameters",
    "apply_prefab_overrides",
    "build_prefab_overrides",
    "override_paths",
    "revert_prefab_instance",
    "update_prefab_instance",
]
