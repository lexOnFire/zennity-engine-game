"""Bounded command ingestion for the isolated viewport process."""
from __future__ import annotations

from queue import Empty
from typing import Any, Iterator


class ViewportCommandQueue:
    """Drains IPC commands without allowing producers to starve a frame."""

    def __init__(self, source: Any, *, maximum_per_frame: int = 256) -> None:
        self._source = source
        self.maximum_per_frame = max(1, int(maximum_per_frame))

    def drain(self) -> Iterator[dict[str, Any]]:
        if self._source is None:
            return
        for _ in range(self.maximum_per_frame):
            try:
                command = self._source.get_nowait()
            except Empty:
                return
            if isinstance(command, dict):
                yield command
