"""Data-output evaluation for Logic Graph runtime nodes."""
from __future__ import annotations

import random
from copy import deepcopy
from typing import Any, Mapping


def evaluate_output(
    runtime: Any,
    node_id: str,
    port: str,
    game: Any,
    dt: float,
    resolving: set[tuple[str, str]],
) -> Any:
    key = (node_id, port)
    if key in runtime.values:
        return runtime.values[key]
    if key in resolving:
        node = runtime.nodes.get(node_id, {})
        raise RuntimeError(f"Ciclo de dados detectado no nó '{node.get('title', node_id)}'.")
    node = runtime.nodes.get(node_id)
    if node is None:
        raise RuntimeError(f"Origem de dados não encontrada: {node_id}")
    if node_id not in runtime.executed_nodes:
        runtime.executed_nodes.append(node_id)
    resolving = set(resolving)
    resolving.add(key)
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
    node_type = str(node.get("type", ""))

    if node_type:
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.node import NodeDefinition
        from .registry import registry
        
        context = EngineContext.current()
        if context:
            manager = context.services.get_optional(MetadataManager)
            if manager:
                node_def = manager.get(NodeDefinition, node_type)
                if node_def and node_def.evaluator:
                    value = node_def.evaluator(runtime, node_id, port, node, game, dt, resolving)
                    return runtime._store(node_id, port, value)
                    
        # Fallback for isolated tests
        evaluator = registry.evaluators.get(node_type)
        if evaluator:
            value = evaluator(runtime, node_id, port, node, game, dt, resolving)
            return runtime._store(node_id, port, value)

    value = runtime.values.get(node_id, properties.get(port))
    return runtime._store(node_id, port, value)

