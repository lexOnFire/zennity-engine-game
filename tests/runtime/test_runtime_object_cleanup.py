"""Runtime objects and their references must not outlive the session.

PHASE 9.5B Stage 3.  ``weakref`` is used strictly as a *detector*: the cleanup
itself must be explicit, and ``gc.collect()`` only reveals whether a strong
reference was left behind.
"""

from __future__ import annotations

import gc
import weakref

import pytest

from engine.game_object import GameObject
from engine.runtime import RuntimeManager

from tests._lifecycle_probe import lifecycle_snapshot, scene_with_objects


@pytest.fixture
def manager():
    instance = RuntimeManager()
    yield instance
    instance.stop_play()


def test_runtime_scene_is_released_on_stop(manager):
    scene = scene_with_objects()
    runtime_scene = manager.start_play(scene)
    reference = weakref.ref(runtime_scene)
    manager.tick(1.0 / 60.0)
    del runtime_scene

    manager.stop_play()
    gc.collect()

    assert reference() is None, "the stopped runtime scene is still reachable"


def test_spawned_objects_are_released_on_stop(manager):
    """Objects created *inside* the session must not survive it.

    They are added through the runtime scene, which is a copy of the authoring
    scene -- so nothing here touches the editor's own object list.
    """
    scene = scene_with_objects(count=1)
    runtime_scene = manager.start_play(scene)
    runtime = runtime_scene.scene

    references = []
    for index in range(10):
        spawned = GameObject(f"Spawned{index}")
        references.append(weakref.ref(spawned))
        runtime._add_go(spawned)
        runtime.editable_objects.append(spawned)
        del spawned

    manager.tick(1.0 / 60.0)
    del runtime_scene, runtime
    manager.stop_play()
    gc.collect()

    alive = [reference for reference in references if reference() is not None]
    assert not alive, f"{len(alive)} of 10 spawned objects survived the Stop"


def test_the_authoring_scene_survives_the_session(manager):
    """The inverse guarantee: Stop must not destroy the editor's own scene."""
    scene = scene_with_objects(count=3)
    before = [obj.name for obj in scene.editable_objects]

    manager.start_play(scene)
    manager.tick(1.0 / 60.0)
    manager.stop_play()

    assert [obj.name for obj in scene.editable_objects] == before
