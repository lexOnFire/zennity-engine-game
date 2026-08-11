"""A crashed session must not poison the next one.

PHASE 9.5B Stage 3.  When the viewport process dies mid-Play, the parent has to
be able to start a clean session: no handler, service or object from the crashed
run may still be registered.
"""

from __future__ import annotations

import gc
import weakref

import pytest

from engine.runtime import RuntimeManager, RuntimeState
from tests._lifecycle_probe import (
    lifecycle_snapshot,
    reset_session_services,
    scene_with_objects,
)
from tests.integration.test_play_stop_20_cycles import _run_in_fresh_process


@pytest.fixture
def manager():
    instance = RuntimeManager()
    yield instance
    try:
        instance.stop_play()
    except Exception:
        pass
    reset_session_services()


def test_a_crash_during_start_leaves_no_partial_session():
    """start_play already rolls back on failure; this pins that contract."""
    instance = RuntimeManager()
    baseline = lifecycle_snapshot()

    class _ExplodingScene:
        @property
        def editable_objects(self):
            raise RuntimeError("simulated scene corruption")

    with pytest.raises(Exception):
        instance.start_play(_ExplodingScene())

    assert instance.state == RuntimeState.STOPPED
    assert instance.runtime_scene is None
    assert lifecycle_snapshot() == baseline, "a failed start left state behind"


CRASH_PROBE = """
import gc, json, weakref
from engine.runtime import RuntimeManager, RuntimeState
from tests._lifecycle_probe import lifecycle_snapshot, scene_with_objects

manager = RuntimeManager()
scene = scene_with_objects()
baseline = lifecycle_snapshot()

runtime_scene = manager.start_play(scene)
crashed_reference = weakref.ref(runtime_scene)
manager.tick(1.0 / 60.0)

def _explode(*args, **kwargs):
    raise RuntimeError("simulated viewport crash")

runtime_scene.update = _explode
crashed = False
try:
    manager.tick(1.0 / 60.0)
except RuntimeError:
    crashed = True

del runtime_scene
manager.stop_play()
gc.collect()

after_crash = lifecycle_snapshot()

recovered = manager.start_play(scene)
recovered_ok = recovered is not None and manager.state == RuntimeState.PLAYING
manager.tick(1.0 / 60.0)
manager.stop_play()

print(json.dumps({
    "crashed": crashed,
    "crashed_session_alive": crashed_reference() is not None,
    "baseline": baseline,
    "after_crash": after_crash,
    "after_recovery": lifecycle_snapshot(),
    "recovered_ok": recovered_ok,
}))
"""


def test_a_crash_mid_session_still_allows_a_clean_next_play():
    """Measured in a fresh process: handler registries are process-global, so an
    in-process baseline would pick up runtimes other tests left alive."""
    result = _run_in_fresh_process(CRASH_PROBE)

    assert result["crashed"], "the simulated crash did not propagate"
    assert not result["crashed_session_alive"], "the crashed session is still reachable"
    assert result["after_crash"] == result["baseline"], (
        "the crashed session left state behind"
    )
    assert result["recovered_ok"], "a fresh session could not start after the crash"
    assert result["after_recovery"] == result["baseline"]


def test_stop_after_a_crash_is_still_idempotent(manager):
    scene = scene_with_objects()
    manager.start_play(scene)

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated viewport crash")

    manager.runtime_scene.stop_runtime = _explode

    # stop_play swallows subsystem failures by design: one broken teardown must
    # not prevent the rest of the session from being released.
    manager.stop_play()
    manager.stop_play()

    assert manager.state == RuntimeState.STOPPED
    assert manager.runtime_scene is None
