"""Bounded command ingestion for the isolated viewport process."""
from __future__ import annotations

from collections import deque
from queue import Empty
from typing import Any, Iterator


class ViewportCommandQueue:
    """Drains IPC commands without allowing producers to starve a frame."""

    PRIORITY_TYPES = frozenset({"shutdown", "scene_snapshot", "play", "stop", "pause"})

    def __init__(self, source: Any, *, maximum_per_frame: int = 256, priority_scan_limit: int = 4096) -> None:
        self._source = source
        self.maximum_per_frame = max(1, int(maximum_per_frame))
        self.priority_scan_limit = max(self.maximum_per_frame, int(priority_scan_limit))
        self._deferred: deque[dict[str, Any]] = deque()

    def drain(self) -> Iterator[dict[str, Any]]:
        if self._source is None:
            return
        yielded = 0
        while self._deferred and yielded < self.maximum_per_frame:
            yielded += 1
            yield self._deferred.popleft()
        if yielded >= self.maximum_per_frame:
            return

        scanned: list[dict[str, Any]] = []
        for _ in range(self.priority_scan_limit):
            try:
                command = self._source.get_nowait()
            except Empty:
                break
            if isinstance(command, dict):
                scanned.append(command)

        priority = [command for command in scanned if str(command.get("type", "")) in self.PRIORITY_TYPES]
        normal = [command for command in scanned if str(command.get("type", "")) not in self.PRIORITY_TYPES]
        for command in priority + normal:
            if yielded < self.maximum_per_frame:
                yielded += 1
                yield command
            else:
                self._deferred.append(command)
