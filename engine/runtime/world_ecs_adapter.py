"""Ponte explícita entre o modelo leve do Play Mode e o ECS oficial."""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping

from engine.game_object import GameObject


class RuntimeWorldECSAdapter:
    """Converte identidade e Transform sem esconder os formatos incompatíveis."""

    @staticmethod
    def to_game_object(runtime_object: Mapping[str, Any]) -> GameObject:
        game_object = GameObject(
            str(runtime_object.get("name", "GameObject")),
            str(runtime_object.get("tag", "Untagged")),
        )
        game_object.active = bool(runtime_object.get("active", True))
        game_object.mesh_type = str(runtime_object.get("mesh_type", "Sprite"))
        game_object.transform.position = [
            float(runtime_object.get("x", 0.0)),
            float(runtime_object.get("y", 0.0)),
            float(runtime_object.get("z", 0.0)),
        ]
        game_object.transform.rotation = [0.0, 0.0, float(runtime_object.get("rotation", 0.0))]
        game_object.transform.scale = [
            float(runtime_object.get("w", 1.0)),
            float(runtime_object.get("h", 1.0)),
            1.0,
        ]
        return game_object

    @staticmethod
    def update_runtime_object(game_object: GameObject, runtime_object: MutableMapping[str, Any]) -> None:
        runtime_object.update({
            "name": game_object.name,
            "tag": game_object.tag,
            "active": game_object.active,
            "mesh_type": game_object.mesh_type or runtime_object.get("mesh_type", "Sprite"),
            "x": game_object.transform.x,
            "y": game_object.transform.y,
            "z": game_object.transform.z,
            "rotation": game_object.transform.rz,
            "w": abs(game_object.transform.sx),
            "h": abs(game_object.transform.sy),
        })

