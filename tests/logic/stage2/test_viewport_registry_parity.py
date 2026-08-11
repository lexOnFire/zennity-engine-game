"""The viewport process must see exactly the node system the editor sees.

The viewport is started with ``multiprocessing.get_context("spawn")``, so it
does not inherit the parent's imports -- it rebuilds the whole node system from
scratch.  Before Stage 2 that rebuild went through a different loading path than
the editor's, so nodes could silently be absent at play time.

This test spawns a real ``spawn``-context child that imports the viewport
entrypoint the same way the editor's child does, then compares canonical ids.
"""

from __future__ import annotations

import multiprocessing as mp

import pytest

from ._probe import SNAPSHOT_SOURCE, run_in_fresh_process

VIEWPORT_IMPORTS = """
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import editor.isolated_viewport  # the viewport process entrypoint
"""


def _viewport_child(queue):  # pragma: no cover - runs in the child process
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    try:
        import editor.isolated_viewport  # noqa: F401

        from engine.logic.node_system import get_node_system_status

        status = get_node_system_status()
        queue.put(
            {
                "definitions": sorted(status["definition_ids"]),
                "port_schema": sorted(status["port_schema_ids"]),
                "executors": sorted(status["executor_ids"]),
                "evaluators": sorted(status["evaluator_ids"]),
                "modules": sorted(status["runtime_modules_loaded"]),
                "violations": list(status["contract_violations"]),
            }
        )
    except BaseException as exc:  # noqa: BLE001 - reported to the parent
        queue.put({"error": f"{type(exc).__name__}: {exc}"})


def test_real_spawned_viewport_process_matches_the_editor_process():
    context = mp.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_viewport_child, args=(queue,), name="stage2-viewport-probe")
    process.start()
    try:
        viewport = queue.get(timeout=300)
    finally:
        process.join(timeout=30)
        if process.is_alive():  # pragma: no cover
            process.terminate()
            process.join(timeout=10)

    if "error" in viewport:
        pytest.fail(f"viewport probe failed: {viewport['error']}")

    editor = run_in_fresh_process(SNAPSHOT_SOURCE)
    for key in ("definitions", "port_schema", "executors", "evaluators", "modules"):
        assert editor[key] == viewport[key], (
            f"{key} differ between the editor process and the spawned viewport:\n"
            f"  only in editor:   {sorted(set(editor[key]) - set(viewport[key]))}\n"
            f"  only in viewport: {sorted(set(viewport[key]) - set(editor[key]))}"
        )
    assert viewport["violations"] == []


def test_importing_the_viewport_entrypoint_matches_a_bare_import():
    """No subsystem may disappear because the viewport imports more modules."""
    bare = run_in_fresh_process(SNAPSHOT_SOURCE)
    viewport = run_in_fresh_process(VIEWPORT_IMPORTS + SNAPSHOT_SOURCE)
    for key in ("definitions", "port_schema", "executors", "evaluators", "modules"):
        assert bare[key] == viewport[key], key
