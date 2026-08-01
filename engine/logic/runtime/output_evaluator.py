"""Data-output evaluation for Logic Graph runtime nodes."""
from __future__ import annotations

import random
from copy import deepcopy
from typing import Any, Mapping

from .registry import registry


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

    if node_type in {"event_collision_enter", "event_collision_exit", "event_trigger_enter", "event_trigger_exit"}:
        # Referências de objetos do Play Mode não podem ser copiadas: elas
        # carregam o mundo e a fila de eventos do processo da viewport.
        value = runtime.values.get((node_id, "other"))
    elif node_type == "subgraph_input":
        value = deepcopy(runtime.values.get((node_id, "value"), properties.get("default")))
    elif node_type == "call_subgraph":
        value = deepcopy(runtime.values.get((node_id, port)))
    elif node_type == "event_custom":
        value = deepcopy(runtime.values.get((node_id, "payload")))
    elif node_type == "input_axis":
        negative = str(properties.get("negative", "A")).lower()
        positive = str(properties.get("positive", "D")).lower()
        value = float(game.axis(negative, positive))
        runtime.values["axis"] = value
    elif node_type == "key_pressed":
        value = bool(game.key_pressed(str(properties.get("key", "space")).lower()))
    elif node_type == "key_held":
        value = bool(game.key(str(properties.get("key", "space")).lower()))
    elif node_type == "is_grounded":
        value = bool(game.grounded)
    elif node_type == "compare_number":
        left = runtime._read_input(node_id, "value", runtime.values.get("axis", 0.0), game, dt, resolving)
        value = runtime._compare(left, properties.get("operator", ">"), properties.get("value", 0.0))
    elif node_type == "compare_text":
        left = runtime._read_input(node_id, "value", "", game, dt, resolving)
        right = str(properties.get("value", ""))
        operator = str(properties.get("operator", "=="))
        equal = str(left).casefold() == right.casefold()
        value = not equal if operator == "!=" else equal
    elif node_type == "and":
        left = bool(runtime._read_input(node_id, "a", False, game, dt, resolving))
        right = bool(runtime._read_input(node_id, "b", False, game, dt, resolving))
        value = left and right
    elif node_type == "or":
        left = bool(runtime._read_input(node_id, "a", False, game, dt, resolving))
        right = bool(runtime._read_input(node_id, "b", False, game, dt, resolving))
        value = left or right
    elif node_type == "not":
        value = not bool(runtime._read_input(node_id, "value", False, game, dt, resolving))
    elif node_type in {"add_number", "subtract_number", "multiply_number", "divide_number"}:
        left = float(runtime._read_input(node_id, "a", properties.get("a", 0.0), game, dt, resolving))
        right = float(runtime._read_input(node_id, "b", properties.get("b", 0.0), game, dt, resolving))
        if node_type == "add_number":
            value = left + right
        elif node_type == "subtract_number":
            value = left - right
        elif node_type == "multiply_number":
            value = left * right
        else:
            if right == 0.0:
                raise RuntimeError("Divisão por zero.")
            value = left / right
    elif node_type == "absolute_number":
        value = abs(float(runtime._read_input(node_id, "value", properties.get("value", 0.0), game, dt, resolving)))
    elif node_type == "clamp_number":
        raw = float(runtime._read_input(node_id, "value", properties.get("value", 0.0), game, dt, resolving))
        minimum = float(runtime._read_input(node_id, "minimum", properties.get("minimum", 0.0), game, dt, resolving))
        maximum = float(runtime._read_input(node_id, "maximum", properties.get("maximum", 1.0), game, dt, resolving))
        if minimum > maximum:
            minimum, maximum = maximum, minimum
        value = max(minimum, min(maximum, raw))
    elif node_type == "random_number":
        minimum = float(runtime._read_input(node_id, "minimum", properties.get("minimum", 0.0), game, dt, resolving))
        maximum = float(runtime._read_input(node_id, "maximum", properties.get("maximum", 1.0), game, dt, resolving))
        value = random.uniform(minimum, maximum)
    elif node_type == "delta_time":
        value = float(dt)
    elif node_type == "join_text":
        left = runtime._read_input(node_id, "a", properties.get("a", ""), game, dt, resolving)
        right = runtime._read_input(node_id, "b", properties.get("b", ""), game, dt, resolving)
        value = f"{left}{right}"
    elif node_type == "to_text":
        value = str(runtime._read_input(node_id, "value", properties.get("value", ""), game, dt, resolving))
    elif node_type == "get_variable":
        value = runtime.blackboard.get(
            str(properties.get("scope", "object")).lower(),
            str(properties.get("name", "value")),
            runtime.object_key,
        )
    elif node_type in {"number_value", "bool_value", "text_value"}:
        value = deepcopy(properties.get("value"))
    elif node_type == "self_object":
        value = game
    elif node_type == "get_position":
        target = runtime._read_target(node_id, game, dt, resolving)
        value = float(target.x if port == "x" else target.y)
    elif node_type == "find_tag":
        value = game.find(str(properties.get("tag", "Player")))
    elif node_type == "get_tag":
        target = runtime._read_target(node_id, game, dt, resolving)
        value = str(getattr(target, "tag", "Untagged"))
    elif node_type == "get_prefab_parameter":
        target = runtime._read_target(node_id, game, dt, resolving)
        getter = getattr(target, "prefab_parameter", None)
        name = str(properties.get("name", "speed"))
        value = getter(name, properties.get("default")) if callable(getter) else properties.get("default")
    elif node_type in {"create_object", "create_prefab", "clone_object"}:
        value = runtime.values.get((node_id, "object"))
    elif node_type == "if_else":
        raw = runtime._read_input(node_id, "condition", properties.get("condition", False), game, dt, resolving)
        value = runtime._condition(raw)
    else:
        evaluator = registry.evaluators.get(node_type)
        if evaluator:
            value = evaluator(runtime, node_id, port, node, game, dt, resolving)
        else:
            value = runtime.values.get(node_id, properties.get(port))
    return runtime._store(node_id, port, value)

