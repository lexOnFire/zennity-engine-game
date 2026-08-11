"""Phase 9.5B Stage 0 — crash reports and the in-memory ring buffer."""
from __future__ import annotations

import re

import pytest

from engine.diagnostics import crash_report
from engine.diagnostics.crash_report import (
    clear_context,
    latest_crash_report,
    register_context_provider,
    render_report,
    set_context,
    write_crash_report,
)
from engine.diagnostics.logging_setup import (
    get_logger,
    owned_handlers,
    ring_buffer,
    setup_logging,
    teardown_logging,
)
from engine.diagnostics.ring_buffer import RingBufferHandler


@pytest.fixture
def project(tmp_path):
    teardown_logging()
    clear_context()
    setup_logging(tmp_path, process_name="Viewport")
    yield tmp_path
    teardown_logging()
    clear_context()


def boom() -> BaseException:
    try:
        raise RuntimeError("diagnostic probe")
    except RuntimeError as exc:
        return exc


# ------------------------------------------------------------------ content
def test_report_contains_every_required_field(project):
    set_context(project=str(project), active_scene="Level1.zscene", mode="Play")
    exc = boom()

    body = render_report(type(exc), exc, exc.__traceback__, origin="unit test")

    assert re.search(r"timestamp\s+: \d{4}-\d{2}-\d{2} ", body)
    assert "engine version   :" in body
    assert "python version   :" in body
    assert "platform         :" in body
    assert "process          : Viewport" in body
    assert "thread           : MainThread" in body
    assert "active_scene     : Level1.zscene" in body
    assert "mode             : Play" in body
    assert "type             : RuntimeError" in body
    assert "message          : diagnostic probe" in body
    assert "Traceback (most recent call last)" in body
    assert "diagnostic probe" in body


def test_report_embeds_recent_log_records(project):
    log = get_logger("logic")
    for i in range(5):
        log.info("ring-context-%d", i)
    exc = boom()

    body = render_report(type(exc), exc, exc.__traceback__, origin="unit test")

    assert "last 200 log records" in body
    for i in range(5):
        assert f"ring-context-{i}" in body


def test_context_provider_is_queried_at_crash_time(project):
    register_context_provider(lambda: {"live_value": "computed-late"})
    exc = boom()
    assert "computed-late" in render_report(type(exc), exc, exc.__traceback__)


def test_failing_context_provider_does_not_break_the_report(project):
    def _bad():
        raise RuntimeError("provider exploded")

    register_context_provider(_bad)
    exc = boom()
    body = render_report(type(exc), exc, exc.__traceback__)
    assert "diagnostic probe" in body


# --------------------------------------------------------------------- file
def test_write_creates_timestamped_file(project):
    exc = boom()
    path = write_crash_report(type(exc), exc, exc.__traceback__, project_root=project)

    assert path is not None
    assert path.parent == project / "logs"
    assert re.match(r"crash-\d{8}-\d{6}(-\d+)?\.log$", path.name), path.name
    assert "diagnostic probe" in path.read_text(encoding="utf-8")


def test_two_crashes_in_the_same_second_do_not_overwrite(project):
    exc = boom()
    first = write_crash_report(type(exc), exc, exc.__traceback__, project_root=project)
    second = write_crash_report(type(exc), exc, exc.__traceback__, project_root=project)

    assert first != second
    assert first.exists() and second.exists()


def test_latest_crash_report_finds_the_newest(project):
    exc = boom()
    write_crash_report(type(exc), exc, exc.__traceback__, project_root=project)
    newest = write_crash_report(type(exc), exc, exc.__traceback__, project_root=project)
    assert latest_crash_report(project) == newest


def test_write_never_raises_on_bad_destination(project, monkeypatch):
    monkeypatch.setattr("pathlib.Path.mkdir", lambda *a, **k: (_ for _ in ()).throw(OSError()))
    exc = boom()
    assert write_crash_report(type(exc), exc, exc.__traceback__,
                              project_root=project / "nope") is None


# -------------------------------------------------------------- ring buffer
def test_ring_buffer_is_bounded():
    handler = RingBufferHandler(capacity=10)
    handler.setFormatter(__import__("logging").Formatter("%(message)s"))
    log = __import__("logging").getLogger("ring-test")
    log.handlers = [handler]
    log.setLevel(10)

    for i in range(100):
        log.debug("entry-%d", i)

    snapshot = handler.snapshot()
    assert len(snapshot) == 10
    assert snapshot[0] == "entry-90"
    assert snapshot[-1] == "entry-99"


def test_ring_buffer_snapshot_limit():
    handler = RingBufferHandler(capacity=50)
    handler.setFormatter(__import__("logging").Formatter("%(message)s"))
    for i in range(50):
        handler.emit(__import__("logging").LogRecord(
            "n", 20, "f", 1, "line-%d", (i,), None))
    assert len(handler.snapshot(limit=5)) == 5


def test_ring_buffer_default_capacity_is_200(project):
    log = get_logger("logic")
    for i in range(500):
        log.info("flood-%d", i)
    assert len(ring_buffer()) == 200


def test_ring_buffer_survives_unformattable_record():
    handler = RingBufferHandler(capacity=5)

    class Exploding:
        def __str__(self):
            raise ValueError("cannot render")

    handler.setFormatter(__import__("logging").Formatter("%(message)s"))
    handler.emit(__import__("logging").LogRecord(
        "n", 20, "f", 1, "%s", (Exploding(),), None))
    assert len(handler) == 1
