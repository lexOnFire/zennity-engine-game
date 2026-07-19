"""Modelo canônico e tipado do documento editável de uma cena.

O documento não executa componentes. Ele representa exclusivamente o estado
editável/serializável e fornece índices estáveis sem expor as estruturas
internas mutáveis à interface.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping
import uuid


@dataclass(slots=True)
class SceneDocument:
    scene_name: str = "Untitled"
    format_version: int = 2
    engine_version: str = "Zennity 0.1.0"
    objects: list[dict[str, Any]] = field(default_factory=list)
    blackboard: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)
    _by_id: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)
    _by_name: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.replace_objects(self.objects)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SceneDocument":
        known = {"format_version", "scene_name", "engine_version", "objects", "blackboard"}
        return cls(
            scene_name=str(payload.get("scene_name", "Untitled")),
            format_version=max(1, int(payload.get("format_version", 1))),
            engine_version=str(payload.get("engine_version", "Zennity 0.1.0")),
            objects=deepcopy(list(payload.get("objects", []))),
            blackboard=deepcopy(dict(payload.get("blackboard", {}))),
            extra={key: deepcopy(value) for key, value in payload.items() if key not in known},
        )

    def to_mapping(self) -> dict[str, Any]:
        payload = deepcopy(self.extra)
        payload.update({
            "format_version": int(self.format_version),
            "scene_name": self.scene_name,
            "engine_version": self.engine_version,
            "objects": deepcopy(self.objects),
        })
        if self.blackboard:
            payload["blackboard"] = deepcopy(self.blackboard)
        return payload

    def replace_objects(self, objects: Iterable[Mapping[str, Any]]) -> None:
        normalized: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_names: set[str] = set()
        for raw in objects:
            item = deepcopy(dict(raw))
            object_id = str(item.get("id") or uuid.uuid4())
            name = str(item.get("name") or "GameObject").strip() or "GameObject"
            if object_id in seen_ids:
                raise ValueError(f"ID de objeto duplicado: {object_id}")
            if name in seen_names:
                raise ValueError(f"Nome de objeto duplicado: {name}")
            item["id"] = object_id
            item["name"] = name
            seen_ids.add(object_id)
            seen_names.add(name)
            normalized.append(item)
        self.objects = normalized
        self._rebuild_indexes()

    def snapshot(self) -> list[dict[str, Any]]:
        return deepcopy(self.objects)

    def find_by_id(self, object_id: str) -> dict[str, Any] | None:
        return self._by_id.get(str(object_id))

    def find_by_name(self, name: str) -> dict[str, Any] | None:
        return self._by_name.get(str(name))

    def add(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        candidate = deepcopy(dict(raw))
        candidate.setdefault("id", str(uuid.uuid4()))
        candidate.setdefault("name", "GameObject")
        self.replace_objects([*self.objects, candidate])
        return self._by_id[str(candidate["id"])]

    def remove(self, object_id: str) -> dict[str, Any] | None:
        existing = self.find_by_id(object_id)
        if existing is None:
            return None
        removed = deepcopy(existing)
        self.replace_objects(item for item in self.objects if str(item["id"]) != str(object_id))
        return removed

    def rename(self, object_id: str, new_name: str) -> None:
        normalized = str(new_name).strip()
        if not normalized:
            raise ValueError("Nome do objeto não pode ser vazio")
        existing = self.find_by_name(normalized)
        if existing is not None and str(existing["id"]) != str(object_id):
            raise ValueError(f"Nome de objeto duplicado: {normalized}")
        target = self.find_by_id(object_id)
        if target is None:
            raise KeyError(object_id)
        target["name"] = normalized
        self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        self._by_id = {str(item["id"]): item for item in self.objects}
        self._by_name = {str(item["name"]): item for item in self.objects}
