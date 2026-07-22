"""Repeatable allocation measurements for lifecycle and release gates."""
from __future__ import annotations

import gc
import tracemalloc
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class MemoryMeasurement:
    iterations: int
    retained_bytes: int
    retained_blocks: int
    peak_bytes: int

    def assert_within(self, *, retained_bytes: int, peak_bytes: int) -> None:
        if self.retained_bytes > retained_bytes or self.peak_bytes > peak_bytes:
            raise AssertionError(
                "memory budget exceeded: "
                f"retained={self.retained_bytes}/{retained_bytes} bytes, "
                f"peak={self.peak_bytes}/{peak_bytes} bytes"
            )


def measure_allocations(
    operation: Callable[[], None],
    *,
    iterations: int,
    warmup: int = 10,
) -> MemoryMeasurement:
    """Measure net retained memory after repeated, warmed-up operations."""
    count = max(1, int(iterations))
    for _ in range(max(0, int(warmup))):
        operation()
    gc.collect()

    started_here = not tracemalloc.is_tracing()
    if started_here:
        tracemalloc.start()
    tracemalloc.reset_peak()
    before_current, _ = tracemalloc.get_traced_memory()
    before = tracemalloc.take_snapshot()

    for _ in range(count):
        operation()
    gc.collect()

    after = tracemalloc.take_snapshot()
    current, peak = tracemalloc.get_traced_memory()
    changes = after.compare_to(before, "lineno")
    measurement = MemoryMeasurement(
        iterations=count,
        retained_bytes=max(0, sum(item.size_diff for item in changes)),
        retained_blocks=max(0, sum(item.count_diff for item in changes)),
        peak_bytes=max(0, peak - before_current),
    )
    if started_here:
        tracemalloc.stop()
    return measurement
