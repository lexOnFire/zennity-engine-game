"""Phase 9.5B Stage 0 — no thread may die without a record.

Covers threading.excepthook, sys.excepthook and sys.unraisablehook, all of
which were ABSENT or partial before Stage 0.
"""
from __future__ import annotations

import gc
import sys
import threading

import pytest

from engine.diagnostics import error_boundary
from engine.diagnostics.error_boundary import (
    add_crash_listener,
    clear_crash_listeners,
    install_process_hooks,
    reset_hooks_for_tests,
)
from engine.diagnostics.logging_setup import (
    owned_handlers,
    setup_logging,
    teardown_logging,
)


@pytest.fixture
def hooked(tmp_path):
    saved = (sys.excepthook, threading.excepthook, sys.unraisablehook)
    teardown_logging()
    clear_crash_listeners()
    reset_hooks_for_tests()
    setup_logging(tmp_path, process_name="Test")
    install_process_hooks(process_name="Test", enable_faulthandler=False)
    yield tmp_path / "logs"
    sys.excepthook, threading.excepthook, sys.unraisablehook = saved
    reset_hooks_for_tests()
    clear_crash_listeners()
    teardown_logging()


def read_log(log_dir):
    for handler in owned_handlers():
        handler.flush()
    return (log_dir / "zennity.log").read_text(encoding="utf-8")


# ------------------------------------------------------------------- hooks
def test_hooks_are_installed(hooked):
    assert sys.excepthook is not sys.__excepthook__
    assert threading.excepthook is not threading.__excepthook__
    assert error_boundary.hooks_installed()


def test_install_is_idempotent(hooked):
    first = sys.excepthook
    install_process_hooks(process_name="Test", enable_faulthandler=False)
    assert sys.excepthook is first


# ---------------------------------------------------------- worker threads
def test_worker_thread_exception_is_logged_with_traceback(hooked):
    def explode():
        raise RuntimeError("thread probe failure")

    worker = threading.Thread(target=explode, name="ProbeWorker")
    worker.start()
    worker.join(timeout=5)

    text = read_log(hooked)
    assert "thread probe failure" in text
    assert "RuntimeError" in text
    assert "ProbeWorker" in text
    assert "Traceback (most recent call last)" in text


def test_worker_thread_exception_writes_a_crash_report(hooked):
    def explode():
        raise RuntimeError("thread crash report probe")

    worker = threading.Thread(target=explode, name="ReportWorker")
    worker.start()
    worker.join(timeout=5)

    reports = list(hooked.glob("crash-*.log"))
    assert reports, "no crash report was written for a dead thread"
    body = "\n".join(p.read_text(encoding="utf-8") for p in reports)
    assert "thread crash report probe" in body
    assert "ReportWorker" in body


def test_worker_thread_crash_notifies_listeners(hooked):
    seen = []
    add_crash_listener(lambda summary, path: seen.append((summary, path)))

    worker = threading.Thread(target=lambda: 1 / 0, name="NotifyWorker")
    worker.start()
    worker.join(timeout=5)

    assert seen, "crash listener was never notified"
    assert "ZeroDivisionError" in seen[0][0]


def test_thread_systemexit_is_not_treated_as_a_crash(hooked):
    worker = threading.Thread(target=lambda: sys.exit(0), name="ExitWorker")
    worker.start()
    worker.join(timeout=5)

    assert not list(hooked.glob("crash-*.log"))


# ----------------------------------------------------------- main-thread hook
def test_main_thread_excepthook_logs_and_reports(hooked):
    try:
        raise ValueError("main thread probe")
    except ValueError:
        sys.excepthook(*sys.exc_info())

    text = read_log(hooked)
    assert "main thread probe" in text
    assert list(hooked.glob("crash-*.log"))


def test_keyboard_interrupt_is_not_a_crash(hooked):
    try:
        raise KeyboardInterrupt
    except KeyboardInterrupt:
        sys.excepthook(*sys.exc_info())

    assert not list(hooked.glob("crash-*.log"))


# -------------------------------------------------------------- unraisable
def test_unraisable_exception_is_logged(hooked):
    """Exceptions in __del__ used to vanish entirely."""

    class Exploding:
        def __del__(self):
            raise RuntimeError("destructor probe")

    obj = Exploding()
    del obj
    gc.collect()

    text = read_log(hooked)
    assert "UNRAISABLE" in text
    assert "destructor probe" in text


def test_unraisablehook_handles_a_partial_payload(hooked):
    """The hook must not itself raise on an odd payload."""

    class Payload:
        exc_type = RuntimeError
        exc_value = RuntimeError("partial")
        exc_traceback = None
        object = None
        err_msg = None

    sys.unraisablehook(Payload())
    assert "partial" in read_log(hooked)
