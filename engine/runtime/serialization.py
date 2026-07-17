"""engine/runtime/serialization.py
─────────────────────────────────────────────────────────────
Centraliza a serialização e desserialização de cenas e prefabs.

Schema versão 1 (v1):
  Scene:
    {
      "__schema__": "zennity-scene",
      "version": 1,
      "name": str,
      "objects": [ <game_object_data>, ... ]
    }

  GameObjectData:
    {
      "id": str (UUID4),
      "name": str,
      "tag": str,
      "active": bool,
      "layer": int,
      "transform": { "position": [x,y,z], "rotation": [x,y,z], "scale": [x,y,z] },
      "components": [ <component_data>, ... ],
      "children": [ <game_object_data>, ... ]
    }

  ComponentData: dicionário retornado por component.serialize()
    Deve conter ao menos "type" com o nome registrado no ComponentRegistry.

Uso:
    from engine.runtime.serialization import SceneSerializer

    data = SceneSerializer.serialize(editor_scene)
    scene = SceneSerializer.deserialize(data, scene_class=EditorScene)
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import numpy as np

from engine.core.component_registry import component_registry
from engine.game_object import GameObject

_SCHEMA_SCENE = "zennity-scene"
_SCHEMA_PREFAB = "zennity-prefab"
_CURRENT_VERSION = 1


class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        return super().default(obj)


# ---------------------------------------------------------------------------
# Serialização de GameObjects
# ---------------------------------------------------------------------------

def _serialize_go(go: GameObject) -> dict[str, Any]:
    """Serializa um GameObject e toda sua árvore de filhos."""
    transform = go.transform
    data: dict[str, Any] = {
        "id": str(go.id),
        "name": str(go.name),
        "tag": str(go.tag),
        "active": bool(go.active),
        "layer": int(getattr(go, "layer", 0)),
        "transform": {
            "position": np.array(transform.position, dtype=float).tolist(),
            "rotation": np.array(transform.rotation, dtype=float).tolist(),
            "scale": np.array(transform.scale, dtype=float).tolist(),
        },
        "components": [],
        "children": [],
    }

    # Campos opcionais que podem existir no GameObject do editor
    for attr in (
        "mesh_type",
        "sprite_path",
        "asset_uuid",
        "material",
        "prefab_uuid",
        "scripts",
        "script_path",
    ):
        val = getattr(go, attr, None)
        if val is not None:
            if isinstance(val, np.ndarray):
                val = val.tolist()
            data[attr] = val

    # Componentes (Transform serializado via transform block, skip aqui)
    from engine.core.component import Transform
    for comp in getattr(go, "components", []):
        if isinstance(comp, Transform) or comp is go.transform:
            continue
        if hasattr(comp, "serialize"):
            try:
                comp_data = comp.serialize()
                if comp_data:
                    data["components"].append(comp_data)
            except Exception as exc:
                warnings.warn(
                    f"[SceneSerializer] serialize() falhou em "
                    f"{type(comp).__name__}: {exc}. Componente ignorado.",
                    RuntimeWarning,
                    stacklevel=2,
                )

    # Filhos recursivos
    for child in getattr(go, "children", []):
        data["children"].append(_serialize_go(child))

    return data


def _deserialize_go(data: dict[str, Any]) -> GameObject:
    """Reconstrói um GameObject a partir de dados serializados."""
    go = GameObject(
        name=str(data.get("name", "GameObject")),
        tag=str(data.get("tag", "Untagged")),
    )
    # Restaura ID original para manter referências cruzadas válidas
    if "id" in data:
        go._id = str(data["id"])

    go.active = bool(data.get("active", True))
    if "layer" in data:
        go.layer = int(data["layer"])

    # Transform
    t = data.get("transform", {})
    if "position" in t:
        go.transform.position = np.array(t["position"], dtype=np.float32)
    if "rotation" in t:
        go.transform.rotation = np.array(t["rotation"], dtype=np.float32)
    if "scale" in t:
        go.transform.scale = np.array(t["scale"], dtype=np.float32)

    # Campos opcionais
    for attr in (
        "mesh_type",
        "sprite_path",
        "asset_uuid",
        "material",
        "prefab_uuid",
        "scripts",
        "script_path",
    ):
        if attr in data:
            setattr(go, attr, data[attr])

    # Componentes
    for comp_data in data.get("components", []):
        try:
            comp = component_registry.create(comp_data)
            if comp is not None:
                go.add_component(comp)
        except Exception as exc:
            warnings.warn(
                f"[SceneSerializer] Falha ao criar componente {comp_data.get('type', '?')}: {exc}. "
                "Componente ignorado.",
                RuntimeWarning,
                stacklevel=2,
            )

    # Filhos
    for child_data in data.get("children", []):
        go.add_child(_deserialize_go(child_data))

    return go


# ---------------------------------------------------------------------------
# SceneSerializer — API pública
# ---------------------------------------------------------------------------

class SceneSerializer:
    """Serializa e desserializa cenas completas."""

    @staticmethod
    def serialize(scene: Any) -> dict[str, Any]:
        """Serializa uma cena para um dicionário JSON-compatível."""
        objs = getattr(scene, "editable_objects", None)
        if objs is None:
            objs = getattr(scene, "game_objects", [])
        return {
            "__schema__": _SCHEMA_SCENE,
            "version": _CURRENT_VERSION,
            "name": str(getattr(scene, "name", "Scene")),
            "objects": [_serialize_go(go) for go in list(objs)],
        }

    @staticmethod
    def serialize_to_json(scene: Any, indent: int = 2) -> str:
        return json.dumps(
            SceneSerializer.serialize(scene),
            cls=_NumpyEncoder,
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def deserialize(data: dict[str, Any], scene_class: type | None = None) -> Any:
        """Reconstrói uma cena a partir de dados serializados.

        Args:
            data: dicionário gerado por SceneSerializer.serialize()
            scene_class: classe da cena a ser instanciada. Se None, usa
                         engine.core.Scene base.
        """
        _validate_schema(data, _SCHEMA_SCENE)
        from engine.core.scene import Scene
        klass = scene_class or Scene
        scene = klass.__new__(klass)
        klass.__init__(scene)
        scene.name = str(data.get("name", "Scene"))
        for go_data in data.get("objects", []):
            go = _deserialize_go(go_data)
            if hasattr(scene, "_add_go"):
                scene._add_go(go)
            elif hasattr(scene, "add_game_object"):
                scene.add_game_object(go)
            else:
                scene.game_objects.append(go)
                go.scene = scene
        return scene

    @staticmethod
    def deserialize_from_json(
        json_str: str, scene_class: type | None = None
    ) -> Any:
        data = json.loads(json_str)
        return SceneSerializer.deserialize(data, scene_class)

    @staticmethod
    def save_to_file(scene: Any, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            SceneSerializer.serialize_to_json(scene), encoding="utf-8"
        )

    @staticmethod
    def load_from_file(
        path: str | Path, scene_class: type | None = None
    ) -> Any:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de cena não encontrado: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return SceneSerializer.deserialize(data, scene_class)


# ---------------------------------------------------------------------------
# PrefabSerializer — API pública
# ---------------------------------------------------------------------------

class PrefabSerializer:
    """Serializa e desserializa prefabs (um único GameObject + filhos)."""

    @staticmethod
    def serialize(go: GameObject) -> dict[str, Any]:
        return {
            "__schema__": _SCHEMA_PREFAB,
            "version": _CURRENT_VERSION,
            "root": _serialize_go(go),
        }

    @staticmethod
    def serialize_to_json(go: GameObject, indent: int = 2) -> str:
        return json.dumps(
            PrefabSerializer.serialize(go),
            cls=_NumpyEncoder,
            indent=indent,
            ensure_ascii=False,
        )

    @staticmethod
    def deserialize(data: dict[str, Any]) -> GameObject:
        _validate_schema(data, _SCHEMA_PREFAB)
        return _deserialize_go(data["root"])

    @staticmethod
    def deserialize_from_json(json_str: str) -> GameObject:
        return PrefabSerializer.deserialize(json.loads(json_str))

    @staticmethod
    def save_to_file(go: GameObject, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            PrefabSerializer.serialize_to_json(go), encoding="utf-8"
        )

    @staticmethod
    def load_from_file(path: str | Path) -> GameObject:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Prefab não encontrado: {path}")
        return PrefabSerializer.deserialize(
            json.loads(path.read_text(encoding="utf-8"))
        )


# ---------------------------------------------------------------------------
# Validação de schema
# ---------------------------------------------------------------------------

def _validate_schema(data: dict[str, Any], expected_schema: str) -> None:
    schema = data.get("__schema__")
    if schema != expected_schema:
        raise ValueError(
            f"Schema inválido: esperado '{expected_schema}', encontrado '{schema}'."
        )
    version = data.get("version", 0)
    if version > _CURRENT_VERSION:
        warnings.warn(
            f"[Serialization] Versão do arquivo ({version}) é mais nova que a "
            f"engine ({_CURRENT_VERSION}). Alguns dados podem ser ignorados.",
            UserWarning,
            stacklevel=3,
        )
