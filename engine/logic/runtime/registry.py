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
        # Phase 9.5B Stage 2: every module that ever claimed a node id, so that
        # two modules fighting over the same node is a detectable CI failure
        # instead of a silent last-write-wins.
        self.executor_owners: dict[str, set[str]] = {}
        self.evaluator_owners: dict[str, set[str]] = {}

    @staticmethod
    def _owner(func: Any) -> str:
        return str(getattr(func, "__module__", "") or "<unknown>")

    def register_executor(self, node_types: str | tuple[str, ...]) -> Callable[[ExecutorFunc], ExecutorFunc]:
        """Registra uma função como executora de fluxo injetando no MetadataManager via EngineContext."""
        def decorator(func: ExecutorFunc) -> ExecutorFunc:
            types = (node_types,) if isinstance(node_types, str) else node_types
            for t in types:
                self.executors[t] = func
                self.executor_owners.setdefault(t, set()).add(self._owner(func))
            return func
        return decorator

    def register_evaluator(self, node_types: str | tuple[str, ...]) -> Callable[[EvaluatorFunc], EvaluatorFunc]:
        """Registra uma função como avaliadora injetando no MetadataManager via EngineContext."""
        def decorator(func: EvaluatorFunc) -> EvaluatorFunc:
            types = (node_types,) if isinstance(node_types, str) else node_types
            for t in types:
                self.evaluators[t] = func
                self.evaluator_owners.setdefault(t, set()).add(self._owner(func))
            return func
        return decorator

    def duplicate_owners(self) -> dict[str, list[str]]:
        """Node ids claimed by more than one implementing module."""
        duplicates: dict[str, list[str]] = {}
        for node_id, owners in self.executor_owners.items():
            if len(owners) > 1:
                duplicates[f"executor:{node_id}"] = sorted(owners)
        for node_id, owners in self.evaluator_owners.items():
            if len(owners) > 1:
                duplicates[f"evaluator:{node_id}"] = sorted(owners)
        return duplicates

registry = NodeRegistry()

def sync_logic_registry_to_metadata(context) -> None:
    from engine.metadata.manager import MetadataManager
    from engine.core.metadata import NodeDefinition
    
    manager = context.services.get_optional(MetadataManager)
    manager = context.services.get_optional(MetadataManager)
    if not manager:
        return
        
    for type_id, func in registry.executors.items():
        node_def = manager.get(NodeDefinition, type_id)
        if not node_def:
            node_def = NodeDefinition(id=type_id, title_key=type_id)
            manager.register(node_def)
            print(f"Registered executor {type_id}")
        node_def.executor = func
            
    for type_id, func in registry.evaluators.items():
        node_def = manager.get(NodeDefinition, type_id)
        if not node_def:
            node_def = NodeDefinition(id=type_id, title_key=type_id)
            manager.register(node_def)
            print(f"Registered evaluator {type_id}")
        node_def.evaluator = func
