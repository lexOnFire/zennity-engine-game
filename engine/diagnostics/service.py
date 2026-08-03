"""Serviço Central de Diagnósticos e Estatísticas de Performance (DiagnosticsService).

Infraestrutura oficial (Diagnostics Platform) consumida por:
- Profiler Visual
- FPS Overlay
- Runtime Debugger
- Memory Inspector
- Performance HUD
"""
from __future__ import annotations
import time
from typing import Dict, List, Any, Optional
from engine.core.services import IService
from engine.core.lifecycle import ServiceScope


class PerformanceCounter:
    """Contador de estatísticas de performance."""

    def __init__(self, name: str, category: str = "General", unit: str = "") -> None:
        self.name = name
        self.category = category
        self.unit = unit
        self.current_value: float = 0.0
        self.history: List[float] = []

    def record(self, value: float) -> None:
        self.current_value = value
        self.history.append(value)
        if len(self.history) > 120:  # Mantém até 120 amostras do histórico
            self.history.pop(0)


class DiagnosticScope:
    """Gerenciador de contexto para medir o tempo de execução de subsistemas (with diagnostics.measure("Physics"): ...)."""

    def __init__(self, service: DiagnosticsService, scope_name: str) -> None:
        self.service = service
        self.scope_name = scope_name
        self.start_time: float = 0.0

    def __enter__(self) -> DiagnosticScope:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
        self.service.record_scope_time(self.scope_name, elapsed_ms)


class DiagnosticsService(IService):
    """Serviço central de coleta e telemetria da Zennity Engine."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self._counters: Dict[str, PerformanceCounter] = {}
        self._scope_times: Dict[str, float] = {}

    def initialize(self) -> None:
        # Inicializa contadores nativos (FPS, Frame Time, Memória, Draw Calls)
        self.register_counter("fps", category="CPU", unit="FPS")
        self.register_counter("frame_time", category="CPU", unit="ms")
        self.register_counter("memory_heap", category="Memory", unit="MB")
        self.register_counter("draw_calls", category="GPU", unit="Calls")

    def shutdown(self) -> None:
        self._counters.clear()
        self._scope_times.clear()

    def measure(self, scope_name: str) -> DiagnosticScope:
        """Retorna um gerenciador de contexto para medição de subsistemas."""
        return DiagnosticScope(self, scope_name)

    def record_scope_time(self, scope_name: str, elapsed_ms: float) -> None:
        self._scope_times[scope_name] = elapsed_ms
        self.record_counter(f"scope.{scope_name}", elapsed_ms)

    def get_scope_time(self, scope_name: str) -> float:
        return self._scope_times.get(scope_name, 0.0)

    def register_counter(self, name: str, category: str = "General", unit: str = "") -> PerformanceCounter:
        if name not in self._counters:
            self._counters[name] = PerformanceCounter(name, category, unit)
        return self._counters[name]

    def record_counter(self, name: str, value: float) -> None:
        if name not in self._counters:
            self.register_counter(name)
        self._counters[name].record(value)

    def get_counter(self, name: str) -> Optional[PerformanceCounter]:
        return self._counters.get(name)

    def get_all_counters(self) -> Dict[str, PerformanceCounter]:
        return self._counters

    def get_summary(self) -> Dict[str, float]:
        summary = {name: c.current_value for name, c in self._counters.items()}
        summary.update(self._scope_times)
        return summary
