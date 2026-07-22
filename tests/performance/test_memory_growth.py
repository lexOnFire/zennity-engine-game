from __future__ import annotations

from engine.performance.memory_probe import measure_allocations
from editor.runtime.play_session import EditorPlaySession


def test_play_stop_cycles_stay_within_memory_budget() -> None:
    source = [{
        "id": "player",
        "name": "Player",
        "scripts": ["Assets/Scripts/player.py"],
        "animator": {"clips": {"idle": {"frames": list(range(16))}}},
        "ui": {"type": "text", "text": "Score"},
    }]
    session = EditorPlaySession()

    def cycle() -> None:
        runtime = session.begin(source, "Player")
        runtime.append({"id": "temporary", "name": "Temporary", "spawned_by_logic": True})
        session.set_runtime_state("play")
        session.finish()

    result = measure_allocations(cycle, iterations=500, warmup=20)

    result.assert_within(retained_bytes=2 * 1024 * 1024, peak_bytes=8 * 1024 * 1024)


def test_probe_reports_intentionally_retained_allocations() -> None:
    retained: list[bytearray] = []

    result = measure_allocations(
        lambda: retained.append(bytearray(4096)),
        iterations=40,
        warmup=0,
    )

    assert result.retained_bytes >= 150_000
    assert result.retained_blocks > 0
