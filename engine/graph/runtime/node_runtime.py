"""Interface Abstrata de Execução de Nó (GraphNodeRuntime) da Zennity Engine.

Desacopla o GraphExecutor dos tipos concretos de nós de IA, Diálogo, Materiais e Visual Scripting.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from engine.graph.runtime.compiler import CompiledGraphInstruction


class GraphNodeRuntime(ABC):
    """Classe base para executadores de runtime de nós individuais."""

    @abstractmethod
    def execute(self, instruction: CompiledGraphInstruction, context: Any) -> Any:
        """Executa a lógica específica do nó e retorna o resultado."""
        pass
