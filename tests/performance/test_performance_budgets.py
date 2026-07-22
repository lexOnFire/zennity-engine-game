from __future__ import annotations

import pytest

from engine.performance import EDITOR_BUDGET, RUNTIME_BUDGET, PerformanceWindow


def _sample(**overrides) -> PerformanceWindow:
    values = {
        "p95_frame_time_ms": 15.0,
        "maximum_frame_time_ms": 25.0,
        "p95_draw_calls": 500,
        "repaints_per_frame": 1.0,
        "invalidations_per_frame": 10.0,
        "cache_hits": 95,
        "cache_misses": 5,
    }
    values.update(overrides)
    return PerformanceWindow(**values)


def test_runtime_budget_accepts_warmed_up_60fps_window() -> None:
    assert RUNTIME_BUDGET.violations(_sample()) == ()
    RUNTIME_BUDGET.assert_within(_sample())


def test_budget_reports_every_regressed_metric() -> None:
    violations = RUNTIME_BUDGET.violations(_sample(
        p95_frame_time_ms=20.0,
        maximum_frame_time_ms=40.0,
        p95_draw_calls=1200,
        repaints_per_frame=2.0,
        invalidations_per_frame=40.0,
        cache_hits=50,
        cache_misses=50,
    ))

    assert len(violations) == 6
    assert {message.split(":", 1)[0] for message in violations} == {
        "p95_frame_time_ms",
        "maximum_frame_time_ms",
        "p95_draw_calls",
        "repaints_per_frame",
        "invalidations_per_frame",
        "cache_hit_ratio",
    }
    with pytest.raises(AssertionError, match="runtime-60fps-v1"):
        RUNTIME_BUDGET.assert_within(_sample(p95_frame_time_ms=20.0))


def test_empty_cache_window_is_not_a_false_failure() -> None:
    sample = _sample(cache_hits=0, cache_misses=0)

    assert sample.cache_hit_ratio == 1.0
    assert EDITOR_BUDGET.violations(sample) == ()
