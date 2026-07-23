from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.scene.scene_serializer import deserialize_scene
from engine.scene.scene_document import SceneDocument


def load_scene_document(path: str | Path) -> SceneDocument:
    """Load the canonical lossless representation of a ``.zscene`` file."""
    return SceneDocument.load(path)


def load_scene(path: str | Path) -> dict[str, Any]:
    """Load a .zscene file and return a scene data model."""
    return deserialize_scene(load_scene_document(path).to_dict())
