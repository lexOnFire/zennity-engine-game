from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable


LifecycleCallback = Callable[[], None]
LifecycleUpdateCallback = Callable[[float], None]
EnabledPredicate = Callable[[], bool]


@dataclass
class LifecycleEntry:
    key: Hashable
    enabled: EnabledPredicate
    awake: LifecycleCallback | None = None
    start: LifecycleCallback | None = None
    update: LifecycleUpdateCallback | None = None
    fixed_update: LifecycleUpdateCallback | None = None
    late_update: LifecycleUpdateCallback | None = None
    stop: LifecycleCallback | None = None
    started: bool = False


class LifecycleScheduler:
    """Canonical ordered lifecycle for Runtime components and scripts."""

    def __init__(self, *, fixed_delta_time: float = 1.0 / 60.0, max_fixed_steps: int = 8) -> None:
        if fixed_delta_time <= 0.0:
            raise ValueError("fixed_delta_time must be greater than zero")
        if max_fixed_steps < 1:
            raise ValueError("max_fixed_steps must be at least one")
        self.fixed_delta_time = float(fixed_delta_time)
        self.max_fixed_steps = int(max_fixed_steps)
        self._entries: list[LifecycleEntry] = []
        self._entries_by_key: dict[Hashable, LifecycleEntry] = {}
        self._fixed_accumulator = 0.0
        self.running = False

    def register(self, entry: LifecycleEntry) -> LifecycleEntry:
        if entry.key in self._entries_by_key:
            return self._entries_by_key[entry.key]
        self._entries.append(entry)
        self._entries_by_key[entry.key] = entry
        if self.running:
            self._start_entry(entry)
        return entry

    def unregister(self, key: Hashable) -> bool:
        entry = self._entries_by_key.pop(key, None)
        if entry is None:
            return False
        if entry.started and entry.stop is not None:
            entry.stop()
        entry.started = False
        self._entries.remove(entry)
        return True

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._fixed_accumulator = 0.0
        for entry in list(self._entries):
            self._start_entry(entry)

    def update(self, delta_time: float) -> None:
        self._run_update_phase("update", float(delta_time))

    def run_fixed_updates(self, delta_time: float, step: LifecycleUpdateCallback | None = None) -> int:
        if not self.running:
            return 0
        self._fixed_accumulator += max(0.0, float(delta_time))
        epsilon = self.fixed_delta_time * 1e-9
        available_steps = int((self._fixed_accumulator + epsilon) / self.fixed_delta_time)
        steps = min(available_steps, self.max_fixed_steps)
        for _ in range(steps):
            self._run_update_phase("fixed_update", self.fixed_delta_time)
            if step is not None:
                step(self.fixed_delta_time)
            self._fixed_accumulator = max(0.0, self._fixed_accumulator - self.fixed_delta_time)
        if available_steps > self.max_fixed_steps:
            # A frame already exceeded the safety budget. Keeping its stale
            # remainder would make the next frame pay for discarded work.
            self._fixed_accumulator = 0.0
        return steps

    def late_update(self, delta_time: float) -> None:
        self._run_update_phase("late_update", float(delta_time))

    def stop(self) -> None:
        if not self.running:
            return
        for entry in reversed(list(self._entries)):
            if entry.started and entry.stop is not None:
                entry.stop()
            entry.started = False
        self.running = False
        self._fixed_accumulator = 0.0

    def clear(self) -> None:
        self.stop()
        self._entries.clear()
        self._entries_by_key.clear()

    def _start_entry(self, entry: LifecycleEntry) -> None:
        if entry.started or not entry.enabled():
            return
        if entry.awake is not None:
            entry.awake()
        if entry.start is not None:
            entry.start()
        entry.started = True

    def _run_update_phase(self, phase: str, delta_time: float) -> None:
        if not self.running:
            return
        for entry in list(self._entries):
            if not entry.started:
                self._start_entry(entry)
            if not entry.started or not entry.enabled():
                continue
            callback = getattr(entry, phase)
            if callback is not None:
                callback(delta_time)
