"""Versioned, deterministic performance contracts for release gates."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PerformanceWindow:
    """Aggregate metrics from a representative warmed-up frame window."""

    p95_frame_time_ms: float
    maximum_frame_time_ms: float
    p95_draw_calls: int
    repaints_per_frame: float
    invalidations_per_frame: float
    cache_hits: int
    cache_misses: int

    @property
    def cache_hit_ratio(self) -> float:
        total = max(0, self.cache_hits) + max(0, self.cache_misses)
        return 1.0 if total == 0 else max(0, self.cache_hits) / total


@dataclass(frozen=True)
class PerformanceBudget:
    name: str
    p95_frame_time_ms: float
    maximum_frame_time_ms: float
    p95_draw_calls: int
    repaints_per_frame: float
    invalidations_per_frame: float
    minimum_cache_hit_ratio: float

    def violations(self, sample: PerformanceWindow) -> tuple[str, ...]:
        checks = (
            ("p95_frame_time_ms", sample.p95_frame_time_ms, self.p95_frame_time_ms, "<="),
            ("maximum_frame_time_ms", sample.maximum_frame_time_ms, self.maximum_frame_time_ms, "<="),
            ("p95_draw_calls", sample.p95_draw_calls, self.p95_draw_calls, "<="),
            ("repaints_per_frame", sample.repaints_per_frame, self.repaints_per_frame, "<="),
            ("invalidations_per_frame", sample.invalidations_per_frame, self.invalidations_per_frame, "<="),
            ("cache_hit_ratio", sample.cache_hit_ratio, self.minimum_cache_hit_ratio, ">="),
        )
        return tuple(
            f"{name}: {actual:.3f} must be {operator} {limit:.3f}"
            for name, actual, limit, operator in checks
            if (actual > limit if operator == "<=" else actual < limit)
        )

    def assert_within(self, sample: PerformanceWindow) -> None:
        violations = self.violations(sample)
        if violations:
            raise AssertionError(f"{self.name} performance budget exceeded: " + "; ".join(violations))


RUNTIME_BUDGET = PerformanceBudget(
    name="runtime-60fps-v1",
    p95_frame_time_ms=16.67,
    maximum_frame_time_ms=33.33,
    p95_draw_calls=1000,
    repaints_per_frame=1.0,
    invalidations_per_frame=32.0,
    minimum_cache_hit_ratio=0.90,
)

EDITOR_BUDGET = PerformanceBudget(
    name="editor-interactive-v1",
    p95_frame_time_ms=20.0,
    maximum_frame_time_ms=50.0,
    p95_draw_calls=1500,
    repaints_per_frame=1.0,
    invalidations_per_frame=64.0,
    minimum_cache_hit_ratio=0.85,
)
