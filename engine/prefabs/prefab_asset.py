"""Formato portátil de Prefabs parametrizáveis e variantes com herança."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, MutableMapping


PREFAB_FORMAT_VERSION = 2
PREFAB_PROPERTY_TYPES = {"number", "bool", "text", "color", "image", "animation", "audio"}


def parameter_port(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", str(name).strip()).strip("_") or "value"
    return f"param_{safe}"


def port_type(property_type: str) -> str:
    return {"number": "number", "bool": "bool"}.get(str(property_type).lower(), "text")


def coerce_prefab_value(value: Any, property_type: str) -> Any:
    kind = str(property_type).lower()
    if kind == "number":
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    if kind == "bool":
        if isinstance(value, str):
            return value.strip().casefold() in {"1", "true", "sim", "yes", "on"}
        return bool(value)
    if kind == "color":
        if isinstance(value, (list, tuple)) and len(value) >= 3:
            return [max(0, min(255, int(channel))) for channel in value[:3]]
        text = str(value).strip()
        return text if text else "#ffffff"
    return "" if value is None else str(value)


def normalize_exposed_properties(values: Any) -> list[dict[str, Any]]:
    source = values if isinstance(values, list) else []
    result: list[dict[str, Any]] = []
    names: set[str] = set()
    for raw in source:
        if not isinstance(raw, Mapping):
            continue
        name = str(raw.get("name", "")).strip()
        if not name or name in names:
            continue
        names.add(name)
        kind = str(raw.get("type", "text")).lower()
        if kind not in PREFAB_PROPERTY_TYPES:
            kind = "text"
        definition = {
            "name": name,
            "label": str(raw.get("label", name)).strip() or name,
            "type": kind,
            "default": coerce_prefab_value(raw.get("default"), kind),
            "target": str(raw.get("target", name)).strip() or name,
            "port": parameter_port(name),
        }
        for key in ("minimum", "maximum", "description", "asset_kind", "semantic"):
            if key in raw:
                definition[key] = deepcopy(raw[key])
        result.append(definition)
    return result


def _merge_dict(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _resolve_reference(value: str, current: Path, project_root: Path) -> Path:
    raw = Path(str(value))
    candidate = raw if raw.is_absolute() else (project_root / raw if raw.parts and raw.parts[0].casefold() == "assets" else current.parent / raw)
    resolved = candidate.resolve()
    root = project_root.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("O Prefab base precisa estar dentro do projeto.")
    return resolved


def load_prefab_asset(
    path: str | Path,
    project_root: str | Path | None = None,
    _stack: tuple[Path, ...] = (),
) -> dict[str, Any]:
    target = Path(path)
    root = Path(project_root or Path.cwd()).resolve()
    if not target.is_absolute():
        target = root / target
    target = target.resolve()
    if target in _stack:
        chain = " → ".join(item.name for item in (*_stack, target))
        raise ValueError(f"Herança circular de Prefab: {chain}")
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Prefab precisa conter um objeto JSON.")

    base_reference = str(payload.get("base_prefab", "")).strip()
    if base_reference:
        base_path = _resolve_reference(base_reference, target, root)
        base = load_prefab_asset(base_path, root, (*_stack, target))
        base_object = base.get("object", {}) if isinstance(base.get("object"), Mapping) else {}
        object_override = payload.get("object_overrides", payload.get("object", {}))
        object_value = _merge_dict(base_object, object_override if isinstance(object_override, Mapping) else {})
        definitions_by_name = {item["name"]: item for item in base.get("exposed_properties", [])}
        for item in normalize_exposed_properties(payload.get("exposed_properties", [])):
            definitions_by_name[item["name"]] = item
        property_overrides = payload.get("property_overrides", {})
        if isinstance(property_overrides, Mapping):
            for name, value in property_overrides.items():
                if str(name) in definitions_by_name:
                    definition = definitions_by_name[str(name)]
                    definition["default"] = coerce_prefab_value(value, definition["type"])
        definitions = list(definitions_by_name.values())
    else:
        raw_object = payload.get("object")
        if not isinstance(raw_object, Mapping):
            # Compatibilidade com o serializador antigo.
            raw_object = {
                "name": payload.get("source_object_name", payload.get("name", "Prefab")),
                "transform": payload.get("transform", {}),
                "visual": payload.get("visual", {}),
                "components": payload.get("components", {}),
                "tag": payload.get("tag", "Untagged"),
                "layer": payload.get("layer", "Default"),
                "active": payload.get("active", payload.get("enabled", True)),
                "prefab_uuid": payload.get("prefab_uuid"),
            }
        object_value = deepcopy(dict(raw_object))
        definitions = normalize_exposed_properties(payload.get("exposed_properties", []))

    return {
        "format_version": max(1, int(payload.get("format_version", 1))),
        "prefab_name": str(payload.get("prefab_name", payload.get("name", target.stem))),
        "base_prefab": base_reference,
        "source_path": target.as_posix(),
        "object": object_value,
        "exposed_properties": definitions,
    }


def resolve_prefab_parameters(definitions: list[Mapping[str, Any]], overrides: Any) -> dict[str, Any]:
    supplied = overrides if isinstance(overrides, Mapping) else {}
    return {
        str(definition["name"]): coerce_prefab_value(
            supplied.get(str(definition["name"]), definition.get("default")),
            str(definition.get("type", "text")),
        )
        for definition in definitions
    }


def apply_exposed_properties(
    obj: MutableMapping[str, Any], definitions: list[Mapping[str, Any]], values: Mapping[str, Any]
) -> None:
    for definition in definitions:
        name = str(definition.get("name", ""))
        target = str(definition.get("target", name)).strip()
        if not name or not target:
            continue
        parts = [part for part in target.split(".") if part]
        if not parts or any(part.startswith("_") for part in parts):
            continue
        cursor: Any = obj
        for part in parts[:-1]:
            if isinstance(cursor, MutableMapping):
                child = cursor.get(part)
                if not isinstance(child, (MutableMapping, list)):
                    child = {}
                    cursor[part] = child
            elif isinstance(cursor, list) and part.isdigit():
                index = int(part)
                while len(cursor) <= index:
                    cursor.append({})
                child = cursor[index]
                if not isinstance(child, (MutableMapping, list)):
                    child = {}
                    cursor[index] = child
            else:
                break
            cursor = child
        else:
            value = deepcopy(values.get(name, definition.get("default")))
            final = parts[-1]
            if isinstance(cursor, MutableMapping):
                cursor[final] = value
            elif isinstance(cursor, list) and final.isdigit():
                index = int(final)
                while len(cursor) <= index:
                    cursor.append(None)
                cursor[index] = value


def create_prefab_variant(
    base_path: str | Path,
    variant_path: str | Path,
    *,
    property_overrides: Mapping[str, Any] | None = None,
    object_overrides: Mapping[str, Any] | None = None,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root or Path.cwd()).resolve()
    base_input = Path(base_path)
    target_input = Path(variant_path)
    base = (base_input if base_input.is_absolute() else root / base_input).resolve()
    target = (target_input if target_input.is_absolute() else root / target_input).resolve()
    if not base.is_relative_to(root) or not target.is_relative_to(root):
        raise ValueError("Prefabs e variantes precisam estar dentro do projeto.")
    payload = {
        "format_version": PREFAB_FORMAT_VERSION,
        "prefab_name": target.stem,
        "base_prefab": base.relative_to(root).as_posix(),
        "property_overrides": deepcopy(dict(property_overrides or {})),
        "object_overrides": deepcopy(dict(object_overrides or {})),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
