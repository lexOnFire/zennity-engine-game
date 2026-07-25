"""Executador de Grafos (GraphExecutor) da Zennity Engine.

Serviço de Runtime (IService) responsável por avaliar instruções compiladas de grafos.
Reutilizado por Behavior Tree, Dialogue Graph, Visual Scripting e Material Graph.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from engine.core.services import IService
from engine.core.lifecycle import ServiceScope
from engine.graph.runtime.compiler import CompiledGraph, CompiledGraphInstruction


class GraphExecutionContext:
    def __init__(self, target: Any = None, blackboard: Optional[dict] = None) -> None:
        self.target = target
        self.blackboard: dict = blackboard or {}
        self.node_outputs: dict[str, dict[str, Any]] = {}


class GraphExecutor(IService):
    """Serviço unificado de execução de grafos em tempo de jogo."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def execute_graph(self, graph: CompiledGraph, context: Optional[GraphExecutionContext] = None) -> Any:
        """Executa sequencialmente o grafo compilado."""
        if context is None:
            context = GraphExecutionContext()

        curr_id = graph.entry_node_id
        last_result = None

        while curr_id and curr_id in graph.instructions_by_id:
            inst = graph.instructions_by_id[curr_id]
            last_result = self.execute_instruction(inst, context)
            
            # Próxima instrução por fluxo de execução
            next_id = inst.outputs.get("out") or inst.outputs.get("next")
            curr_id = str(next_id) if next_id else ""

        return last_result

    def execute_instruction(self, inst: CompiledGraphInstruction, context: GraphExecutionContext) -> Any:
        """Avalia uma instrução de nó individual."""
        # Se for um nó matemático ou constante, armazena no contexto
        if "math" in inst.node_type or "color" in inst.node_type:
            val = inst.inputs.get("value", 0.0)
            context.node_outputs[inst.node_id] = {"output": val}
            return val

        return True
