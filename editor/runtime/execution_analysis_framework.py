"""Execution Analysis Framework (EAF) — Fase 1 (Zennity Engine AAA).

Infraestrutura compartilhada de rastreamento de execução, métricas e profilagem
utilizada por TODOS os editores de grafos da engine:
  - Visual Scripting
  - Behavior Tree
  - Animation Graph
  - Dialogue Graph
  - Material Graph
"""
from __future__ import annotations

import time
from typing import Any, Optional
from editor.core.event_bus import EventBus


class ExecutionAnalysisFramework:
    """Singleton unificado de análise de execução para todos os editores de grafos."""

    _instance: Optional[ExecutionAnalysisFramework] = None

    def __init__(self) -> None:
        self.node_metrics: dict[str, dict[str, Any]] = {}
        self.execution_history: list[dict[str, Any]] = []
        self.profiler_categories: dict[str, float] = {
            "physics": 1.2,
            "scripts": 2.4,
            "animation": 0.8,
            "audio": 0.3,
            "rendering": 3.1,
        }

    @classmethod
    def instance(cls) -> ExecutionAnalysisFramework:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_node_execution(self, graph_type: str, node_id: str, node_name: str, exec_time_ms: float = 0.5) -> None:
        """Registra a execução de um nó em qualquer grafo da engine."""
        if node_id not in self.node_metrics:
            self.node_metrics[node_id] = {
                "name": node_name,
                "graph_type": graph_type,
                "count": 0,
                "total_time_ms": 0.0,
                "max_time_ms": 0.0,
                "avg_time_ms": 0.0,
            }

        m = self.node_metrics[node_id]
        m["count"] += 1
        m["total_time_ms"] += exec_time_ms
        m["max_time_ms"] = max(m["max_time_ms"], exec_time_ms)
        m["avg_time_ms"] = m["total_time_ms"] / m["count"]

        entry = {
            "timestamp": time.time(),
            "graph_type": graph_type,
            "node_id": node_id,
            "node_name": node_name,
            "exec_time_ms": exec_time_ms,
        }
        self.execution_history.append(entry)

        # Emite via Barramento de Eventos
        EventBus.emit("EAF.node_executed", graph_type=graph_type, node_id=node_id, metrics=m)

    def get_heatmap_color(self, node_id: str) -> str:
        """Retorna a cor térmica (#HEX) para o nó conforme a contagem de execuções."""
        count = self.node_metrics.get(node_id, {}).get("count", 0)
        if count < 5:
            return "#4c9aff"  # Azul (Frio)
        elif count < 15:
            return "#50c878"  # Verde
        elif count < 30:
            return "#ffe600"  # Amarelo
        elif count < 50:
            return "#ff9933"  # Laranja
        else:
            return "#ff4d4d"  # Vermelho (Gargalo)
