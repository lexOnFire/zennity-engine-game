"""Structured crash reports: ``logs/crash-YYYYMMDD-HHMMSS.log``.

Phase 9.5B Stage 0.  Written only for genuine crashes -- unhandled exceptions
reaching a process hook, a thread dying, or an explicitly reported fatal.
Ordinary logged-and-recovered errors go to ``zennity.log`` only.

A report carries enough context to diagnose without reproducing: what was
running, which process and thread, the traceback, and the last N log lines from
the in-memory ring buffer.
"""
from __future__ import annotations

import datetime as _dt
import os
import platform
import sys
import threading
import traceback
from pathlib import Path
from typing import Any, Callable, Optional

from engine.diagnostics import logging_setup

CRASH_PREFIX = "crash-"
CRASH_SUFFIX = ".log"

#: Populated by the editor / viewport so reports can say what was running.
#: Kept as a plain dict so no import cycle is created back into the editor.
_context: dict[str, Any] = {}
_context_providers: list[Callable[[], dict[str, Any]]] = []


def set_context(**values: Any) -> None:
    """Record ambient context (project, scene, mode) for future crash reports."""
    for key, value in values.items():
        if value is None:
            _context.pop(key, None)
        else:
            _context[key] = value


def register_context_provider(provider: Callable[[], dict[str, Any]]) -> None:
    """Register a callable queried at crash time for late-bound context."""
    if provider not in _context_providers:
        _context_providers.append(provider)


def clear_context() -> None:
    _context.clear()
    _context_providers.clear()


def engine_version() -> str:
    """Best-effort engine version from package metadata, then pyproject.toml."""
    try:
        from importlib.metadata import version

        return version("zennity-engine")
    except Exception:
        pass
    try:
        root = Path(__file__).resolve().parents[2]
        text = (root / "pyproject.toml").read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("version"):
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "unknown"


def collect_context() -> dict[str, Any]:
    """Merge static context with anything the registered providers report."""
    data = dict(_context)
    for provider in list(_context_providers):
        try:
            extra = provider()
        except Exception:
            continue
        if isinstance(extra, dict):
            data.update(extra)
    return data


def _crash_dir(project_root: Path | str | None) -> Optional[Path]:
    state = logging_setup.current_state()
    if project_root is not None:
        directory = logging_setup.default_log_dir(project_root)
    elif state is not None and state.log_dir is not None:
        directory = state.log_dir
    else:
        directory = logging_setup.default_log_dir(None)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    return directory


def render_report(
    exc_type: type[BaseException] | None,
    exc: BaseException | None,
    tb: Any,
    *,
    origin: str = "unhandled exception",
    thread_name: str | None = None,
    thread_ident: int | None = None,
    extra_context: dict[str, Any] | None = None,
    log_lines: int = 200,
) -> str:
    """Build the crash report body.  Never raises."""
    now = _dt.datetime.now()
    state = logging_setup.current_state()
    context = collect_context()
    if extra_context:
        context.update(extra_context)

    current = threading.current_thread()
    name = thread_name or current.name
    ident = thread_ident if thread_ident is not None else current.ident

    lines: list[str] = []
    add = lines.append

    add("=" * 78)
    add("ZENNITY CRASH REPORT")
    add("=" * 78)
    add(f"timestamp        : {now.isoformat(sep=' ', timespec='milliseconds')}")
    add(f"origin           : {origin}")
    add(f"engine version   : {engine_version()}")
    add(f"python version   : {sys.version.split()[0]}")
    add(f"platform         : {platform.platform()}")
    add(f"machine          : {platform.machine()}")
    add(f"process          : {state.process_name if state else 'unknown'} (pid {os.getpid()})")
    add(f"thread           : {name} (ident {ident})")

    add("")
    add("-- context " + "-" * 66)
    if context:
        for key in sorted(context):
            add(f"{key:<17}: {context[key]}")
    else:
        add("(no context registered)")

    add("")
    add("-- exception " + "-" * 64)
    if exc_type is None and exc is None:
        add("(no exception object -- reported explicitly)")
    else:
        type_name = getattr(exc_type, "__name__", str(exc_type))
        add(f"type             : {type_name}")
        try:
            add(f"message          : {exc}")
        except Exception:
            add("message          : <unrepresentable>")
        add("")
        add("-- traceback " + "-" * 64)
        try:
            add("".join(traceback.format_exception(exc_type, exc, tb)).rstrip())
        except Exception:
            add("<traceback unavailable>")

    add("")
    add(f"-- last {log_lines} log records " + "-" * 48)
    ring = logging_setup.ring_buffer()
    if ring is None:
        add("(ring buffer unavailable -- logging was not initialised)")
    else:
        snapshot = ring.snapshot(limit=log_lines)
        if snapshot:
            lines.extend(snapshot)
        else:
            add("(ring buffer empty)")

    add("")
    add("-- end of report " + "-" * 60)
    return "\n".join(lines) + "\n"


def write_crash_report(
    exc_type: type[BaseException] | None = None,
    exc: BaseException | None = None,
    tb: Any = None,
    *,
    origin: str = "unhandled exception",
    project_root: Path | str | None = None,
    thread_name: str | None = None,
    thread_ident: int | None = None,
    extra_context: dict[str, Any] | None = None,
    log_lines: int = 200,
) -> Optional[Path]:
    """Write a crash report and return its path (``None`` if it could not be written).

    This function is called from exception hooks, so it must never raise.
    """
    try:
        body = render_report(
            exc_type, exc, tb,
            origin=origin,
            thread_name=thread_name,
            thread_ident=thread_ident,
            extra_context=extra_context,
            log_lines=log_lines,
        )
    except Exception:
        return None

    directory = _crash_dir(project_root)
    if directory is None:
        return None

    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = directory / f"{CRASH_PREFIX}{stamp}{CRASH_SUFFIX}"
    # Two crashes inside the same second must not overwrite each other.
    counter = 1
    while path.exists() and counter < 100:
        path = directory / f"{CRASH_PREFIX}{stamp}-{counter}{CRASH_SUFFIX}"
        counter += 1

    try:
        path.write_text(body, encoding="utf-8")
    except OSError:
        return None
    return path


def latest_crash_report(project_root: Path | str | None = None) -> Optional[Path]:
    """Most recent crash report on disk, if any."""
    directory = _crash_dir(project_root)
    if directory is None:
        return None
    try:
        reports = list(directory.glob(f"{CRASH_PREFIX}*{CRASH_SUFFIX}"))
    except OSError:
        return None
    if not reports:
        return None
    # Plain name sorting is wrong here: the de-duplication suffix makes
    # "crash-<stamp>-1.log" sort *before* "crash-<stamp>.log" ('-' < '.'), so
    # the oldest file of a same-second burst would win.  Order by (stamp,
    # counter) instead, with mtime only as a last resort for foreign names.
    def _key(path: Path) -> tuple:
        # stem is "YYYYMMDD-HHMMSS" or "YYYYMMDD-HHMMSS-N"
        stem = path.name[len(CRASH_PREFIX):-len(CRASH_SUFFIX)]
        parts = stem.split("-")
        stamp = "-".join(parts[:2])
        counter = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        try:
            mtime = path.stat().st_mtime_ns
        except OSError:
            mtime = 0
        return (stamp, counter, mtime)

    return max(reports, key=_key)
