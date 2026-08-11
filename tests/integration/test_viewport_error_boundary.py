"""Phase 9.5B Stage 0 — the viewport subprocess cannot crash silently.

Before Stage 0 the viewport had NO error boundary at all: it installed no
excepthook, no faulthandler and no logging, and ``run_viewport()``'s frame loop
did ``except Exception: session.running = False``.  A crash simply blanked the
window.

These tests run the real thing in a real subprocess.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------
# In-process checks of the boundary the viewport installs
# --------------------------------------------------------------------------
def test_run_viewport_installs_its_own_boundary_source():
    """The child must not rely on inheriting the parent's hooks."""
    src = (ROOT / "editor" / "isolated_viewport.py").read_text(encoding="utf-8")

    assert "setup_logging(" in src, "viewport does not initialise logging"
    assert 'process_name="Viewport"' in src
    assert "install_process_hooks(" in src, "viewport does not install exception hooks"
    assert "report_crash(" in src, "viewport frame loop does not report crashes"
    assert "viewport_crashed" in src, "viewport does not notify the editor"


def test_frame_loop_no_longer_swallows_silently():
    src = (ROOT / "editor" / "isolated_viewport.py").read_text(encoding="utf-8")
    assert "except Exception:\n                session.running = False" not in src


def test_editor_handles_the_viewport_crashed_event():
    bootstrap = (ROOT / "editor" / "editor_bootstrap_controller.py").read_text(encoding="utf-8")
    main = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")

    assert '"viewport_crashed"' in bootstrap
    assert "_handle_viewport_crashed_event" in main
    assert "Play Mode stopped because the viewport crashed" in main


# --------------------------------------------------------------------------
# Real subprocess: a child that crashes must leave a durable trace
# --------------------------------------------------------------------------
CHILD = textwrap.dedent(
    """
    import sys, threading
    sys.path.insert(0, {root!r})
    from pathlib import Path
    from engine.diagnostics import install_process_hooks, setup_logging

    # Exactly what editor/isolated_viewport.py::run_viewport does on entry.
    setup_logging(Path({project!r}), process_name="Viewport")
    install_process_hooks(process_name="Viewport", enable_faulthandler=False)

    if {mode!r} == "main":
        raise RuntimeError("viewport main-thread probe")
    else:
        t = threading.Thread(target=lambda: (_ for _ in ()).throw(
            RuntimeError("viewport worker probe")), name="ViewportWorker")
        t.start(); t.join()
    """
)


def _run_child(tmp_path: Path, mode: str) -> int:
    import subprocess

    script = tmp_path / f"child_{mode}.py"
    script.write_text(
        CHILD.format(root=str(ROOT), project=str(tmp_path), mode=mode),
        encoding="utf-8",
    )
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=120, env=env
    )
    return proc.returncode


@pytest.mark.timeout(180)
def test_subprocess_main_thread_crash_leaves_a_log_and_a_report(tmp_path):
    _run_child(tmp_path, "main")

    log = tmp_path / "logs" / "zennity.log"
    assert log.exists(), "the child process wrote no log file"
    text = log.read_text(encoding="utf-8")
    assert "viewport main-thread probe" in text
    assert "Viewport" in text
    assert "Traceback (most recent call last)" in text

    reports = list((tmp_path / "logs").glob("crash-*.log"))
    assert reports, "no crash report for a subprocess main-thread crash"
    body = reports[0].read_text(encoding="utf-8")
    assert "process          : Viewport" in body
    assert "viewport main-thread probe" in body


@pytest.mark.timeout(180)
def test_subprocess_worker_thread_crash_leaves_a_log_and_a_report(tmp_path):
    """A worker dying in the child was completely untraceable before Stage 0."""
    rc = _run_child(tmp_path, "thread")
    assert rc == 0, "a dead worker must not take the process down"

    text = (tmp_path / "logs" / "zennity.log").read_text(encoding="utf-8")
    assert "viewport worker probe" in text
    assert "ViewportWorker" in text

    reports = list((tmp_path / "logs").glob("crash-*.log"))
    assert reports
    assert "ViewportWorker" in reports[0].read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Broken-node probe: a Logic Graph node that raises must be visible
# --------------------------------------------------------------------------
@pytest.mark.timeout(120)
def test_broken_logic_node_is_reported_not_swallowed(tmp_path):
    """Item 17: a node raising RuntimeError must surface, not vanish."""
    from engine.diagnostics.logging_setup import (
        owned_handlers, setup_logging, teardown_logging)
    from engine.diagnostics.error_boundary import report_error, swallow
    from engine.diagnostics import get_logger

    teardown_logging()
    try:
        setup_logging(tmp_path, process_name="Viewport")
        log = get_logger("logic")

        # This mirrors ViewportRuntimeInitializer._initialize_logic's handler.
        try:
            raise RuntimeError("diagnostic probe")
        except Exception as exc:
            report_error(log, "start Logic Graph for object 'Probe'", exc)

        # And the frame-loop style boundary.
        with swallow(log, "execute node 'probe_node'"):
            raise RuntimeError("diagnostic probe")

        for handler in owned_handlers():
            handler.flush()
        text = (tmp_path / "logs" / "zennity.log").read_text(encoding="utf-8")

        assert text.count("diagnostic probe") >= 2
        assert "start Logic Graph for object 'Probe'" in text
        assert "execute node 'probe_node'" in text
        assert "Traceback (most recent call last)" in text
    finally:
        teardown_logging()
