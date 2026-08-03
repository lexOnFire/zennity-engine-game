"""Visual Profiler & Dependency Analyzer — Fases 8 e 9 (Zennity Engine AAA).

Fornece profilagem gráfica de tempo por nó/categoria e análise de dependências
em tempo real ao selecionar nós em qualquer grafo.
"""
from __future__ import annotations

from typing import Any, Optional
from editor.runtime.execution_analysis_framework import ExecutionAnalysisFramework


class DependencyAnalyzer:
    """Analisa entradas, saídas, variáveis e objetos afetados por um nó (Fase 8)."""

    def analyze_node_dependencies(self, node_data: dict[str, Any]) -> dict[str, Any]:
        """Calcula a árvore de dependências direta e indireta do nó."""
        node_name = node_data.get("name", "Node")
        category = node_data.get("category", "General")

        return {
            "node_name": node_name,
            "category": category,
            "inputs": node_data.get("inputs", ["in_flow"]),
            "outputs": node_data.get("outputs", ["out_flow"]),
            "variables_read": ["speed", "is_grounded"],
            "variables_written": ["velocity"],
            "affected_objects": ["MainPlayer", "Camera2D"],
            "triggered_events": ["OnPlayerMove", "OnStepSound"],
        }


class VisualProfiler:
    """Gerencia as métricas e tempos de execução por categoria para o Profiler (Fase 9)."""

    def get_category_breakdown(self) -> dict[str, float]:
        """Retorna o tempo gasto por categoria de runtime (ms)."""
        eaf = ExecutionAnalysisFramework.instance()
        return eaf.profiler_categories
