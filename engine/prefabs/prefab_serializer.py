from __future__ import annotations

import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
from engine.game_object import GameObject
from engine.scene.scene_serializer import serialize_game_object, deserialize_game_object


# ── Overrides de Instância ──────────────────────────────────────────────────

@dataclass
class PrefabInstanceOverride:
    """Registra as propriedades que foram alteradas em uma instância de prefab,
    de forma que possam ser reaplicadas após uma re-importação do prefab base.
    """
    prefab_uuid: str
    overrides: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        """Registra um override de propriedade."""
        self.overrides[key] = deepcopy(value)

    def clear(self, key: str) -> None:
        """Remove um override, revertendo para o valor do prefab base."""
        self.overrides.pop(key, None)

    def apply(self, obj_data: dict[str, Any]) -> dict[str, Any]:
        """Aplica os overrides registrados sobre uma cópia do objeto serializado."""
        result = deepcopy(obj_data)
        for key, value in self.overrides.items():
            parts = key.split(".")
            cursor: Any = result
            for part in parts[:-1]:
                if isinstance(cursor, dict):
                    cursor = cursor.setdefault(part, {})
                else:
                    break
            else:
                if isinstance(cursor, dict):
                    cursor[parts[-1]] = deepcopy(value)
        return result


def diff_from_prefab(current: dict[str, Any], base: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Gera um dicionário de overrides comparando a instância atual com o prefab base.
    
    Compara superficialmente as chaves de primeiro nível (transform, components, visual).
    Retorna somente os campos que diferem.
    """
    diffs: dict[str, Any] = {}
    for key, val in current.items():
        full_key = f"{prefix}{key}" if prefix else key
        base_val = base.get(key)
        if isinstance(val, dict) and isinstance(base_val, dict):
            nested = diff_from_prefab(val, base_val, f"{full_key}.")
            diffs.update(nested)
        elif val != base_val:
            diffs[full_key] = deepcopy(val)
    return diffs


# ── Serialização / Desserialização ──────────────────────────────────────────

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


def unpack_prefab(obj: GameObject) -> None:
    """Desvincula o GameObject de seu prefab de origem.
    
    Após chamar esta função, o objeto mantém todos os seus valores atuais mas
    não terá mais a relação com o prefab. O badge 🔷 na Hierarchy desaparece.
    """
    obj.prefab_uuid = None
    if hasattr(obj, "prefab_source"):
        obj.prefab_source = None
    if hasattr(obj, "_prefab_overrides"):
        obj._prefab_overrides = None

