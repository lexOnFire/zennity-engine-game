"""Compatibilidade temporária para o ProfilerDock legado.

O cliente oficial da Diagnostics Platform vive em ``editor.profiler``.
Este módulo permanece até a remoção dos imports legados planejada para v2.0.
"""
from __future__ import annotations

import warnings

warnings.warn(
    "editor.widgets.profiler_dock está deprecado; use editor.profiler.ProfilerDock.",
    DeprecationWarning,
    stacklevel=2,
)

from editor.profiler.profiler_dock import ProfilerDock, ProfilerGraphWidget

# Nome histórico mantido somente para consumidores externos durante o sunset.
ViewportProfilerDock = ProfilerDock
PerformanceChartWidget = ProfilerGraphWidget

__all__ = [
    "PerformanceChartWidget",
    "ProfilerDock",
    "ProfilerGraphWidget",
    "ViewportProfilerDock",
]
