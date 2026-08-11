"""Reusable error boundaries: ``swallow()`` plus the process-wide hooks.

Phase 9.5B Stage 0.  **This module changes visibility, not behaviour.**

``swallow(logger, context)`` is a drop-in replacement for::

    try:
        operation()
    except Exception:
        pass

with identical control flow -- the exception is still suppressed and execution
continues after the block -- but the failure is now logged with its context,
type, message and traceback.

The process hooks (:func:`install_process_hooks`) cover the four ways an
exception escapes in a Python/Qt/pygame application:

  * ``sys.excepthook``        -- main thread, unhandled
  * ``threading.excepthook``  -- worker threads (absent before Stage 0)
  * ``sys.unraisablehook``    -- ``__del__``, GC callbacks, destructors
  * ``faulthandler``          -- native/interpreter-level faults, all threads

plus an ``atexit`` marker so a clean shutdown is distinguishable from a process
that died during teardown.
"""
from __future__ import annotations

import atexit
import faulthandler
import logging
import os
import sys
import threading
import traceback
from pathlib import Path
from typing import Any, Callable, Optional

from engine.diagnostics import crash_report, logging_setup

_hooks_installed = False
_hook_lock = threading.Lock()

#: Called with (summary, crash_report_path) when a crash-level failure occurs.
#: The editor registers a listener here to update its status bar and console.
_crash_listeners: list[Callable[[str, Optional[Path]], None]] = []


# --------------------------------------------------------------------------
# swallow -- the per-call-site boundary
# --------------------------------------------------------------------------
#: Throttle bookkeeping for ``swallow(..., throttle=N)``: key -> [seen, suppressed].
_throttle_state: dict[str, list[int]] = {}
_throttle_lock = threading.Lock()


def _throttle_allows(key: str, every: int) -> tuple[bool, int]:
    """Return ``(should_log, suppressed_since_last)`` for a throttled site."""
    with _throttle_lock:
        entry = _throttle_state.setdefault(key, [0, 0])
        entry[0] += 1
        if entry[0] == 1 or entry[0] % every == 0:
            suppressed = entry[1]
            entry[1] = 0
            return True, suppressed
        entry[1] += 1
        return False, 0


def reset_throttles() -> None:
    """Clear throttle counters (called on Play start, and by tests)."""
    with _throttle_lock:
        _throttle_state.clear()


class _Swallow:
    """Context manager behind :func:`swallow`.

    Implemented as a slotted class rather than ``@contextlib.contextmanager``
    because some call sites run per contact per frame: the generator-based
    version costs ~1.5 us per entry, this one ~0.2 us.  The success path does
    no work beyond ``__enter__``/``__exit__`` returning.
    """

    __slots__ = ("log", "context", "level", "reraise", "exc_types",
                 "throttle", "throttle_key")

    def __init__(self, log, context, level, reraise, exc_types, throttle, throttle_key):
        self.log = log
        self.context = context
        self.level = level
        self.reraise = reraise
        self.exc_types = exc_types
        self.throttle = throttle
        self.throttle_key = throttle_key

    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            return False
        if self.reraise and issubclass(exc_type, self.reraise):
            return False
        if not issubclass(exc_type, self.exc_types):
            return False
        try:
            suffix = ""
            if self.throttle and self.throttle > 1:
                should_log, suppressed = _throttle_allows(
                    self.throttle_key or self.context, self.throttle)
                if not should_log:
                    return True
                if suppressed:
                    suffix = (f" [{suppressed} identical failures suppressed "
                              f"since the last report]")
            self.log.log(self.level, "Suppressed failure while %s: %s: %s%s",
                         self.context, exc_type.__name__, exc, suffix, exc_info=exc)
        except Exception:
            try:
                print(f"[zennity] suppressed failure while {self.context}: {exc!r}",
                      file=sys.stderr)
            except Exception:
                pass
        return True  # suppress, exactly like `except Exception: pass`


def swallow(
    logger: logging.Logger | str,
    context: str,
    *,
    level: int = logging.ERROR,
    reraise: tuple[type[BaseException], ...] = (),
    exc_types: tuple[type[BaseException], ...] = (Exception,),
    throttle: int = 0,
    throttle_key: str | None = None,
) -> "_Swallow":
    """Suppress ``exc_types`` like ``except: pass`` did, but log the failure.

    Args:
        logger: a ``Logger`` or a subsystem name accepted by ``get_logger``.
        context: what was being attempted, e.g. ``"initialise animation for 'player'"``.
        level: log level for the failure (default ``ERROR``).
        reraise: exception types that must propagate rather than be swallowed.
            ``KeyboardInterrupt`` and ``SystemExit`` always propagate, because
            they derive from ``BaseException`` and are not caught here.
        exc_types: what to catch.  Narrow this when the original handler was
            narrow, so the boundary does not widen behaviour.
        throttle: for per-frame / per-event call sites, log the 1st failure and
            then only every Nth, reporting how many were suppressed in between.
            ``0`` (default) means log every failure.
        throttle_key: override the throttle bucket (defaults to ``context``).

    Control flow is unchanged from a bare ``except: pass``: the ``with`` block
    is abandoned at the point of failure and execution resumes after it.

    Cost on the success path is one object construction plus ``__enter__`` /
    ``__exit__`` -- no formatting and no logger lookup beyond the one done here.
    """
    log = logging_setup.get_logger(logger) if isinstance(logger, str) else logger
    return _Swallow(log, context, level, reraise, exc_types, throttle, throttle_key)


def report_error(
    logger: logging.Logger | str,
    context: str,
    exc: BaseException,
    *,
    level: int = logging.ERROR,
    throttle: int = 0,
    throttle_key: str | None = None,
) -> None:
    """Log an already-caught exception with context, without altering flow.

    For handlers that must keep their own recovery logic (returning a sentinel,
    emitting an event) and only need the failure to become visible.  Prefer this
    over :func:`swallow` on per-frame paths: the caller keeps its own ``try``,
    so the success path costs nothing at all.

    ``throttle`` behaves as in :func:`swallow`.
    """
    log = logging_setup.get_logger(logger) if isinstance(logger, str) else logger
    try:
        suffix = ""
        if throttle and throttle > 1:
            should_log, suppressed = _throttle_allows(throttle_key or context, throttle)
            if not should_log:
                return
            if suppressed:
                suffix = (f" [{suppressed} identical failures suppressed "
                          f"since the last report]")
        log.log(level, "%s: %s: %s%s", context, type(exc).__name__, exc, suffix,
                exc_info=exc)
    except Exception:
        pass


# --------------------------------------------------------------------------
# crash notification
# --------------------------------------------------------------------------
def add_crash_listener(listener: Callable[[str, Optional[Path]], None]) -> None:
    """Register a UI callback invoked when a crash-level failure is recorded."""
    if listener not in _crash_listeners:
        _crash_listeners.append(listener)


def remove_crash_listener(listener: Callable[[str, Optional[Path]], None]) -> None:
    if listener in _crash_listeners:
        _crash_listeners.remove(listener)


def clear_crash_listeners() -> None:
    _crash_listeners.clear()


def _notify(summary: str, report_path: Optional[Path]) -> None:
    for listener in list(_crash_listeners):
        try:
            listener(summary, report_path)
        except Exception:
            # A failing notifier must not mask the crash being reported.
            try:
                logging_setup.get_logger("diagnostics").exception(
                    "Crash listener raised while reporting: %s", summary)
            except Exception:
                pass


def report_crash(
    exc_type: type[BaseException] | None,
    exc: BaseException | None,
    tb: Any,
    *,
    origin: str,
    thread_name: str | None = None,
    thread_ident: int | None = None,
    extra_context: dict[str, Any] | None = None,
) -> Optional[Path]:
    """Log a crash, write a crash report, and notify listeners.  Never raises."""
    log = logging_setup.get_logger("diagnostics")
    type_name = getattr(exc_type, "__name__", str(exc_type))
    summary = f"{type_name}: {exc}" if exc is not None else str(origin)

    try:
        log.critical("CRASH (%s) in thread %s: %s",
                     origin, thread_name or threading.current_thread().name, summary,
                     exc_info=(exc_type, exc, tb) if exc_type and exc else None)
    except Exception:
        pass

    path = crash_report.write_crash_report(
        exc_type, exc, tb,
        origin=origin,
        thread_name=thread_name,
        thread_ident=thread_ident,
        extra_context=extra_context,
    )

    if path is not None:
        try:
            log.critical("Crash report written to %s", path)
        except Exception:
            pass

    _notify(summary, path)
    return path


# --------------------------------------------------------------------------
# process-wide hooks
# --------------------------------------------------------------------------
def install_process_hooks(
    *,
    process_name: str = "Editor",
    enable_faulthandler: bool = True,
    install_qt_handler: bool = False,
) -> None:
    """Install every process-level exception boundary.  Idempotent.

    Must be called in **each** process -- a multiprocessing child does not
    inherit the parent's hooks.
    """
    global _hooks_installed

    with _hook_lock:
        if _hooks_installed:
            return
        _hooks_installed = True

    log = logging_setup.get_logger("diagnostics")
    previous_excepthook = sys.excepthook
    previous_unraisable = getattr(sys, "unraisablehook", None)

    # -- main-thread unhandled exceptions ---------------------------------
    def _excepthook(exc_type, exc, tb) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            # Ctrl-C is a user action, not a crash.
            previous_excepthook(exc_type, exc, tb)
            return
        report_crash(exc_type, exc, tb, origin=f"unhandled exception ({process_name})")
        try:
            previous_excepthook(exc_type, exc, tb)
        except Exception:
            pass

    sys.excepthook = _excepthook

    # -- worker-thread exceptions -----------------------------------------
    def _threading_excepthook(args) -> None:
        thread = getattr(args, "thread", None)
        name = getattr(thread, "name", "<unknown>")
        ident = getattr(thread, "ident", None)
        if args.exc_type is not None and issubclass(args.exc_type, SystemExit):
            return
        report_crash(
            args.exc_type, args.exc_value, args.exc_traceback,
            origin=f"unhandled exception in thread ({process_name})",
            thread_name=name,
            thread_ident=ident,
        )

    threading.excepthook = _threading_excepthook

    # -- unraisable exceptions (__del__, GC callbacks, destructors) --------
    def _unraisablehook(unraisable) -> None:
        exc = getattr(unraisable, "exc_value", None)
        exc_type = getattr(unraisable, "exc_type", None)
        tb = getattr(unraisable, "exc_traceback", None)
        obj = getattr(unraisable, "object", None)
        err_msg = getattr(unraisable, "err_msg", None) or "unraisable exception"
        try:
            log.error(
                "UNRAISABLE (%s): %s in %r: %s: %s",
                process_name, err_msg, obj,
                getattr(exc_type, "__name__", exc_type), exc,
                exc_info=(exc_type, exc, tb) if exc_type and exc else None,
            )
        except Exception:
            try:
                traceback.print_exception(exc_type, exc, tb, file=sys.stderr)
            except Exception:
                pass

    if previous_unraisable is not None:
        sys.unraisablehook = _unraisablehook

    # -- native / interpreter-level faults, all threads --------------------
    if enable_faulthandler:
        state = logging_setup.current_state()
        target = None
        if state is not None and state.log_dir is not None:
            try:
                target = (state.log_dir / f"faulthandler-{process_name.lower()}.log").open(
                    "a", encoding="utf-8", buffering=1)
            except OSError:
                target = None
        try:
            faulthandler.enable(file=target or sys.stderr, all_threads=True)
        except Exception:
            pass

    # -- Qt message handler (editor process only) --------------------------
    if install_qt_handler:
        _install_qt_message_handler()

    # -- shutdown marker ---------------------------------------------------
    # Without this, a process that dies during teardown is indistinguishable
    # from one that was killed: the log simply stops mid-sentence.
    def _on_exit() -> None:
        try:
            log.info("Process exiting cleanly (process=%s pid=%s)", process_name, os.getpid())
            for handler in logging.getLogger(logging_setup.ROOT_LOGGER_NAME).handlers:
                try:
                    handler.flush()
                except Exception:
                    pass
        except Exception:
            pass

    atexit.register(_on_exit)

    log.info("Process error boundaries installed (process=%s)", process_name)


def _install_qt_message_handler() -> None:
    try:
        from PySide6.QtCore import QtMsgType, qInstallMessageHandler
    except Exception:
        return

    qt_log = logging_setup.get_logger("editor.qt")
    _levels = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }

    def _handler(mode, context, message) -> None:
        try:
            qt_log.log(_levels.get(mode, logging.WARNING), "Qt: %s", message)
        except Exception:
            pass

    try:
        qInstallMessageHandler(_handler)
    except Exception:
        pass


def hooks_installed() -> bool:
    return _hooks_installed


def reset_hooks_for_tests() -> None:
    """Allow a test to re-install hooks.  Not used by production code."""
    global _hooks_installed
    with _hook_lock:
        _hooks_installed = False
