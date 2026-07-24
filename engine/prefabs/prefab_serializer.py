from __future__ import annotations

import uuid
from typing import Any
from engine.game_object import GameObject
from engine.scene.scene_serializer import serialize_game_object, deserialize_game_object


def serialize_prefab(obj: GameObject, prefab_uuid: str | None = None) -> dict[str, Any]:
    """Serializes a GameObject into a .zprefab structure."""
    obj_data = serialize_game_object(obj)
    
    p_uuid = prefab_uuid or getattr(obj, "prefab_uuid", None) or str(uuid.uuid4())
    
    return {
        "format_version": 2,
        "prefab_uuid": p_uuid,
        "name": obj_data.get("name", "Prefab"),
        "source_object_name": obj_data.get("name", "GameObject"),
        "transform": obj_data.get("transform", {}),
        "components": obj_data.get("components", {}),
        "visual": obj_data.get("visual", {}),
        "children": [],  # Prepared for future nested child game objects
        "exposed_properties": [
            {"name": "width", "label": "Largura", "type": "number", "default": obj_data.get("transform", {}).get("scale", [64, 64, 1])[0], "target": "transform.scale.0"},
            {"name": "height", "label": "Altura", "type": "number", "default": obj_data.get("transform", {}).get("scale", [64, 64, 1])[1], "target": "transform.scale.1"},
            {"name": "color", "label": "Cor", "type": "color", "default": obj_data.get("visual", {}).get("color", [255, 255, 255]), "target": "visual.color"},
            {"name": "image", "label": "Imagem", "type": "image", "default": obj_data.get("visual", {}).get("texture", ""), "target": "visual.texture", "asset_kind": "image"},
            {"name": "tag", "label": "Tag", "type": "text", "default": obj_data.get("tag", "Untagged"), "target": "tag"},
            {"name": "layer", "label": "Layer", "type": "text", "default": obj_data.get("layer", "Default"), "target": "layer"},
        ],
    }


def deserialize_prefab(data: dict[str, Any]) -> GameObject:
    """Deserializes a .zprefab dict into a GameObject instance."""
    obj_data = {
        "name": data.get("source_object_name") or data.get("name", "GameObject"),
        "transform": data.get("transform", {}),
        "components": data.get("components", {}),
        "visual": data.get("visual", {}),
    }
    
    obj = deserialize_game_object(obj_data)
    obj.prefab_uuid = data.get("prefab_uuid")
    return obj
