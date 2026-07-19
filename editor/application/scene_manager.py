"""Scene document ownership and lookup operations for the editor."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable


SceneObject = dict[str, Any]


class SceneManager:
    """Own the editable scene snapshot without depending on Qt or Pygame.

    The manager returns defensive copies at process/UI boundaries. Internal
    mutation remains explicit so a future Command system can become the only
    writer without changing scene serialization again.
    """

    def __init__(self, initial_objects: Iterable[SceneObject] = ()) -> None:
        self._initial_objects = deepcopy(list(initial_objects))
        self._objects: list[SceneObject] = []
        self._objects_by_name: dict[str, SceneObject] = {}
        self.replace(self._initial_objects)

    @property
    def objects(self) -> list[SceneObject]:
        return self._objects

    @property
    def objects_by_name(self) -> dict[str, SceneObject]:
        return self._objects_by_name

    def snapshot(self) -> list[SceneObject]:
        return deepcopy(self._objects)

    def replace(self, objects: Iterable[SceneObject]) -> None:
        candidate = deepcopy(list(objects))
        index: dict[str, SceneObject] = {}
        for item in candidate:
            name = str(item.get("name", "")).strip()
            if not name:
                raise ValueError("Scene objects must have a non-empty name")
            if name in index:
                raise ValueError(f"Duplicate scene object name: {name}")
            item["name"] = name
            index[name] = item
        self._objects = candidate
        self._objects_by_name = index

    def reset(self) -> None:
        self.replace(self._initial_objects)

    def find(self, name: str | None) -> SceneObject | None:
        if name is None:
            return None
        return self._objects_by_name.get(str(name))

    def contains(self, name: str) -> bool:
        return str(name) in self._objects_by_name

    def add(self, scene_object: SceneObject) -> SceneObject:
        item = deepcopy(scene_object)
        name = str(item.get("name", "")).strip()
        if not name:
            raise ValueError("Scene objects must have a non-empty name")
        if name in self._objects_by_name:
            raise ValueError(f"Duplicate scene object name: {name}")
        item["name"] = name
        self._objects.append(item)
        self._objects_by_name[name] = item
        return item

    def remove(self, name: str) -> SceneObject | None:
        normalized = str(name)
        item = self._objects_by_name.pop(normalized, None)
        if item is None:
            return None
        self._objects.remove(item)
        return item

    def rename(self, old_name: str, new_name: str) -> SceneObject:
        normalized_old = str(old_name)
        normalized_new = str(new_name).strip()
        if not normalized_new:
            raise ValueError("Scene objects must have a non-empty name")
        item = self._objects_by_name.get(normalized_old)
        if item is None:
            raise KeyError(normalized_old)
        if normalized_new != normalized_old and normalized_new in self._objects_by_name:
            raise ValueError(f"Duplicate scene object name: {normalized_new}")
        del self._objects_by_name[normalized_old]
        item["name"] = normalized_new
        self._objects_by_name[normalized_new] = item
        return item
