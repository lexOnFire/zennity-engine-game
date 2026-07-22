from __future__ import annotations

from typing import Any, Callable, Mapping

# Tipos de assinatura para handlers
# (runtime: LogicGraphRuntime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]
ExecutorFunc = Callable[[Any, Mapping[str, Any], Any, float], list[str]]

# (runtime: LogicGraphRuntime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any
EvaluatorFunc = Callable[[Any, str, str, Mapping[str, Any], Any, float, set[str]], Any]


class NodeRegistry:
    def __init__(self) -> None:
        self.executors: dict[str, ExecutorFunc] = {}
        self.evaluators: dict[str, EvaluatorFunc] = {}

    def register_executor(self, node_types: str | tuple[str, ...]) -> Callable[[ExecutorFunc], ExecutorFunc]:
        """Registra uma função como executora de fluxo para os tipos de nós informados."""
        def decorator(func: ExecutorFunc) -> ExecutorFunc:
            if isinstance(node_types, str):
                self.executors[node_types] = func
            else:
                for t in node_types:
                    self.executors[t] = func
            return func
        return decorator

    def register_evaluator(self, node_types: str | tuple[str, ...]) -> Callable[[EvaluatorFunc], EvaluatorFunc]:
        """Registra uma função como avaliadora de valor (outputs) para os tipos de nós informados."""
        def decorator(func: EvaluatorFunc) -> EvaluatorFunc:
            if isinstance(node_types, str):
                self.evaluators[node_types] = func
            else:
                for t in node_types:
                    self.evaluators[t] = func
            return func
        return decorator


registry = NodeRegistry()
