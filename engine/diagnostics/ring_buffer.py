"""Bounded in-memory log handler used to give crash reports recent context.

Phase 9.5B Stage 0.  Deliberately tiny and allocation-light: it stores already
formatted strings in a :class:`collections.deque` with a hard ``maxlen``, so it
cannot grow without bound no matter how long a session runs.
"""
from __future__ import annotations

import logging
import threading
from collections import deque

DEFAULT_CAPACITY = 200


class RingBufferHandler(logging.Handler):
    """Keeps the last ``capacity`` formatted log records in memory."""

    def __init__(self, capacity: int = DEFAULT_CAPACITY) -> None:
        super().__init__()
        self.capacity = max(1, int(capacity))
        self._records: deque[str] = deque(maxlen=self.capacity)
        self._lock_records = threading.Lock()

    # ``logging`` calls this for every record that passes the level filter.
    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
        except Exception:
            # A formatting failure must never take down the emitting thread.
            try:
                line = f"<unformattable {record.levelname} record from {record.name}>"
            except Exception:
                return
        with self._lock_records:
            self._records.append(line)

    def snapshot(self, limit: int | None = None) -> list[str]:
        """Return the buffered lines, oldest first."""
        with self._lock_records:
            lines = list(self._records)
        if limit is not None and limit >= 0:
            return lines[-limit:]
        return lines

    def clear(self) -> None:
        with self._lock_records:
            self._records.clear()

    def __len__(self) -> int:
        with self._lock_records:
            return len(self._records)
