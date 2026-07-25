"""Testes unitários do Sprint 4d — Diagnostics, Extensions e Build Pipeline integrados.

Valida:
  - DiagnosticsBridge: registra 'diagnostics.profiler' no ToolRegistry, mede tempo com context manager e gera eventos
  - ExtensionsBridge: registra 'extensions.manager' no ToolRegistry, gerencia e recarrega extensões
  - BuildPipelineBridge: executa pipeline, integra medição com Diagnostics, emite eventos Build.* e atualiza UI
  - Orchestrator: inicializa os 9 bridges com sucesso
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Fakes & Helpers
# ─────────────────────────────────────────────────────────────────────────────

class FakeEditorContext:
    def __init__(self):
        from editor.runtime.selection_manager import SelectionService
        self.selection = SelectionService()


class FakeDiagnosticsService:
    def __init__(self):
        self._counters = {}
        self.scopes_recorded = []

    def get_or_create_counter(self, name: str, unit: str = ""):
        if name not in self._counters:
            from engine.diagnostics.service import PerformanceCounter
            self._counters[name] = PerformanceCounter(name, unit=unit)
        return self._counters[name]

    def record_scope_time(self, scope_name: str, elapsed_ms: float):
        self.scopes_recorded.append((scope_name, elapsed_ms))


class FakeWizardDock:
    def __init__(self):
        self.progress_value = 0
        self.log_text = ""

    class _Bar:
        def __init__(self, outer):
            self.outer = outer
        def setValue(self, val):
            self.outer.progress_value = val

    class _Log:
        def __init__(self, outer):
            self.outer = outer
        def setText(self, text):
            self.outer.log_text = text

    @property
    def progress_bar(self):
        return self._Bar(self)

    @property
    def txt_log(self):
        return self._Log(self)


# ─────────────────────────────────────────────────────────────────────────────
# DiagnosticsBridge
# ─────────────────────────────────────────────────────────────────────────────

def test_diagnostics_bridge_registers_tool():
    """DiagnosticsBridge registra 'diagnostics.profiler' no ToolRegistry."""
    from editor.runtime.diagnostics_bridge import DiagnosticsBridge
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    bridge = DiagnosticsBridge(ctx)

    tool = ToolRegistry.instance().get("diagnostics.profiler")
    assert tool is not None
    assert tool.id == "diagnostics.profiler"
    assert "diagnostics.reset" in tool.commands
    assert "Ctrl+Shift+P" in tool.shortcuts


def test_diagnostics_bridge_measure_context():
    """DiagnosticsBridge.measure() mede tempo de execução e emite eventos."""
    from editor.runtime.diagnostics_bridge import DiagnosticsBridge
    from editor.core.event_bus import EventBus

    ctx = FakeEditorContext()
    diag_svc = FakeDiagnosticsService()
    bridge = DiagnosticsBridge(ctx)
    bridge.attach_diagnostics_service(diag_svc)

    received = []
    EventBus.subscribe("Runtime.log", lambda **kw: received.append(kw))

    with bridge.measure("AssetCooking"):
        import time
        time.sleep(0.01)

    assert len(received) >= 1
    assert any(r.get("scope") == "AssetCooking" for r in received)
    assert len(diag_svc.scopes_recorded) == 1
    assert diag_svc.scopes_recorded[0][0] == "AssetCooking"


def test_diagnostics_bridge_reset_and_snapshot():
    """DiagnosticsBridge grava contadores e tira snapshot."""
    from editor.runtime.diagnostics_bridge import DiagnosticsBridge

    ctx = FakeEditorContext()
    diag_svc = FakeDiagnosticsService()
    bridge = DiagnosticsBridge(ctx)
    bridge.attach_diagnostics_service(diag_svc)

    bridge.record("fps", 60.0, unit="fps")
    snap = bridge.snapshot()

    assert "fps" in snap
    assert snap["fps"]["current"] == 60.0

    bridge.reset_counters()
    snap_after = bridge.snapshot()
    assert snap_after["fps"]["current"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# ExtensionsBridge
# ─────────────────────────────────────────────────────────────────────────────

def test_extensions_bridge_registers_tool():
    """ExtensionsBridge registra 'extensions.manager' no ToolRegistry."""
    from editor.runtime.extensions_bridge import ExtensionsBridge
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    bridge = ExtensionsBridge(ctx)

    tool = ToolRegistry.instance().get("extensions.manager")
    assert tool is not None
    assert tool.id == "extensions.manager"
    assert "extensions.reload" in tool.commands
    assert "Ctrl+Shift+E" in tool.shortcuts


def test_extensions_bridge_register_and_list():
    """ExtensionsBridge registra extensões e lista."""
    from editor.runtime.extensions_bridge import ExtensionsBridge

    ctx = FakeEditorContext()
    bridge = ExtensionsBridge(ctx)

    bridge.register_extension("my_plugin", {"name": "My Plugin"})
    exts = bridge.list_extensions()

    assert "my_plugin" in exts


# ─────────────────────────────────────────────────────────────────────────────
# BuildPipelineBridge
# ─────────────────────────────────────────────────────────────────────────────

def test_build_pipeline_bridge_registers_tools():
    """BuildPipelineBridge registra 'build.wizard' e 'build.report' no ToolRegistry."""
    from editor.runtime.build_pipeline_bridge import BuildPipelineBridge
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    bridge = BuildPipelineBridge(ctx)

    wizard_tool = ToolRegistry.instance().get("build.wizard")
    report_tool = ToolRegistry.instance().get("build.report")

    assert wizard_tool is not None
    assert report_tool is not None
    assert wizard_tool.id == "build.wizard"
    assert report_tool.id == "build.report"


def test_build_pipeline_bridge_run_build_events_and_ui():
    """BuildPipelineBridge executa build, emite eventos Build.* e atualiza UI Dock."""
    from editor.runtime.build_pipeline_bridge import BuildPipelineBridge
    from editor.runtime.diagnostics_bridge import DiagnosticsBridge
    from editor.core.event_bus import EventBus

    ctx = FakeEditorContext()
    diag_bridge = DiagnosticsBridge(ctx)
    build_bridge = BuildPipelineBridge(ctx, diagnostics_bridge=diag_bridge)

    dock = FakeWizardDock()
    build_bridge.attach_wizard_dock(dock)

    events = []
    EventBus.subscribe("Build.started", lambda **kw: events.append("started"))
    EventBus.subscribe("Build.completed", lambda **kw: events.append("completed"))

    result_task = build_bridge.run_build(target_scene="TestScene.zscene")

    assert "started" in events
    assert "completed" in events
    assert result_task is not None
    assert dock.progress_value == 100
    assert "Resultado Final" in dock.log_text


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator — Testes de Integração do Sprint 4d
# ─────────────────────────────────────────────────────────────────────────────

def test_orchestrator_creates_all_nine_bridges():
    """Orchestrator inicializa com sucesso todos os 9 bridges da suite 2.0."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    assert orchestrator.reactive is not None
    assert orchestrator.animation is not None
    assert orchestrator.visual_scripting is not None
    assert orchestrator.behavior_tree is not None
    assert orchestrator.dialogue is not None
    assert orchestrator.material_graph is not None
    assert orchestrator.diagnostics is not None
    assert orchestrator.extensions is not None
    assert orchestrator.build_pipeline is not None


def test_orchestrator_activates_sprint4d_tools():
    """Orchestrator possui métodos helper para ativar as ferramentas do Sprint 4d."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    orchestrator.activate_profiler()
    assert ToolRegistry.instance().active_tool.id == "diagnostics.profiler"

    orchestrator.activate_extensions()
    assert ToolRegistry.instance().active_tool.id == "extensions.manager"

    orchestrator.activate_build_wizard()
    assert ToolRegistry.instance().active_tool.id == "build.wizard"
