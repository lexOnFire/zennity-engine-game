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


class DiagnosticsService(IService):
    """Serviço central de coleta e telemetria da Zennity Engine."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self._counters: Dict[str, PerformanceCounter] = {}

    def initialize(self) -> None:
        # Inicializa contadores nativos (FPS, Frame Time, Memória, Draw Calls)
        self.register_counter("fps", category="CPU", unit="FPS")
        self.register_counter("frame_time", category="CPU", unit="ms")
        self.register_counter("memory_heap", category="Memory", unit="MB")
        self.register_counter("draw_calls", category="GPU", unit="Calls")

    def shutdown(self) -> None:
        self._counters.clear()

    def register_counter(self, name: str, category: str = "General", unit: str = "") -> PerformanceCounter:
        if name not in self._counters:
            self._counters[name] = PerformanceCounter(name, category, unit)
        return self._counters[name]

    def record_counter(self, name: str, value: float) -> None:
        if name in self._counters:
            self._counters[name].record(value)

    def get_counter(self, name: str) -> Optional[PerformanceCounter]:
        return self._counters.get(name)

    def get_all_counters(self) -> Dict[str, PerformanceCounter]:
        return self._counters

    def get_summary(self) -> Dict[str, float]:
        return {name: c.current_value for name, c in self._counters.items()}
