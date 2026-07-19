"""Demand-driven frame invalidation and lightweight render metrics."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameInvalidationStats:
    requested: int
    coalesced: int
    rendered: int
    idle_ticks: int


class FrameInvalidation:
    """Coalesce repaint requests until the pending frame is consumed."""

    def __init__(self) -> None:
        self._dirty = False
        self._reasons: set[str] = set()
        self._requested = 0
        self._coalesced = 0
        self._rendered = 0
        self._idle_ticks = 0

    @property
    def dirty(self) -> bool:
        return self._dirty

    def invalidate(self, reason: str = "unspecified") -> bool:
        """Return True only when the caller must schedule a new repaint."""
        self._requested += 1
        self._reasons.add(str(reason))
        if self._dirty:
            self._coalesced += 1
            return False
        self._dirty = True
        return True

    def consume(self) -> frozenset[str]:
        reasons = frozenset(self._reasons)
        self._dirty = False
        self._reasons.clear()
        self._rendered += 1
        return reasons

    def record_idle_tick(self) -> None:
        self._idle_ticks += 1

    def snapshot(self) -> FrameInvalidationStats:
        return FrameInvalidationStats(
            requested=self._requested,
            coalesced=self._coalesced,
            rendered=self._rendered,
            idle_ticks=self._idle_ticks,
        )
