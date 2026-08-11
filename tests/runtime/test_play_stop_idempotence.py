"""Play -> Stop -> Play must land on the same initial state, every time.

PHASE 9.5B Stage 3.  The golden lifecycle test: five cycles, each compared
against a snapshot taken before the first Play.
"""

from __future__ import annotations

import pytest

from engine.game_object import GameObject
from engine.runtime import RuntimeManager, RuntimeState
from tests._lifecycle_probe import lifecycle_snapshot, scene_with_objects

CYCLES = 5
FRAMES_PER_CYCLE = 3


@pytest.fixture
def manager():
    instance = RuntimeManager()
    yield instance
    instance.stop_play()


def test_five_play_stop_cycles_return_to_baseline(manager):
    scene = scene_with_objects()
    baseline = lifecycle_snapshot()

    for cycle in range(1, CYCLES + 1):
        manager.start_play(scene)
        for _ in range(FRAMES_PER_CYCLE):
            manager.tick(1.0 / 60.0)
        manager.stop_play()

        assert lifecycle_snapshot() == baseline, (
            f"state diverged from baseline after Stop #{cycle}"
        )


def test_state_is_stopped_after_every_cycle(manager):
    scene = scene_with_objects()
    for _ in range(CYCLES):
        manager.start_play(scene)
        assert manager.state == RuntimeState.PLAYING
        manager.stop_play()
        assert manager.state == RuntimeState.STOPPED
        assert manager.runtime_scene is None


def test_stop_is_idempotent(manager):
    """Stop, Stop, Stop -- a safe no-op, no KeyError or double unregister."""
    scene = scene_with_objects()
    manager.start_play(scene)
    manager.tick(1.0 / 60.0)

    manager.stop_play()
    after_first = lifecycle_snapshot()
    manager.stop_play()
    manager.stop_play()

    assert lifecycle_snapshot() == after_first
    assert manager.state == RuntimeState.STOPPED


def test_stop_without_play_is_safe():
    """An idle editor: Stop must do nothing rather than raise."""
    idle = RuntimeManager()
    baseline = lifecycle_snapshot()

    idle.stop_play()
    idle.stop_play()

    assert idle.state == RuntimeState.STOPPED
    assert idle.runtime_scene is None
    assert lifecycle_snapshot() == baseline


def test_play_while_playing_does_not_create_a_second_session(manager):
    """Documented behaviour: the second Play is ignored, not stacked."""
    scene = scene_with_objects()

    first = manager.start_play(scene)
    second = manager.start_play(scene)
    third = manager.start_play(scene)

    assert first is second is third, "Play while playing created a new session"
    assert manager.state == RuntimeState.PLAYING

    manager.stop_play()
    assert manager.runtime_scene is None


def test_runtime_spawned_objects_do_not_survive_stop(manager):
    """Objects created during a session must not appear in the next one."""
    scene = scene_with_objects(count=2)
    authoring_count = len(scene.editable_objects)

    for _ in range(3):
        runtime_scene = manager.start_play(scene)
        target = runtime_scene.scene
        for index in range(10):
            spawned = GameObject(f"Spawned{index}")
            if hasattr(target, "_add_go"):
                target._add_go(spawned)
        manager.tick(1.0 / 60.0)
        manager.stop_play()

        assert len(scene.editable_objects) == authoring_count, (
            "runtime-spawned objects leaked into the authoring scene"
        )
