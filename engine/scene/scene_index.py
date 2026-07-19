"""Índice de leitura da cena por UUID, nome e tag."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


class SceneIndex:
    def __init__(self) -> None:
        self._by_id: dict[str, Any] = {}
        self._by_name: dict[str, Any] = {}
        self._by_tag: dict[str, list[Any]] = defaultdict(list)

    def rebuild(self, roots: Iterable[Any]) -> None:
        self.clear()
        for root in roots:
            self.add(root)

    def add(self, obj: Any) -> None:
        object_id = str(getattr(obj, "id", ""))
        name = str(getattr(obj, "name", ""))
        tag = str(getattr(obj, "tag", "Untagged"))
        if object_id:
            existing = self._by_id.get(object_id)
            if existing is not None and existing is not obj:
                raise ValueError(f"UUID duplicado na cena: {object_id}")
            self._by_id[object_id] = obj
        if name:
            self._by_name.setdefault(name, obj)
        if obj not in self._by_tag[tag]:
            self._by_tag[tag].append(obj)
        for child in getattr(obj, "children", ()):
            self.add(child)

    def remove(self, obj: Any) -> None:
        for child in tuple(getattr(obj, "children", ())):
            self.remove(child)
        self._by_id.pop(str(getattr(obj, "id", "")), None)
        name = str(getattr(obj, "name", ""))
        if self._by_name.get(name) is obj:
            self._by_name.pop(name, None)
        tag = str(getattr(obj, "tag", "Untagged"))
        tagged = self._by_tag.get(tag, [])
        if obj in tagged:
            tagged.remove(obj)
        if not tagged:
            self._by_tag.pop(tag, None)

    def by_id(self, object_id: str) -> Any | None:
        value = str(object_id)
        exact = self._by_id.get(value)
        if exact is not None:
            return exact
        if len(value) == 8:
            return next((obj for key, obj in self._by_id.items() if key.startswith(value)), None)
        return None

    def by_name(self, name: str) -> Any | None:
        result = self._by_name.get(str(name))
        return result if result is not None and str(getattr(result, "name", "")) == str(name) else None

    def by_tag(self, tag: str) -> list[Any]:
        return [obj for obj in self._by_tag.get(str(tag), ()) if str(getattr(obj, "tag", "")) == str(tag)]

    def clear(self) -> None:
        self._by_id.clear()
        self._by_name.clear()
        self._by_tag.clear()
