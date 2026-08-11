"""Twenty Play/Stop cycles must show no linear growth in anything.

PHASE 9.5B Stage 3.  Marked slow: the 5-cycle golden test in
``tests/runtime/test_play_stop_idempotence.py`` is the CI gate; this is the
stress run that would catch a slow leak the short one misses.

Every measurement runs in a **fresh interpreter**.  Handler registries, service
singletons and the UI dispatcher are process-global, and other tests in the
session leave runtimes alive in them -- an in-process baseline picks that up and
the comparison stops meaning anything.  Isolating the process is what makes
"identical to baseline" a real claim rather than a lucky ordering.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CYCLES = 20


def _run_in_fresh_process(source: str, timeout: int = 600) -> dict:
    environment = dict(os.environ)
    environment.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="1",
        QT_QPA_PLATFORM="offscreen",
        PYTHONPATH=str(REPO_ROOT) + os.pathsep + environment.get("PYTHONPATH", ""),
    )
    result = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=environment,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"probe failed (exit {result.returncode})\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines, f"probe produced no output\nstderr:\n{result.stderr}"
    return json.loads(lines[-1])


CYCLE_PROBE = f"""
import gc, json, weakref
from engine.runtime import RuntimeManager
from tests._lifecycle_probe import lifecycle_snapshot, scene_with_objects, session_threads

manager = RuntimeManager()
scene = scene_with_objects()
baseline = lifecycle_snapshot()
thread_baseline = session_threads()

divergences = []
references = []
for cycle in range(1, {CYCLES} + 1):
    runtime_scene = manager.start_play(scene)
    references.append(weakref.ref(runtime_scene))
    for _ in range(3):
        manager.tick(1.0 / 60.0)
    del runtime_scene
    manager.stop_play()
    snapshot = lifecycle_snapshot()
    if snapshot != baseline:
        divergences.append([cycle, snapshot])

gc.collect()
print(json.dumps({{
    "baseline": baseline,
    "divergences": divergences,
    "thread_baseline": thread_baseline,
    "threads_after": session_threads(),
    "runtime_scenes_alive": sum(1 for r in references if r() is not None),
    "cycles": {CYCLES},
}}))
"""


@pytest.mark.slow
def test_twenty_cycles_stay_at_baseline():
    result = _run_in_fresh_process(CYCLE_PROBE)
    divergences = result["divergences"]
    assert not divergences, (
        f"{len(divergences)} of {result['cycles']} cycles diverged from "
        f"{result['baseline']}; first at cycle {divergences[0][0]}: {divergences[0][1]}"
    )


@pytest.mark.slow
def test_threads_do_not_accumulate_over_twenty_cycles():
    result = _run_in_fresh_process(CYCLE_PROBE)
    assert result["threads_after"] == result["thread_baseline"]


@pytest.mark.slow
def test_runtime_scenes_do_not_accumulate():
    """Each cycle's RuntimeScene must be gone before the next one starts."""
    result = _run_in_fresh_process(CYCLE_PROBE)
    assert result["runtime_scenes_alive"] == 0, (
        f"{result['runtime_scenes_alive']} of {result['cycles']} runtime scenes "
        "are still reachable"
    )
