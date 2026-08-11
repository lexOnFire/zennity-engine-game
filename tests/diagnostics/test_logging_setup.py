"""Phase 9.5B Stage 0 — central logging foundation."""
from __future__ import annotations

import logging
import re

import pytest

from engine.diagnostics import logging_setup
from engine.diagnostics.logging_setup import (
    ROOT_LOGGER_NAME,
    get_logger,
    owned_handlers,
    setup_logging,
    teardown_logging,
)


@pytest.fixture(autouse=True)
def _clean_logging():
    teardown_logging()
    yield
    teardown_logging()


def test_setup_creates_log_dir_and_file(tmp_path):
    state = setup_logging(tmp_path, process_name="Editor")

    assert state.log_dir == tmp_path / "logs"
    assert state.log_dir.is_dir()
    assert state.log_path == tmp_path / "logs" / "zennity.log"
    assert state.log_path.exists()


def test_installs_exactly_three_handlers(tmp_path):
    setup_logging(tmp_path)

    handlers = owned_handlers()
    assert len(handlers) == 3
    kinds = {type(h).__name__ for h in handlers}
    assert kinds == {"RotatingFileHandler", "StreamHandler", "RingBufferHandler"}


def test_setup_is_idempotent(tmp_path):
    """Editor and viewport may both call it; handlers must not accumulate."""
    first = setup_logging(tmp_path)
    second = setup_logging(tmp_path)
    third = setup_logging(tmp_path)

    assert first is second is third
    handlers = owned_handlers()
    assert len(handlers) == 3
    assert sum(1 for h in handlers if type(h).__name__ == "RotatingFileHandler") == 1
    assert sum(1 for h in handlers if type(h).__name__ == "StreamHandler") == 1
    assert sum(1 for h in handlers if type(h).__name__ == "RingBufferHandler") == 1


def test_force_rebuilds_without_duplicating(tmp_path):
    setup_logging(tmp_path)
    setup_logging(tmp_path, force=True)
    assert len(owned_handlers()) == 3


def test_record_reaches_the_log_file(tmp_path):
    setup_logging(tmp_path)
    get_logger("logic").error("probe-message-12345")

    for handler in owned_handlers():
        handler.flush()

    text = (tmp_path / "logs" / "zennity.log").read_text(encoding="utf-8")
    assert "probe-message-12345" in text


def test_format_contains_required_fields(tmp_path):
    """timestamp, level, process, pid, thread, subsystem, message."""
    setup_logging(tmp_path, process_name="Viewport")
    get_logger("physics").warning("field-probe")
    for handler in owned_handlers():
        handler.flush()

    line = next(
        l for l in (tmp_path / "logs" / "zennity.log").read_text(encoding="utf-8").splitlines()
        if "field-probe" in l
    )

    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} ", line), line
    assert "WARNING" in line
    assert "Viewport:" in line          # process name and pid
    assert "MainThread" in line         # thread name
    assert "zennity.physics" in line    # subsystem logger
    assert line.rstrip().endswith("field-probe")


def test_get_logger_normalises_names():
    assert get_logger("logic").name == "zennity.logic"
    assert get_logger("zennity.logic").name == "zennity.logic"
    assert get_logger("").name == "zennity.misc"


def test_zennity_logger_does_not_propagate_to_root(tmp_path):
    setup_logging(tmp_path)
    assert logging.getLogger(ROOT_LOGGER_NAME).propagate is False


def test_rotation_creates_backups(tmp_path):
    """Log files must not grow without bound."""
    setup_logging(tmp_path, max_bytes=2048, backup_count=3)
    log = get_logger("logic")

    payload = "x" * 200
    for i in range(200):
        log.error("rotation-probe %d %s", i, payload)
    for handler in owned_handlers():
        handler.flush()

    log_dir = tmp_path / "logs"
    assert (log_dir / "zennity.log").exists()
    backups = sorted(p.name for p in log_dir.glob("zennity.log.*"))
    assert backups, "rotation never produced a backup file"
    assert len(backups) <= 3, f"backup_count exceeded: {backups}"
    for path in log_dir.glob("zennity.log*"):
        assert path.stat().st_size < 20_000, f"{path.name} grew past the rotation bound"


def test_survives_unwritable_log_dir(tmp_path, monkeypatch):
    """A read-only location must degrade to console+ring, not crash startup."""
    def _boom(*_args, **_kwargs):
        raise OSError("read-only filesystem")

    monkeypatch.setattr("pathlib.Path.mkdir", _boom)
    state = setup_logging(tmp_path)

    assert state.log_dir is None
    assert state.file_handler is None
    assert state.ring_handler is not None
    get_logger("logic").error("still works")  # must not raise
