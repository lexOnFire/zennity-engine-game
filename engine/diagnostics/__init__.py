"""Zennity diagnostics: observability primitives shared by every process.

Phase 9.5B Stage 0 added the observability layer (logging, crash reports, error
boundaries).  Those modules are intentionally dependency-free -- they must be
importable from the viewport subprocess and from exception hooks without
dragging in ``engine.core`` (and therefore numpy).

``DiagnosticsProvider`` / ``DiagnosticsService`` predate Stage 0 and do depend
on ``engine.core``, so they are exposed lazily through ``__getattr__`` to keep
``import engine.diagnostics.logging_setup`` cheap.
"""
from engine.diagnostics.crash_report import (
    latest_crash_report,
    register_context_provider,
    set_context,
    write_crash_report,
)
from engine.diagnostics.error_boundary import (
    add_crash_listener,
    install_process_hooks,
    report_crash,
    report_error,
    swallow,
)
from engine.diagnostics.logging_setup import (
    get_logger,
    log_file_path,
    ring_buffer,
    setup_logging,
)
from engine.diagnostics.ring_buffer import RingBufferHandler

__all__ = [
    # Stage 0 observability API
    "RingBufferHandler",
    "add_crash_listener",
    "get_logger",
    "install_process_hooks",
    "latest_crash_report",
    "log_file_path",
    "register_context_provider",
    "report_crash",
    "report_error",
    "ring_buffer",
    "set_context",
    "setup_logging",
    "swallow",
    "write_crash_report",
    # legacy, resolved lazily
    "DiagnosticsProvider",
    "DiagnosticsService",
    "PerformanceCounter",
]

_LAZY = {
    "DiagnosticsProvider": ("engine.diagnostics.provider", "DiagnosticsProvider"),
    "DiagnosticsService": ("engine.diagnostics.service", "DiagnosticsService"),
    "PerformanceCounter": ("engine.diagnostics.service", "PerformanceCounter"),
}


def __getattr__(name: str):
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    value = getattr(import_module(target[0]), target[1])
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
