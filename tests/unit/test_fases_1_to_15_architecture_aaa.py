"""Suíte de Testes da Arquitetura AAA — Fases 1 a 15 (Execution Analysis Framework & Profiler).

Valida o EAF compartilhado, Visual Profiler, Dependency Analyzer e compatibilidade total.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_execution_analysis_framework_recording():
    """Valida o registro de execuções no Execution Analysis Framework (Fase 1)."""
    from editor.runtime.execution_analysis_framework import ExecutionAnalysisFramework

    eaf = ExecutionAnalysisFramework.instance()
    eaf.record_node_execution("VisualScripting", "n_move_1", "Move", exec_time_ms=0.8)
    eaf.record_node_execution("BehaviorTree", "n_bt_patrol", "PatrolTask", exec_time_ms=1.2)

    assert "n_move_1" in eaf.node_metrics
    assert eaf.node_metrics["n_move_1"]["count"] >= 1
    assert eaf.get_heatmap_color("n_move_1") == "#4c9aff"


def test_dependency_analyzer():
    """Valida a análise de dependências de nós no DependencyAnalyzer (Fase 8)."""
    from editor.runtime.visual_profiler import DependencyAnalyzer

    analyzer = DependencyAnalyzer()
    res = analyzer.analyze_node_dependencies({"name": "MovePlayer", "category": "Movement"})

    assert res["node_name"] == "MovePlayer"
    assert "velocity" in res["variables_written"]
    assert "MainPlayer" in res["affected_objects"]


def test_visual_profiler_breakdown():
    """Valida a profilagem por categoria no VisualProfiler (Fase 9)."""
    from editor.runtime.visual_profiler import VisualProfiler

    profiler = VisualProfiler()
    breakdown = profiler.get_category_breakdown()

    assert "physics" in breakdown
    assert "scripts" in breakdown
    assert breakdown["physics"] > 0.0


def test_visual_scripting_dock_profiler_tab(qapp):
    """Valida a presença da aba Visual Profiler no VisualScriptingEditorDock."""
    from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock

    dock = VisualScriptingEditorDock()
    assert hasattr(dock, "profiler_text")
    assert dock.watches_tabs.count() >= 3
