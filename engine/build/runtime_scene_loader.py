"""Carregador leve de cenas usado pelo runtime de desenvolvimento exportado.

Este módulo não importa Pygame, Qt ou o pacote completo da engine. Isso permite
validar uma cena exportada antes de abrir a janela do jogo.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def load_objects(path: str | Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    objects = payload.get("objects", [])
    if not isinstance(objects, list):
        raise ValueError("A cena exportada precisa conter uma lista 'objects'.")
    return [_load_object(item) for item in objects if isinstance(item, dict)]


def _load_object(item: dict[str, Any]) -> dict[str, Any]:
    transform = item.get("transform") if isinstance(item.get("transform"), dict) else {}
    position = _vector(transform.get("position"), [item.get("x", 0), item.get("y", 0), 0])
    scale = _vector(transform.get("scale"), [item.get("w", 32), item.get("h", 32), 1])
    rotation_vector = _vector(transform.get("rotation"), [0, 0, item.get("rotation", 0)])
    visual = item.get("visual") if isinstance(item.get("visual"), dict) else {}
    components = item.get("components") if isinstance(item.get("components"), dict) else {}
    rotation = transform.get("rz", rotation_vector[2])

    obj: dict[str, Any] = {
        "id": item.get("id", item.get("name")),
        "name": str(item.get("name", "Object")),
        "x": float(position[0]),
        "y": float(position[1]),
        "w": abs(float(scale[0])),
        "h": abs(float(scale[1])),
        "rotation": float(rotation),
        "color": deepcopy(visual.get("color", item.get("color", [180, 180, 190]))),
        "tag": str(item.get("tag", "Untagged")),
        "layer": str(item.get("layer", "Default")),
        "static": bool(item.get("static", False)),
        "active": bool(item.get("active", item.get("enabled", True))),
        "scripts": [str(script) for script in components.get("scripts", item.get("scripts", []))],
        "texture": str(visual.get("texture", item.get("texture", ""))),
        "renderer_enabled": bool(visual.get("enabled", item.get("renderer_enabled", True))),
        "render_layer": str(visual.get("layer", item.get("render_layer", "Default"))),
        "sort_order": int(visual.get("order", item.get("sort_order", 0))),
    }
    editor_data = item.get("editor_data")
    if isinstance(editor_data, dict):
        obj.update(deepcopy(editor_data))
    for key in ("rigidbody", "collider", "camera", "audio"):
        value = components.get(key, item.get(key))
        if isinstance(value, dict):
            obj[key] = deepcopy(value)
    for component in components.get("items", []):
        ui = _scene_item_to_ui(component)
        if ui is not None:
            obj["ui"] = ui
    return obj


def _vector(value: Any, fallback: list[Any]) -> list[Any]:
    result = list(value) if isinstance(value, (list, tuple)) else list(fallback)
    return (result + list(fallback))[0:3]


def _scene_item_to_ui(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    kind = {
        "canvas": "canvas",
        "label": "text",
        "uilabel": "text",
        "image": "image",
        "uiimage": "image",
        "button": "button",
        "uibutton": "button",
    }.get(str(item.get("type", "")).lower())
    if kind is None:
        return None
    properties = deepcopy(item.get("properties")) if isinstance(item.get("properties"), dict) else {}
    properties["type"] = kind
    if "sprite_path" in properties and "path" not in properties:
        properties["path"] = properties.pop("sprite_path")
    properties.setdefault("visible", bool(item.get("enabled", True)))
    return properties

