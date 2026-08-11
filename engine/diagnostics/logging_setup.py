"""Central logging configuration shared by every Zennity process.

Phase 9.5B Stage 0.  One implementation, used by both the editor main process
and the isolated viewport subprocess -- the subprocess does **not** inherit the
parent's logging configuration, so each process calls :func:`setup_logging`
exactly once at startup.

Design constraints:
  * idempotent -- calling it twice must not duplicate handlers
  * cheap on the normal path -- no work per frame, no formatting unless a
    record is actually emitted
  * process-aware -- every line names the process so editor and viewport output
    can be told apart in a single interleaved file
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import threading
from pathlib import Path
from typing import Optional

from engine.diagnostics.ring_buffer import RingBufferHandler

#: Root of the Zennity logger hierarchy.  Every subsystem logger lives under it.
ROOT_LOGGER_NAME = "zennity"

#: Canonical subsystem logger names.  Use :func:`get_logger` rather than these
#: directly; they are listed to document the convention.
SUBSYSTEMS = (
    "zennity.logic",
    "zennity.physics",
    "zennity.animation",
    "zennity.ui",
    "zennity.audio",
    "zennity.viewport",
    "zennity.scene",
    "zennity.assets",
    "zennity.dialogue",
    "zennity.editor",
    "zennity.runtime",
    "zennity.diagnostics",
)

LOG_DIR_NAME = "logs"
LOG_FILE_NAME = "zennity.log"

DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5
DEFAULT_RING_CAPACITY = 200

_FORMAT = (
    "%(asctime)s.%(msecs)03d %(levelname)-8s "
    "[%(processName)s:%(process)d/%(threadName)s] %(name)s: %(message)s"
)
_DATEFMT = "%Y-%m-%d %H:%M:%S"

# Marks the handlers this module owns, so idempotency checks never trip over a
# handler installed by something else (pytest's caplog, for example).
_OWNED = "_zennity_diagnostics_handler"

_lock = threading.Lock()
_state: Optional["LoggingState"] = None


class LoggingState:
    """Handles installed by :func:`setup_logging`, for teardown and tests."""

    __slots__ = ("log_dir", "log_path", "file_handler", "console_handler",
                 "ring_handler", "process_name")

    def __init__(self, log_dir, log_path, file_handler, console_handler,
                 ring_handler, process_name):
        self.log_dir = log_dir
        self.log_path = log_path
        self.file_handler = file_handler
        self.console_handler = console_handler
        self.ring_handler = ring_handler
        self.process_name = process_name


def default_log_dir(project_root: Path | str | None = None) -> Path:
    """Return ``<project_root>/logs``, defaulting to the current directory."""
    root = Path(project_root) if project_root is not None else Path.cwd()
    return root / LOG_DIR_NAME


def setup_logging(
    project_root: Path | str | None = None,
    *,
    process_name: str = "Editor",
    level: int = logging.INFO,
    console: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    ring_capacity: int = DEFAULT_RING_CAPACITY,
    force: bool = False,
) -> LoggingState:
    """Configure the ``zennity`` logger hierarchy for this process.

    Idempotent: repeated calls return the existing state without adding
    handlers.  Pass ``force=True`` to tear down and rebuild (tests only).

    Installs exactly three handlers on the ``zennity`` logger:
      * ``RotatingFileHandler``  -> ``<project_root>/logs/zennity.log``
      * ``StreamHandler``        -> stderr (optional)
      * ``RingBufferHandler``    -> in-memory, for crash-report context
    """
    global _state

    with _lock:
        if _state is not None and not force:
            return _state
        if _state is not None and force:
            _teardown_locked()

        # multiprocessing children inherit a useful default name; prefer the
        # explicit one so log lines say "Viewport" not "Process-1".
        try:
            import multiprocessing

            multiprocessing.current_process().name = process_name
        except Exception:
            pass

        log_dir = default_log_dir(project_root)
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Read-only location: fall back to console + ring buffer only.
            log_dir = None

        formatter = logging.Formatter(_FORMAT, datefmt=_DATEFMT)
        logger = logging.getLogger(ROOT_LOGGER_NAME)
        logger.setLevel(level)
        # Zennity output is fully handled here; do not double-print through the
        # root logger if the host application configured one.
        logger.propagate = False

        file_handler = None
        log_path = None
        if log_dir is not None:
            log_path = log_dir / LOG_FILE_NAME
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    log_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                    delay=False,
                )
                file_handler.setFormatter(formatter)
                file_handler.setLevel(level)
                setattr(file_handler, _OWNED, True)
                logger.addHandler(file_handler)
            except OSError:
                file_handler = None
                log_path = None

        console_handler = None
        if console:
            console_handler = logging.StreamHandler(stream=sys.stderr)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level)
            setattr(console_handler, _OWNED, True)
            logger.addHandler(console_handler)

        ring_handler = RingBufferHandler(capacity=ring_capacity)
        ring_handler.setFormatter(formatter)
        ring_handler.setLevel(logging.DEBUG)
        setattr(ring_handler, _OWNED, True)
        logger.addHandler(ring_handler)

        _state = LoggingState(
            log_dir=log_dir,
            log_path=log_path,
            file_handler=file_handler,
            console_handler=console_handler,
            ring_handler=ring_handler,
            process_name=process_name,
        )

    get_logger("diagnostics").info(
        "Logging initialised (process=%s pid=%s file=%s)",
        process_name, os.getpid(), log_path,
    )
    return _state


def get_logger(subsystem: str) -> logging.Logger:
    """Return the logger for a subsystem.

    ``get_logger("logic")`` and ``get_logger("zennity.logic")`` are equivalent.
    Safe to call at import time and before :func:`setup_logging`.
    """
    name = str(subsystem or "").strip() or "misc"
    if not name.startswith(ROOT_LOGGER_NAME + "."):
        name = f"{ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(name)


def is_configured() -> bool:
    return _state is not None


def current_state() -> Optional[LoggingState]:
    return _state


def log_file_path() -> Optional[Path]:
    return _state.log_path if _state is not None else None


def ring_buffer() -> Optional[RingBufferHandler]:
    """The in-memory handler holding recent records for crash reports."""
    return _state.ring_handler if _state is not None else None


def owned_handlers() -> list[logging.Handler]:
    """Handlers installed by this module (used by the idempotency tests)."""
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    return [h for h in logger.handlers if getattr(h, _OWNED, False)]


def _teardown_locked() -> None:
    global _state
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    for handler in list(logger.handlers):
        if not getattr(handler, _OWNED, False):
            continue
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    _state = None


def teardown_logging() -> None:
    """Remove this module's handlers.  Intended for tests and clean shutdown."""
    with _lock:
        _teardown_locked()
