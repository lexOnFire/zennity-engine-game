"""Phase 9.5B Stage 0 — swallow() must preserve behaviour and add visibility."""
from __future__ import annotations

import logging

import pytest

from engine.diagnostics.error_boundary import (
    report_error,
    reset_throttles,
    swallow,
)
from engine.diagnostics.logging_setup import (
    get_logger,
    owned_handlers,
    ring_buffer,
    setup_logging,
    teardown_logging,
)


@pytest.fixture
def logs(tmp_path):
    teardown_logging()
    reset_throttles()
    setup_logging(tmp_path, process_name="Test")
    yield tmp_path / "logs" / "zennity.log"
    teardown_logging()
    reset_throttles()


def read(path):
    for handler in owned_handlers():
        handler.flush()
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------- behaviour
def test_swallow_suppresses_like_except_pass(logs):
    """Control flow must be identical to `try/except Exception: pass`."""
    after = False
    with swallow(get_logger("logic"), "do a thing"):
        raise ValueError("boom")
    after = True
    assert after, "execution must resume after the block"


def test_swallow_abandons_the_block_at_the_failure_point(logs):
    reached = []
    with swallow(get_logger("logic"), "do a thing"):
        reached.append("before")
        raise ValueError("boom")
        reached.append("after")  # pragma: no cover
    assert reached == ["before"]


def test_swallow_is_transparent_on_success(logs):
    with swallow(get_logger("logic"), "do a thing"):
        value = 42
    assert value == 42
    assert "do a thing" not in read(logs)


def test_keyboard_interrupt_still_propagates(logs):
    with pytest.raises(KeyboardInterrupt):
        with swallow(get_logger("logic"), "do a thing"):
            raise KeyboardInterrupt


def test_system_exit_still_propagates(logs):
    with pytest.raises(SystemExit):
        with swallow(get_logger("logic"), "do a thing"):
            raise SystemExit(1)


def test_reraise_types_propagate(logs):
    with pytest.raises(ValueError):
        with swallow(get_logger("logic"), "do a thing", reraise=(ValueError,)):
            raise ValueError("must escape")


def test_narrow_exc_types_do_not_widen_behaviour(logs):
    """A narrow boundary must not start catching unrelated exceptions."""
    with pytest.raises(TypeError):
        with swallow(get_logger("logic"), "narrow", exc_types=(KeyError,)):
            raise TypeError("not caught")


# -------------------------------------------------------------- visibility
def test_swallow_logs_context_type_message_and_traceback(logs):
    with swallow(get_logger("logic"), "initialise the widget"):
        raise ValueError("specific failure text")

    text = read(logs)
    assert "initialise the widget" in text
    assert "ValueError" in text
    assert "specific failure text" in text
    assert "Traceback (most recent call last)" in text


def test_swallow_respects_level(logs):
    with swallow(get_logger("ui"), "warn only", level=logging.WARNING):
        raise ValueError("x")
    assert "WARNING" in read(logs)


def test_report_error_logs_without_changing_flow(logs):
    try:
        raise RuntimeError("caught by caller")
    except RuntimeError as exc:
        report_error(get_logger("physics"), "run the physics step", exc)

    text = read(logs)
    assert "run the physics step" in text
    assert "RuntimeError" in text
    assert "Traceback (most recent call last)" in text


# --------------------------------------------------------------- throttling
def test_throttle_reports_first_then_every_nth(logs):
    for _ in range(10):
        with swallow(get_logger("physics"), "dispatch an event", throttle=5):
            raise ValueError("repeated")

    text = read(logs)
    # 1st and 5th and 10th => 3 reports, not 10
    assert text.count("dispatch an event") == 3


def test_throttle_reports_how_many_were_suppressed(logs):
    for _ in range(5):
        with swallow(get_logger("physics"), "dispatch an event", throttle=5):
            raise ValueError("repeated")
    assert "identical failures suppressed" in read(logs)


def test_throttle_buckets_are_independent(logs):
    with swallow(get_logger("physics"), "a", throttle=100, throttle_key="k1"):
        raise ValueError
    with swallow(get_logger("physics"), "b", throttle=100, throttle_key="k2"):
        raise ValueError
    text = read(logs)
    assert "while a" in text and "while b" in text


def test_untraceable_logger_failure_does_not_escape(logs, monkeypatch):
    """If logging itself breaks, swallow must still swallow."""
    log = get_logger("logic")
    monkeypatch.setattr(log, "log", lambda *a, **k: (_ for _ in ()).throw(OSError("log broke")))
    with swallow(log, "do a thing"):
        raise ValueError("boom")
    # reaching here at all is the assertion


# ---------------------------------------------------------------- ring buffer
def test_failures_land_in_the_ring_buffer(logs):
    with swallow(get_logger("logic"), "ring probe"):
        raise ValueError("ring value")
    assert any("ring probe" in line for line in ring_buffer().snapshot())
