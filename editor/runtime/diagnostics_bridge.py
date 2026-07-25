"""DiagnosticsBridge — Sprint 4d.

Conecta o ProfilerDock ao Editor Framework 2.0:
  - EventBus (domínio Runtime.*): emite métricas de performance como eventos
  - ToolRegistry: registra o Profiler como ferramenta ativa
  - ActionRegistry: expõe ações "diagnostics.reset", "diagnostics.export"
  - DiagnosticsService da engine: integração bidirecional

A integração chave é:
    with diagnostics_bridge.measure("AssetCooking"):
        pipeline.run(task)
    → emite Runtime.log com o tempo medido

Uso:
    bridge = DiagnosticsBridge(editor_context)
    bridge.attach_dock(profiler_dock)
    bridge.attach_diagnostics_service(diag_service)  # opcional
"""
from __future__ import annotations

import time
from typing import Any


class DiagnosticsBridge:
    """Conecta o ProfilerDock ao Editor Framework 2.0."""

    def __init__(self, editor_context: Any) -> None:
        self._ctx = editor_context
        self._dock: Any = None
        self._diag_service: Any = None
        self._scope_stack: list[tuple[str, float]] = []

        self._register_tool()
        self._register_actions()

    def attach_dock(self, dock: Any) -> None:
        self._dock = dock
        if self._tool_def is not None:
            self._tool_def.dock = dock

    def attach_diagnostics_service(self, service: Any) -> None:
        """Injeta o DiagnosticsService da engine para acesso bidirecional."""
        self._diag_service = service

    # ── Tool Registry ──────────────────────────────────────────────────────────

    def _register_tool(self) -> None:
        try:
            from editor.workspace.tool_registry import ToolDefinition, ToolRegistry
            tool = ToolDefinition(
                id="diagnostics.profiler",
                label="Profiler Visual",
                dock=None,
                shortcuts=["Ctrl+Shift+P"],
                commands=["diagnostics.reset", "diagnostics.export",
                          "diagnostics.measure", "diagnostics.snapshot"],
                menu="Ferramentas",
                icon="profiler",
                category="Debug",
            )
            ToolRegistry.instance().register(tool)
            self._tool_def = tool
        except Exception as exc:
            print(f"[DiagnosticsBridge] _register_tool: {exc}")
            self._tool_def = None

    # ── Action Registry ───────────────────────────────────────────────────────

    def _register_actions(self) -> None:
        try:
            from editor.core.action_system import EditorAction, ActionRegistry
            registry = ActionRegistry.instance()
            registry.register(EditorAction(
                id="diagnostics.reset",
                label="Resetar Contadores",
                shortcut="",
                handler=self.reset_counters,
                category="Debug",
                tags=["diagnostics", "profiler", "reset"],
            ))
            registry.register(EditorAction(
                id="diagnostics.export",
                label="Exportar Relatório",
                shortcut="",
                handler=self.export_report,
                category="Debug",
                tags=["diagnostics", "export", "report"],
            ))
        except Exception:
            pass

    # ── DiagnosticScope API (integração com pipeline) ─────────────────────────

    class _MeasureContext:
        """Context manager para medir tempo de qualquer bloco de código."""
        def __init__(self, bridge: Any, scope_name: str) -> None:
            self._bridge = bridge
            self._name = scope_name
            self._start: float = 0.0

        def __enter__(self) -> "_MeasureContext":
            self._start = time.perf_counter()
            return self

        def __exit__(self, *_: Any) -> None:
            elapsed_ms = (time.perf_counter() - self._start) * 1000.0
            self._bridge._on_scope_completed(self._name, elapsed_ms)

    def measure(self, scope_name: str) -> "_MeasureContext":
        """Mede o tempo de execução de um bloco e emite Runtime.log.

        Uso:
            with bridge.measure("AssetCooking"):
                pipeline.run(task)
        """
        return self._MeasureContext(self, scope_name)

    def _on_scope_completed(self, scope_name: str, elapsed_ms: float) -> None:
        """Emite Runtime.log com métricas e registra no DiagnosticsService."""
        try:
            from editor.core.event_bus import EventBus, EVENT_RUNTIME_LOG
            EventBus.emit(
                EVENT_RUNTIME_LOG,
                scope=scope_name,
                elapsed_ms=elapsed_ms,
                message=f"[Diagnostics] {scope_name}: {elapsed_ms:.2f}ms",
            )
        except Exception:
            pass

        if self._diag_service is not None:
            try:
                self._diag_service.record_scope_time(scope_name, elapsed_ms)
            except Exception:
                pass

    # ── Counter API ───────────────────────────────────────────────────────────

    def record(self, counter_name: str, value: float, unit: str = "") -> None:
        """Registra um valor em um contador de performance."""
        if self._diag_service is not None:
            try:
                counter = self._diag_service.get_or_create_counter(counter_name, unit=unit)
                counter.record(value)
            except Exception:
                pass
        try:
            from editor.core.event_bus import EventBus, EVENT_RUNTIME_LOG
            EventBus.emit(EVENT_RUNTIME_LOG, counter=counter_name,
                          value=value, unit=unit)
        except Exception:
            pass

    def snapshot(self) -> dict:
        """Tira um snapshot de todos os contadores atuais."""
        if self._diag_service is None:
            return {}
        try:
            counters = getattr(self._diag_service, "_counters", {})
            return {
                name: {
                    "current": c.current_value,
                    "unit": getattr(c, "unit", ""),
                    "history_len": len(getattr(c, "history", [])),
                }
                for name, c in counters.items()
            }
        except Exception:
            return {}

    def reset_counters(self) -> None:
        """Reseta todos os contadores — ação registrada no ActionRegistry."""
        if self._diag_service is not None:
            try:
                for c in getattr(self._diag_service, "_counters", {}).values():
                    c.history.clear()
                    c.current_value = 0.0
            except Exception:
                pass
        try:
            from editor.core.event_bus import EventBus, EVENT_RUNTIME_LOG
            EventBus.emit(EVENT_RUNTIME_LOG, message="[Diagnostics] Contadores resetados")
        except Exception:
            pass

    def export_report(self) -> dict:
        """Exporta snapshot completo como dicionário."""
        report = self.snapshot()
        try:
            from editor.core.event_bus import EventBus, EVENT_RUNTIME_LOG
            EventBus.emit(EVENT_RUNTIME_LOG, message="[Diagnostics] Relatório exportado",
                          report=report)
        except Exception:
            pass
        return report
