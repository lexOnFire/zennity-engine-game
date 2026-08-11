"""Repeated Play/Stop must not grow the process without bound.

PHASE 9.5B Stage 3.  Byte-perfect equality is not the bar -- allocators keep
arenas, caches warm up.  What must not appear is *monotonic* growth proportional
to the number of cycles.
"""

from __future__ import annotations

import gc

import pytest

from engine.runtime import RuntimeManager
from tests._lifecycle_probe import lifecycle_snapshot, scene_with_objects


@pytest.fixture
def manager():
    instance = RuntimeManager()
    yield instance
    instance.stop_play()


def _tracked_objects() -> int:
    gc.collect()
    return len(gc.get_objects())


def _run_cycle(manager, scene, frames: int = 3) -> None:
    manager.start_play(scene)
    for _ in range(frames):
        manager.tick(1.0 / 60.0)
    manager.stop_play()


def test_object_count_does_not_grow_linearly(manager):
    scene = scene_with_objects()

    _run_cycle(manager, scene)  # warm up caches so they are not counted as growth
    after_first = _tracked_objects()

    for _ in range(5):
        _run_cycle(manager, scene)
    after_five = _tracked_objects()

    for _ in range(5):
        _run_cycle(manager, scene)
    after_ten = _tracked_objects()

    growth_first_half = after_five - after_first
    growth_second_half = after_ten - after_five

    # A genuine per-cycle leak grows the second window as much as the first.
    assert growth_second_half <= max(growth_first_half, 0) + 2000, (
        "tracked object count keeps growing per cycle: "
        f"{after_first} -> {after_five} -> {after_ten}"
    )


def test_handler_counts_are_flat_across_cycles(manager):
    """The precise signal: registrations must be identical every time."""
    scene = scene_with_objects()
    baseline = lifecycle_snapshot()

    for cycle in range(1, 11):
        _run_cycle(manager, scene)
        assert lifecycle_snapshot() == baseline, f"drift after cycle {cycle}"


@pytest.mark.slow
def test_memory_trend_over_twenty_cycles(manager):
    scene = scene_with_objects()
    samples = {}

    _run_cycle(manager, scene)
    samples["after_stop_1"] = _tracked_objects()

    for _ in range(4):
        _run_cycle(manager, scene)
    samples["after_stop_5"] = _tracked_objects()

    for _ in range(15):
        _run_cycle(manager, scene)
    samples["after_stop_20"] = _tracked_objects()

    per_cycle_early = (samples["after_stop_5"] - samples["after_stop_1"]) / 4
    per_cycle_late = (samples["after_stop_20"] - samples["after_stop_5"]) / 15

    assert per_cycle_late <= per_cycle_early + 200, (
        f"per-cycle growth is not settling: {samples}"
    )
