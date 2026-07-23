"""Incremental, memory-bounded undo/redo history for scene dictionaries."""
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


def _object_key(item: dict[str, Any]) -> str:
    return str(item.get("id") or item.get("name"))


@dataclass(frozen=True)
class SceneDelta:
    before: dict[str, dict[str, Any] | None]
    after: dict[str, dict[str, Any] | None]
    before_order: tuple[str, ...]
    after_order: tuple[str, ...]
    size_bytes: int

    @property
    def changed_objects(self) -> int:
        return len(self.before)


@dataclass(frozen=True)
class SceneHistoryStats:
    undo_entries: int
    redo_entries: int
    retained_bytes: int
    evicted_entries: int
    changed_objects: int


class SceneHistory:
    """Store object-level deltas instead of complete scene snapshots."""

    def __init__(self, max_commands: int = 100, max_bytes: int = 16 * 1024 * 1024) -> None:
        self.max_commands = max(1, int(max_commands))
        self.max_bytes = max(1, int(max_bytes))
        self._undo: list[SceneDelta] = []
        self._redo: list[SceneDelta] = []
        self._pending_before: list[dict[str, Any]] | None = None
        self._retained_bytes = 0
        self._evicted_entries = 0

    def begin(self, current: list[dict[str, Any]]) -> None:
        """Finalize the previous edit and capture the state before a new one."""
        self._clear_redo()
        self._finalize_pending(current)
        self._pending_before = deepcopy(current)

    def commit(self, before: list[dict[str, Any]], after: list[dict[str, Any]]) -> bool:
        """Record an already completed edit, such as a viewport drag."""
        self._clear_redo()
        self._finalize_pending(before)
        delta = self._create_delta(before, after)
        self._pending_before = None
        if delta is None:
            return False
        self._push_undo(delta)
        return True

    def undo(self, current: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        self._finalize_pending(current)
        if not self._undo:
            return None
        delta = self._undo.pop()
        self._retained_bytes -= delta.size_bytes
        self._redo.append(delta)
        self._retained_bytes += delta.size_bytes
        return self._apply(current, delta.before, delta.before_order)

    def redo(self, current: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        if not self._redo:
            return None
        delta = self._redo.pop()
        self._retained_bytes -= delta.size_bytes
        self._undo.append(delta)
        self._retained_bytes += delta.size_bytes
        return self._apply(current, delta.after, delta.after_order)

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._pending_before = None
        self._retained_bytes = 0

    def snapshot(self) -> SceneHistoryStats:
        entries = self._undo + self._redo
        return SceneHistoryStats(
            undo_entries=len(self._undo),
            redo_entries=len(self._redo),
            retained_bytes=self._retained_bytes,
            evicted_entries=self._evicted_entries,
            changed_objects=sum(delta.changed_objects for delta in entries),
        )

    def _finalize_pending(self, current: list[dict[str, Any]]) -> None:
        if self._pending_before is None:
            return
        delta = self._create_delta(self._pending_before, current)
        self._pending_before = None
        if delta is not None:
            self._push_undo(delta)

    def _push_undo(self, delta: SceneDelta) -> None:
        self._undo.append(delta)
        self._retained_bytes += delta.size_bytes
        while len(self._undo) > self.max_commands or self._retained_bytes > self.max_bytes:
            removed = self._undo.pop(0)
            self._retained_bytes -= removed.size_bytes
            self._evicted_entries += 1

    def _clear_redo(self) -> None:
        self._retained_bytes -= sum(delta.size_bytes for delta in self._redo)
        self._redo.clear()

    @staticmethod
    def _create_delta(
        before: list[dict[str, Any]], after: list[dict[str, Any]]
    ) -> SceneDelta | None:
        before_map = {_object_key(item): item for item in before}
        after_map = {_object_key(item): item for item in after}
        changed = {
            key for key in before_map.keys() | after_map.keys()
            if before_map.get(key) != after_map.get(key)
        }
        before_order = tuple(_object_key(item) for item in before)
        after_order = tuple(_object_key(item) for item in after)
        if not changed and before_order == after_order:
            return None
        old_values = {key: deepcopy(before_map.get(key)) for key in changed}
        new_values = {key: deepcopy(after_map.get(key)) for key in changed}
        encoded = json.dumps(
            [old_values, new_values, before_order, after_order],
            default=str,
            separators=(",", ":"),
        ).encode("utf-8")
        return SceneDelta(old_values, new_values, before_order, after_order, len(encoded))

    @staticmethod
    def _apply(
        current: list[dict[str, Any]],
        changes: dict[str, dict[str, Any] | None],
        order: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        result = {_object_key(item): item for item in current}
        for key, value in changes.items():
            if value is None:
                result.pop(key, None)
            else:
                result[key] = deepcopy(value)
        return [result[key] for key in order if key in result]
