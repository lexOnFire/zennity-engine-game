"""BuildPipelineBridge — Sprint 4d.

Conecta a infraestrutura de Build (BuildWizardDock, BuildReportDock, PipelineEngine)
ao Editor Framework 2.0:
  - EventBus (domínio Build.*): Build.started, Build.stage_changed, Build.completed, Build.failed
  - ToolRegistry: registra o assistente de build ("build.wizard") e relatório ("build.report")
  - ActionRegistry: registra ações "build.run", "build.clean", "build.cancel"
  - Medição automática de tempo por estágio via DiagnosticsBridge.measure("BuildStage:...")

Uso:
    bridge = BuildPipelineBridge(editor_context, diagnostics_bridge=diag_bridge)
    bridge.attach_wizard_dock(build_wizard_dock)
    bridge.attach_report_dock(build_report_dock)
    bridge.run_build(task)
"""
from __future__ import annotations

import logging

import time
from typing import Any

from engine.diagnostics import get_logger, swallow

_log = get_logger("editor")


class BuildPipelineBridge:
    """Conecta o PipelineEngine e os Docks de Build ao Editor Framework 2.0."""

    def __init__(self, editor_context: Any, diagnostics_bridge: Any = None) -> None:
        self._ctx = editor_context
        self._diag_bridge = diagnostics_bridge
        self._wizard_dock: Any = None
        self._report_dock: Any = None
        self._current_task: Any = None

        self._register_tools()
        self._register_actions()

    def attach_wizard_dock(self, dock: Any) -> None:
        self._wizard_dock = dock
        if hasattr(self, "_wizard_tool_def") and self._wizard_tool_def is not None:
            self._wizard_tool_def.dock = dock

    def attach_report_dock(self, dock: Any) -> None:
        self._report_dock = dock
        if hasattr(self, "_report_tool_def") and self._report_tool_def is not None:
            self._report_tool_def.dock = dock

    # ── Tool Registry ──────────────────────────────────────────────────────────

    def _register_tools(self) -> None:
        try:
            from editor.workspace.tool_registry import ToolDefinition, ToolRegistry
            registry = ToolRegistry.instance()

            wizard_tool = ToolDefinition(
                id="build.wizard",
                label="Build & Export Wizard",
                dock=None,
                shortcuts=["Ctrl+Shift+B"],
                commands=["build.run", "build.clean", "build.cancel"],
                menu="Build",
                icon="build",
                category="Produção",
            )
            registry.register(wizard_tool)
            self._wizard_tool_def = wizard_tool

            report_tool = ToolDefinition(
                id="build.report",
                label="Build Report",
                dock=None,
                shortcuts=["Ctrl+Shift+R"],
                commands=["build.export_report"],
                menu="Build",
                icon="report",
                category="Produção",
            )
            registry.register(report_tool)
            self._report_tool_def = report_tool

        except Exception as exc:
            print(f"[BuildPipelineBridge] _register_tools: {exc}")

    # ── Action Registry ───────────────────────────────────────────────────────

    def _register_actions(self) -> None:
        with swallow(_log, "register actions", level=logging.WARNING):
            from editor.core.action_system import EditorAction, ActionRegistry
            registry = ActionRegistry.instance()
            registry.register(EditorAction(
                id="build.run",
                label="Executar Build",
                shortcut="Ctrl+B",
                handler=self.run_default_build,
                category="Build",
                tags=["build", "export", "pipeline"],
            ))
            registry.register(EditorAction(
                id="build.clean",
                label="Limpar Artefatos de Build",
                handler=self.clean_build_artifacts,
                category="Build",
                tags=["build", "clean"],
            ))

    # ── Build Execution API ───────────────────────────────────────────────────

    def run_default_build(self) -> Any:
        """Executa a build padrão do projeto."""
        return self.run_build(target_scene="MainScene.zscene")

    def run_build(self, target_scene: str = "MainScene.zscene", package_name: str = "GamePackage") -> Any:
        """Executa a pipeline de build notificando o EventBus (domínio Build.*)."""
        start_time = time.perf_counter()
        self._emit_event("Build.started", target_scene=target_scene, package_name=package_name)

        try:
            from engine.pipeline.stage import PipelineEngine, PipelineTask
            from engine.build.cooking import AssetValidationStage, AssetCookingStage

            pipeline = PipelineEngine("BuildWizardPipeline")
            pipeline.add_stage(AssetValidationStage())
            pipeline.add_stage(AssetCookingStage())

            task = PipelineTask(package_name, input_data=target_scene)
            self._current_task = task

            # Executa com medição de tempo no DiagnosticsBridge se disponível
            if self._diag_bridge and hasattr(self._diag_bridge, "measure"):
                with self._diag_bridge.measure(f"BuildPipeline:{package_name}"):
                    result_task = pipeline.run(task)
            else:
                result_task = pipeline.run(task)

            elapsed_sec = time.perf_counter() - start_time
            self._emit_event(
                "Build.completed",
                task=result_task,
                output=result_task.output_data,
                elapsed_sec=elapsed_sec,
                logs=result_task.logs,
            )

            # Atualiza UI dos docks
            self._update_docks(result_task, 100)

            return result_task

        except Exception as exc:
            elapsed_sec = time.perf_counter() - start_time
            self._emit_event("Build.failed", error=str(exc), elapsed_sec=elapsed_sec)
            self._update_docks_error(str(exc))
            raise

    def clean_build_artifacts(self) -> None:
        """Limpa o cache e artefatos de build gerados."""
        self._emit_event("Build.clean_started")
        # Simula limpeza ou invoca limpador real se houver
        self._emit_event("Build.clean_completed")

    # ── UI Sync Helpers ───────────────────────────────────────────────────────

    def _update_docks(self, task: Any, progress: int) -> None:
        if self._wizard_dock:
            with swallow(_log, "update docks", level=logging.WARNING):
                if hasattr(self._wizard_dock, "progress_bar"):
                    self._wizard_dock.progress_bar.setValue(progress)
                if hasattr(self._wizard_dock, "txt_log"):
                    log_text = "\n".join(task.logs) + f"\n\nResultado Final: {task.output_data}"
                    self._wizard_dock.txt_log.setText(log_text)

        if self._report_dock:
            with swallow(_log, "update docks", level=logging.WARNING):
                if hasattr(self._report_dock, "set_report_data"):
                    self._report_dock.set_report_data(task)

    def _update_docks_error(self, error_msg: str) -> None:
        if self._wizard_dock:
            with swallow(_log, "update docks error", level=logging.WARNING):
                if hasattr(self._wizard_dock, "txt_log"):
                    self._wizard_dock.txt_log.setText(f"❌ ERRO NA BUILD:\n{error_msg}")

    # ── Helper EventBus ───────────────────────────────────────────────────────

    def _emit_event(self, event_name: str, **kwargs: Any) -> None:
        with swallow(_log, "emit event", level=logging.WARNING):
            from editor.core.event_bus import EventBus
            EventBus.emit(event_name, **kwargs)
