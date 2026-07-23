from __future__ import annotations

import pytest

from engine.runtime.lifecycle_scheduler import LifecycleEntry, LifecycleScheduler


def _entry(events: list[tuple[str, float | None]], *, enabled=lambda: True) -> LifecycleEntry:
    return LifecycleEntry(
        key="probe",
        enabled=enabled,
        awake=lambda: events.append(("awake", None)),
        start=lambda: events.append(("start", None)),
        update=lambda dt: events.append(("update", dt)),
        fixed_update=lambda dt: events.append(("fixed", dt)),
        late_update=lambda dt: events.append(("late", dt)),
        stop=lambda: events.append(("stop", None)),
    )


def test_scheduler_runs_each_phase_in_canonical_order() -> None:
    events: list[tuple[str, float | None]] = []
    scheduler = LifecycleScheduler(fixed_delta_time=0.02)
    scheduler.register(_entry(events))

    scheduler.start()
    scheduler.update(0.05)
    steps = scheduler.run_fixed_updates(0.05)
    scheduler.late_update(0.05)
    scheduler.stop()

    assert steps == 2
    assert events == [
        ("awake", None),
        ("start", None),
        ("update", 0.05),
        ("fixed", 0.02),
        ("fixed", 0.02),
        ("late", 0.05),
        ("stop", None),
    ]


def test_start_and_stop_are_idempotent() -> None:
    events: list[tuple[str, float | None]] = []
    scheduler = LifecycleScheduler()
    scheduler.register(_entry(events))

    scheduler.start()
    scheduler.start()
    scheduler.stop()
    scheduler.stop()

    assert [event for event, _ in events] == ["awake", "start", "stop"]


def test_disabled_entry_starts_once_when_it_becomes_enabled() -> None:
    active = False
    events: list[tuple[str, float | None]] = []
    scheduler = LifecycleScheduler()
    scheduler.register(_entry(events, enabled=lambda: active))
    scheduler.start()

    scheduler.update(0.1)
    active = True
    scheduler.update(0.2)
    scheduler.update(0.3)

    assert [event for event, _ in events] == ["awake", "start", "update", "update"]


def test_fixed_update_caps_catch_up_and_discards_excess_backlog() -> None:
    events: list[tuple[str, float | None]] = []
    scheduler = LifecycleScheduler(fixed_delta_time=0.01, max_fixed_steps=3)
    scheduler.register(_entry(events))
    scheduler.start()

    assert scheduler.run_fixed_updates(1.0) == 3
    assert scheduler.run_fixed_updates(0.009) == 0
    assert scheduler.run_fixed_updates(0.001) == 1
    assert [event for event, _ in events].count("fixed") == 4


def test_unregister_stops_started_entry_once() -> None:
    events: list[tuple[str, float | None]] = []
    scheduler = LifecycleScheduler()
    scheduler.register(_entry(events))
    scheduler.start()

    assert scheduler.unregister("probe") is True
    assert scheduler.unregister("probe") is False
    scheduler.stop()

    assert [event for event, _ in events].count("stop") == 1


def test_invalid_fixed_step_configuration_is_rejected() -> None:
    with pytest.raises(ValueError):
        LifecycleScheduler(fixed_delta_time=0.0)
    with pytest.raises(ValueError):
        LifecycleScheduler(max_fixed_steps=0)
