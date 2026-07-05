from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.scene.scene_serializer import deserialize_scene


def load_scene(path: str | Path) -> dict[str, Any]:
    """Load a .zscene file and return a scene data model."""
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(".zscene root must be a JSON object")
    return deserialize_scene(data)
