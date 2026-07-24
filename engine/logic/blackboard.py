"""Blackboard tipado e independente de Qt/Pygame para Logic Graphs."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


BLACKBOARD_FORMAT = "zennity.blackboard"
BLACKBOARD_VERSION = 1
VARIABLE_SCOPES = ("object", "scene", "project")
VARIABLE_TYPES = ("number", "bool", "text", "object")


def infer_variable_type(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "text"
    return "object"


def coerce_variable_value(value: Any, variable_type: str) -> Any:
    kind = str(variable_type).lower()
    if kind == "number":
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    if kind == "bool":
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "verdadeiro", "sim", "yes", "on"}
        return bool(value)
    if kind == "text":
        return "" if value is None else str(value)
    return deepcopy(value)


def normalize_variable_definition(value: Any) -> dict[str, Any]:
    raw = dict(value) if isinstance(value, Mapping) else {"default": deepcopy(value)}
    default = deepcopy(raw.get("default", raw.get("value")))
    variable_type = str(raw.get("type", infer_variable_type(default))).lower()
    scope = str(raw.get("scope", "object")).lower()
    if variable_type not in VARIABLE_TYPES:
        variable_type = infer_variable_type(default)
    if scope not in VARIABLE_SCOPES:
        scope = "object"
    return {
        "type": variable_type,
        "scope": scope,
        "default": coerce_variable_value(default, variable_type),
    }


def normalize_variable_definitions(values: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(values, Mapping):
        return {}
    return {
        str(name): normalize_variable_definition(definition)
        for name, definition in values.items()
        if str(name).strip()
    }


def default_blackboard_asset() -> dict[str, Any]:
    return {
        "format": BLACKBOARD_FORMAT,
        "version": BLACKBOARD_VERSION,
        "variables": {},
    }


def normalize_blackboard_asset(data: Any) -> dict[str, Any]:
    result = default_blackboard_asset()
    if isinstance(data, Mapping):
        result["variables"] = normalize_variable_definitions(data.get("variables", data))
    return result


def load_blackboard_asset(path: str | Path) -> dict[str, Any]:
    return normalize_blackboard_asset(json.loads(Path(path).read_text(encoding="utf-8")))


def save_blackboard_asset(path: str | Path, data: Any) -> dict[str, Any]:
    target = Path(path)
    if target.suffix.lower() != ".zblackboard":
        target = target.with_suffix(".zblackboard")
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_blackboard_asset(data)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(target)
    return normalized


class BlackboardStore:
    """Armazena valores locais e compartilhados usando definições tipadas."""

    def __init__(self, scene: Any = None, project: Any = None) -> None:
        self.definitions: dict[str, dict[str, dict[str, Any]]] = {
            "object": {}, "scene": {}, "project": {},
        }
        self.object_definitions: dict[str, dict[str, dict[str, Any]]] = {}
        self.object_values: dict[str, dict[str, Any]] = {}
        self.shared_values: dict[str, dict[str, Any]] = {"scene": {}, "project": {}}
        self.register(normalize_blackboard_asset(scene).get("variables", {}), "__scene__")
        self.register(normalize_blackboard_asset(project).get("variables", {}), "__project__")

    def register(self, definitions: Any, object_key: str) -> None:
        for name, definition in normalize_variable_definitions(definitions).items():
            scope = definition["scope"]
            if scope == "object":
                object_definitions = self.object_definitions.setdefault(str(object_key), {})
                object_definitions[name] = deepcopy(definition)
                values = self.object_values.setdefault(str(object_key), {})
                values.setdefault(name, deepcopy(definition["default"]))
                continue
            self.definitions[scope][name] = deepcopy(definition)
            self.shared_values[scope].setdefault(name, deepcopy(definition["default"]))

    def values_for_object(self, object_key: str) -> dict[str, Any]:
        return self.object_values.setdefault(str(object_key), {})

    def get(self, scope: str, name: str, object_key: str) -> Any:
        normalized_scope = scope if scope in VARIABLE_SCOPES else "object"
        if normalized_scope == "object":
            return deepcopy(self.object_values.get(str(object_key), {}).get(str(name)))
        return deepcopy(self.shared_values[normalized_scope].get(str(name)))

    def set(self, scope: str, name: str, value: Any, object_key: str) -> Any:
        normalized_scope = scope if scope in VARIABLE_SCOPES else "object"
        if normalized_scope == "object":
            definitions = self.object_definitions.setdefault(str(object_key), {})
            definition = definitions.setdefault(str(name), normalize_variable_definition(value))
            target = self.object_values.setdefault(str(object_key), {})
        else:
            definitions = self.definitions[normalized_scope]
            definition = definitions.setdefault(
                str(name), {**normalize_variable_definition(value), "scope": normalized_scope}
            )
            target = self.shared_values[normalized_scope]
        converted = coerce_variable_value(value, definition["type"])
        target[str(name)] = converted
        return deepcopy(converted)

    def find(self, name: str, object_key: str) -> tuple[str, Any] | None:
        if str(name) in self.object_values.get(str(object_key), {}):
            return "object", self.get("object", name, object_key)
        for scope in ("scene", "project"):
            if str(name) in self.shared_values[scope]:
                return scope, self.get(scope, name, object_key)
        return None

    def reset_object(self, object_key: str) -> None:
        definitions = self.object_definitions.get(str(object_key), {})
        self.object_values[str(object_key)] = {
            name: deepcopy(definition["default"]) for name, definition in definitions.items()
        }

    def snapshot(self, object_key: str) -> dict[str, dict[str, Any]]:
        return {
            "object": deepcopy(self.object_values.get(str(object_key), {})),
            "scene": deepcopy(self.shared_values["scene"]),
            "project": deepcopy(self.shared_values["project"]),
        }
