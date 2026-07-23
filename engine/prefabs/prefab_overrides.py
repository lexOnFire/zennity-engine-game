from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, MutableMapping


PREFAB_INSTANCE_FIELDS = {
    "id",
    "name",
    "prefab_guid",
    "prefab_source",
    "prefab_overrides",
}


def build_prefab_overrides(
    prefab_object: Mapping[str, Any],
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a JSON-serializable patch describing instance-only changes."""
    values: dict[str, Any] = {}
    removed: list[str] = []
    base = {
        key: value
        for key, value in prefab_object.items()
        if key not in PREFAB_INSTANCE_FIELDS
    }
    current = {
        key: value
        for key, value in instance.items()
        if key not in PREFAB_INSTANCE_FIELDS
    }
    _collect_changes(base, current, "", values, removed)
    return {
        "values": dict(sorted(values.items())),
        "removed": sorted(removed),
    }


def apply_prefab_overrides(
    prefab_object: Mapping[str, Any],
    overrides: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Apply a persisted instance patch to a fresh Prefab object."""
    result = deepcopy(dict(prefab_object))
    patch = overrides if isinstance(overrides, Mapping) else {}
    removed = patch.get("removed", [])
    if isinstance(removed, list):
        for path in sorted(
            (str(item) for item in removed),
            key=lambda item: item.count("/"),
            reverse=True,
        ):
            _remove_path(result, path)
    values = patch.get("values", {})
    if isinstance(values, Mapping):
        for path, value in sorted(
            values.items(),
            key=lambda item: str(item[0]).count("/"),
        ):
            _set_path(result, str(path), deepcopy(value))
    return result


def update_prefab_instance(
    prefab_object: Mapping[str, Any],
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    """Refresh an instance from its Prefab while retaining its overrides."""
    overrides = instance.get("prefab_overrides", {})
    refreshed = apply_prefab_overrides(prefab_object, overrides)
    _copy_instance_identity(instance, refreshed)
    return refreshed


def revert_prefab_instance(
    prefab_object: Mapping[str, Any],
    instance: Mapping[str, Any],
) -> dict[str, Any]:
    """Restore Prefab values while retaining instance identity/linkage."""
    reverted = deepcopy(dict(prefab_object))
    _copy_instance_identity(instance, reverted)
    reverted["prefab_overrides"] = {"values": {}, "removed": []}
    return reverted


def override_paths(overrides: Mapping[str, Any] | None) -> list[str]:
    patch = overrides if isinstance(overrides, Mapping) else {}
    values = patch.get("values", {})
    removed = patch.get("removed", [])
    paths = list(values) if isinstance(values, Mapping) else []
    if isinstance(removed, list):
        paths.extend(str(item) for item in removed)
    return sorted(set(paths))


def _collect_changes(
    base: Mapping[str, Any],
    current: Mapping[str, Any],
    prefix: str,
    values: MutableMapping[str, Any],
    removed: list[str],
) -> None:
    for key in base.keys() - current.keys():
        removed.append(_join_path(prefix, key))
    for key in current:
        path = _join_path(prefix, key)
        if key not in base:
            values[path] = deepcopy(current[key])
            continue
        old_value = base[key]
        new_value = current[key]
        if isinstance(old_value, Mapping) and isinstance(new_value, Mapping):
            _collect_changes(old_value, new_value, path, values, removed)
        elif old_value != new_value:
            values[path] = deepcopy(new_value)


def _copy_instance_identity(
    instance: Mapping[str, Any],
    target: MutableMapping[str, Any],
) -> None:
    for field in PREFAB_INSTANCE_FIELDS:
        if field in instance:
            target[field] = deepcopy(instance[field])


def _join_path(prefix: str, key: object) -> str:
    token = str(key).replace("~", "~0").replace("/", "~1")
    return f"{prefix}/{token}"


def _path_parts(path: str) -> list[str]:
    if not path.startswith("/"):
        return []
    return [
        token.replace("~1", "/").replace("~0", "~")
        for token in path[1:].split("/")
        if token
    ]


def _set_path(target: MutableMapping[str, Any], path: str, value: Any) -> None:
    parts = _path_parts(path)
    if not parts or any(part.startswith("_") for part in parts):
        return
    cursor = target
    for part in parts[:-1]:
        child = cursor.get(part)
        if not isinstance(child, MutableMapping):
            child = {}
            cursor[part] = child
        cursor = child
    cursor[parts[-1]] = value


def _remove_path(target: MutableMapping[str, Any], path: str) -> None:
    parts = _path_parts(path)
    if not parts or any(part.startswith("_") for part in parts):
        return
    cursor: Any = target
    for part in parts[:-1]:
        if not isinstance(cursor, MutableMapping):
            return
        cursor = cursor.get(part)
    if isinstance(cursor, MutableMapping):
        cursor.pop(parts[-1], None)
