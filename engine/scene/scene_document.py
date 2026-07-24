"""Lossless document boundary for Zennity ``.zscene`` files.

The document deliberately preserves fields it does not understand.  Typed
runtime objects are built by adapters; this class owns the persisted payload
and prevents older engine versions from erasing newer editor data.
"""
from __future__ import annotations

import json
import shutil
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from engine.scene.scene_format import (
    DEFAULT_SCENE_NAME,
    ENGINE_VERSION,
    SCENE_FORMAT_VERSION,
)


@dataclass(frozen=True, slots=True)
class SceneDocument:
    """Immutable, lossless wrapper around one scene payload."""

    _payload: dict[str, Any]

    @classmethod
    def empty(cls, name: str = DEFAULT_SCENE_NAME) -> "SceneDocument":
        return cls.from_dict(
            {
                "format_version": SCENE_FORMAT_VERSION,
                "scene_name": str(name),
                "engine_version": ENGINE_VERSION,
                "objects": [],
            }
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SceneDocument":
        if not isinstance(payload, Mapping):
            raise TypeError("scene payload must be a mapping")

        copied = deepcopy(dict(payload))
        objects = copied.get("objects", [])
        if not isinstance(objects, list):
            raise ValueError("scene field 'objects' must be a list")
        if any(not isinstance(item, dict) for item in objects):
            raise ValueError("every scene object must be a mapping")

        copied.setdefault("format_version", SCENE_FORMAT_VERSION)
        copied.setdefault("scene_name", DEFAULT_SCENE_NAME)
        copied.setdefault("engine_version", ENGINE_VERSION)
        copied["objects"] = objects
        return cls(copied)

    @classmethod
    def from_json(cls, source: str) -> "SceneDocument":
        payload = json.loads(source)
        if not isinstance(payload, dict):
            raise ValueError("scene JSON root must be an object")
        return cls.from_dict(payload)

    @classmethod
    def load(cls, path: str | Path) -> "SceneDocument":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    @property
    def format_version(self) -> int:
        return int(self._payload["format_version"])

    @property
    def scene_name(self) -> str:
        return str(self._payload["scene_name"])

    @property
    def engine_version(self) -> str:
        return str(self._payload["engine_version"])

    @property
    def objects(self) -> tuple[dict[str, Any], ...]:
        return tuple(deepcopy(self._payload["objects"]))

    def to_dict(self) -> dict[str, Any]:
        """Return a detached payload, including every unknown field."""
        return deepcopy(self._payload)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(
            self._payload,
            indent=indent,
            ensure_ascii=False,
        )

    def save(self, path: str | Path, *, keep_backup: bool = True) -> Path:
        """Atomically persist the document and optionally retain one backup."""
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(self.to_json() + "\n", encoding="utf-8")
        if keep_backup and output.is_file():
            shutil.copy2(output, output.with_suffix(output.suffix + ".bak"))
        temporary.replace(output)
        return output
