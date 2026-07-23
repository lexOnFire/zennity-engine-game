from __future__ import annotations

import pytest

from editor_legacy.editor_2d import Editor2DScene
from engine.performance import RuntimeProfiler
from engine.runtime import RuntimeManager


class _Clock:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self) -> int:
        return self.value

    def advance_ms(self, value: float) -> None:
        self.value += int(value * 1_000_000)


def test_profiler_records_frame_subsystems_and_summary() -> None:
    clock = _Clock()
    profiler = RuntimeProfiler(
        capacity=4,
        clock_ns=clock,
        memory_reader=lambda: 42.5,
        memory_sample_interval=1,
    )

    profiler.begin_frame()
    with profiler.measure("scripts"):
        clock.advance_ms(2)
    with profiler.measure("physics"):
        clock.advance_ms(3)
    sample = profiler.end_frame(0.02, object_count=7, physics_bodies=3)
    summary = profiler.summary()

    assert sample is not None
    assert sample.frame_time_ms == pytest.approx(20)
    assert sample.cpu_time_ms == pytest.approx(5)
    assert sample.subsystems_ms == {"scripts": 2.0, "physics": 3.0}
    assert summary.fps == pytest.approx(50)
    assert summary.memory_mb == 42.5
    assert summary.object_count == 7
    assert summary.physics_bodies == 3


def test_profiler_history_is_strictly_bounded() -> None:
    clock = _Clock()
    profiler = RuntimeProfiler(capacity=3, clock_ns=clock)

    for index in range(8):
        profiler.begin_frame()
        clock.advance_ms(1)
        profiler.end_frame(0.01 + index / 1000)

    assert len(profiler.history) == 3
    assert [sample.index for sample in profiler.history] == [5, 6, 7]


def test_profiler_p95_and_external_render_measurement() -> None:
    clock = _Clock()
    profiler = RuntimeProfiler(capacity=10, clock_ns=clock)
    for frame_ms in (10, 12, 14, 16, 30):
        profiler.begin_frame()
        clock.advance_ms(1)
        profiler.end_frame(frame_ms / 1000)
    with profiler.measure("render"):
        clock.advance_ms(4)

    summary = profiler.summary()

    assert summary.p95_frame_ms == 30
    assert summary.maximum_frame_ms == 30
    assert profiler.history[-1].subsystems_ms["render"] == 4


def test_disabled_profiler_has_no_samples() -> None:
    profiler = RuntimeProfiler(enabled=False)

    profiler.begin_frame()
    with profiler.measure("scripts"):
        pass
    assert profiler.end_frame(0.016) is None
    assert profiler.summary().sample_count == 0


def test_runtime_scene_exposes_real_subsystem_samples() -> None:
    scene = Editor2DScene()
    scene.start()
    manager = RuntimeManager()
    runtime_scene = manager.start_play(scene)

    manager.tick(0.016)
    summary = runtime_scene.profiler.summary()
    manager.stop_play()

    assert summary.sample_count == 1
    assert summary.fps == pytest.approx(62.5)
    assert summary.object_count >= 1
    assert {"scripts", "physics", "late_update", "scene"} <= set(
        summary.subsystems_ms
    )
