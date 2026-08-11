"""No thread started by a Play session may outlive it.

PHASE 9.5B Stage 3.  ``thread.daemon = True`` is not cleanup: a daemon thread
still runs, still holds references, and still accumulates across cycles -- it is
merely killed at interpreter exit.
"""

from __future__ import annotations

import threading

import pytest

from engine.runtime import RuntimeManager

from tests._lifecycle_probe import lifecycle_snapshot, scene_with_objects

#: Threads that legitimately exist for the life of the process.  Anything else
#: appearing after a Stop is a session thread that was never shut down.
ALLOWED_PERSISTENT_THREADS = (
    "MainThread",
    "pydevd",          # debugger, when running under an IDE
    "QThread",         # Qt internal pools
    "ThreadPoolExecutor",
)


def _session_threads() -> list[str]:
    return sorted(
        thread.name
        for thread in threading.enumerate()
        if thread is not threading.main_thread()
        and not any(thread.name.startswith(allowed) for allowed in ALLOWED_PERSISTENT_THREADS)
    )


@pytest.fixture
def manager():
    instance = RuntimeManager()
    yield instance
    instance.stop_play()


def test_threads_do_not_accumulate_over_five_cycles(manager):
    scene = scene_with_objects()
    baseline = _session_threads()

    for cycle in range(1, 6):
        manager.start_play(scene)
        manager.tick(1.0 / 60.0)
        manager.stop_play()
        assert _session_threads() == baseline, (
            f"threads left over after Stop #{cycle}: "
            f"{sorted(set(_session_threads()) - set(baseline))}"
        )


def test_no_session_thread_survives_a_single_stop(manager):
    scene = scene_with_objects()
    baseline = _session_threads()
    manager.start_play(scene)
    for _ in range(5):
        manager.tick(1.0 / 60.0)
    manager.stop_play()
    assert _session_threads() == baseline
