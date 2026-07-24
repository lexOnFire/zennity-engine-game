"""Scene serialization public API."""

from engine.scene.scene_format import ENGINE_VERSION, SCENE_FORMAT_VERSION
from engine.scene.scene_loader import load_scene, load_scene_document
from engine.scene.scene_document import SceneDocument
from engine.scene.scene_serializer import (
    deserialize_game_object,
    deserialize_scene,
    save_scene,
    serialize_game_object,
    serialize_scene,
)

__all__ = [
    "SceneDocument",
    "ENGINE_VERSION",
    "SCENE_FORMAT_VERSION",
    "deserialize_game_object",
    "deserialize_scene",
    "load_scene",
    "load_scene_document",
    "save_scene",
    "serialize_game_object",
    "serialize_scene",
]
