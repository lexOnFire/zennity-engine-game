from __future__ import annotations

import os
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from math import ceil
from time import perf_counter_ns
from typing import Callable, Iterator


@dataclass
class FrameProfile:
    index: int
    frame_time_ms: float
    cpu_time_ms: float
    memory_mb: float
    object_count: int
    physics_bodies: int
    subsystems_ms: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ProfilerSummary:
    sample_count: int
    fps: float
    average_frame_ms: float
    p95_frame_ms: float
    maximum_frame_ms: float
    average_cpu_ms: float
    memory_mb: float
    object_count: int
    physics_bodies: int
    subsystems_ms: dict[str, float]


class RuntimeProfiler:
    """Bounded, opt-in frame and subsystem profiler."""

    def __init__(
        self,
        *,
        capacity: int = 240,
        enabled: bool = True,
        memory_sample_interval: int = 30,
        clock_ns: Callable[[], int] = perf_counter_ns,
        memory_reader: Callable[[], float] | None = None,
    ) -> None:
        if capacity < 1:
            raise ValueError("profiler capacity must be positive")
        self.enabled = bool(enabled)
        self.capacity = int(capacity)
        self.memory_sample_interval = max(1, int(memory_sample_interval))
        self.history: deque[FrameProfile] = deque(maxlen=self.capacity)
        self._clock_ns = clock_ns
        self._memory_reader = memory_reader or process_memory_mb
        self._frame_started_ns: int | None = None
        self._frame_subsystems: dict[str, float] = {}
        self._frame_index = 0
        self._last_memory_mb = 0.0

    def begin_frame(self) -> None:
        if not self.enabled:
            return
        self._frame_started_ns = self._clock_ns()
        self._frame_subsystems = {}

    @contextmanager
    def measure(self, subsystem: str) -> Iterator[None]:
        if not self.enabled:
            yield
            return
        started = self._clock_ns()
        try:
            yield
        finally:
            self.record_ns(subsystem, self._clock_ns() - started)

    def record_ns(self, subsystem: str, elapsed_ns: int) -> None:
        if not self.enabled:
            return
        elapsed_ms = max(0, int(elapsed_ns)) / 1_000_000.0
        name = str(subsystem).strip() or "other"
        if self._frame_started_ns is not None:
            self._frame_subsystems[name] = (
                self._frame_subsystems.get(name, 0.0) + elapsed_ms
            )
        elif self.history:
            latest = self.history[-1]
            latest.subsystems_ms[name] = (
                latest.subsystems_ms.get(name, 0.0) + elapsed_ms
            )

    def end_frame(
        self,
        delta_time: float,
        *,
        object_count: int = 0,
        physics_bodies: int = 0,
    ) -> FrameProfile | None:
        if not self.enabled or self._frame_started_ns is None:
            return None
        finished_ns = self._clock_ns()
        cpu_time_ms = max(0, finished_ns - self._frame_started_ns) / 1_000_000.0
        if self._frame_index % self.memory_sample_interval == 0:
            self._last_memory_mb = max(0.0, float(self._memory_reader()))
        sample = FrameProfile(
            index=self._frame_index,
            frame_time_ms=max(0.0, float(delta_time)) * 1000.0,
            cpu_time_ms=cpu_time_ms,
            memory_mb=self._last_memory_mb,
            object_count=max(0, int(object_count)),
            physics_bodies=max(0, int(physics_bodies)),
            subsystems_ms=dict(self._frame_subsystems),
        )
        self.history.append(sample)
        self._frame_index += 1
        self._frame_started_ns = None
        self._frame_subsystems = {}
        return sample

    def reset(self) -> None:
        self.history.clear()
        self._frame_started_ns = None
        self._frame_subsystems = {}
        self._frame_index = 0

    def summary(self, window: int | None = None) -> ProfilerSummary:
        samples = list(self.history)
        if window is not None:
            samples = samples[-max(0, int(window)):]
        if not samples:
            return ProfilerSummary(
                0, 0.0, 0.0, 0.0, 0.0, 0.0, self._last_memory_mb, 0, 0, {}
            )
        frame_times = sorted(sample.frame_time_ms for sample in samples)
        average_frame = sum(frame_times) / len(frame_times)
        subsystem_names = {
            name for sample in samples for name in sample.subsystems_ms
        }
        subsystem_averages = {
            name: sum(sample.subsystems_ms.get(name, 0.0) for sample in samples)
            / len(samples)
            for name in sorted(subsystem_names)
        }
        latest = samples[-1]
        return ProfilerSummary(
            sample_count=len(samples),
            fps=0.0 if average_frame <= 0 else 1000.0 / average_frame,
            average_frame_ms=average_frame,
            p95_frame_ms=_percentile(frame_times, 0.95),
            maximum_frame_ms=max(frame_times),
            average_cpu_ms=sum(sample.cpu_time_ms for sample in samples)
            / len(samples),
            memory_mb=latest.memory_mb,
            object_count=latest.object_count,
            physics_bodies=latest.physics_bodies,
            subsystems_ms=subsystem_averages,
        )


def process_memory_mb() -> float:
    try:
        import psutil
    except ImportError:
        return 0.0
    try:
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except (OSError, psutil.Error):
        return 0.0


def _percentile(sorted_values: list[float], quantile: float) -> float:
    if not sorted_values:
        return 0.0
    index = min(
        len(sorted_values) - 1,
        max(0, ceil(len(sorted_values) * quantile) - 1),
    )
    return sorted_values[index]
