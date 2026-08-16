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
    if hasattr(runtime, "data_evaluated_nodes") and node_id not in runtime.data_evaluated_nodes:
        runtime.data_evaluated_nodes.append(node_id)
    if hasattr(runtime, "_record_trace"):
        runtime._record_trace("data_evaluated", node_id=node_id, port=port)
    resolving = set(resolving)
    resolving.add(key)
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
    node_type = str(node.get("type", ""))

    if node_type:
        from .registry import registry

        # The MetadataManager is the editor's lookup: LogicProvider.boot() mirrors
        # every evaluator onto it so the inspector can introspect nodes.  It is
        # optional, not primary -- there is no EngineContext in a pytest process
        # and none in the standalone runtime the exporter produces, where
        # engine.core is not shipped at all.  Hence the guarded import.
        try:
            from engine.core.context import EngineContext
            from engine.core.metadata.node import NodeDefinition
            from engine.metadata.manager import MetadataManager
        except ImportError:  # Self-contained exported runtime.
            pass
        else:
            context = EngineContext.current()
            if context:
                manager = context.services.get_optional(MetadataManager)
                if manager:
                    node_def = manager.get(NodeDefinition, node_type)
                    if node_def and node_def.evaluator:
                        value = node_def.evaluator(runtime, node_id, port, node, game, dt, resolving)
                        return runtime._store(node_id, port, value)

        # The decorator registry is the canonical source, not a test-only
        # fallback: it is what @registry.register_evaluator populates at import
        # time, and it is the only evaluator lookup an exported game has.
        evaluator = registry.evaluators.get(node_type)
        if evaluator:
            value = evaluator(runtime, node_id, port, node, game, dt, resolving)
            return runtime._store(node_id, port, value)

    value = runtime.values.get(node_id, properties.get(port))
    return runtime._store(node_id, port, value)

