"""Data-output evaluation for Logic Graph runtime nodes."""

from __future__ import annotations

import random
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

_UNHANDLED = object()


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
    context = (runtime, node_id, port, game, dt, resolving, properties, node_type)
    for evaluator in (
        _evaluate_event_and_input,
        _evaluate_logic,
        _evaluate_math_and_text,
        _evaluate_object,
    ):
        value = evaluator(*context)
        if value is not _UNHANDLED:
            return runtime._store(node_id, port, value)
    return runtime._store(node_id, port, runtime.values.get(node_id, properties.get(port)))


def _evaluate_event_and_input(
    runtime: Any, node_id: str, port: str, game: Any, dt: float,
    resolving: set[tuple[str, str]], properties: Mapping[str, Any], node_type: str,
) -> Any:
    if node_type in {
        "event_collision_enter", "event_collision_exit",
        "event_trigger_enter", "event_trigger_exit",
    }:
        return runtime.values.get((node_id, "other"))
    if node_type == "subgraph_input":
        return deepcopy(runtime.values.get((node_id, "value"), properties.get("default")))
    if node_type == "call_subgraph":
        return deepcopy(runtime.values.get((node_id, port)))
    if node_type == "event_custom":
        return deepcopy(runtime.values.get((node_id, "payload")))
    if node_type == "input_axis":
        negative = str(properties.get("negative", "A")).lower()
        positive = str(properties.get("positive", "D")).lower()
        value = float(game.axis(negative, positive))
        runtime.values["axis"] = value
        return value
    if node_type == "key_pressed":
        return bool(game.key_pressed(str(properties.get("key", "space")).lower()))
    if node_type == "key_held":
        return bool(game.key(str(properties.get("key", "space")).lower()))
    if node_type == "is_grounded":
        return bool(game.grounded)
    if node_type == "delta_time":
        return float(dt)
    return _UNHANDLED


def _evaluate_logic(
    runtime: Any, node_id: str, _port: str, game: Any, dt: float,
    resolving: set[tuple[str, str]], properties: Mapping[str, Any], node_type: str,
) -> Any:
    if node_type == "compare_number":
        left = runtime._read_input(
            node_id, "value", runtime.values.get("axis", 0.0), game, dt, resolving
        )
        return runtime._compare(left, properties.get("operator", ">"), properties.get("value", 0.0))
    if node_type == "compare_text":
        left = runtime._read_input(node_id, "value", "", game, dt, resolving)
        right = str(properties.get("value", ""))
        equal = str(left).casefold() == right.casefold()
        return not equal if str(properties.get("operator", "==")) == "!=" else equal
    if node_type in {"and", "or"}:
        left = bool(runtime._read_input(node_id, "a", False, game, dt, resolving))
        right = bool(runtime._read_input(node_id, "b", False, game, dt, resolving))
        return left and right if node_type == "and" else left or right
    if node_type == "not":
        return not bool(runtime._read_input(node_id, "value", False, game, dt, resolving))
    if node_type == "if_else":
        raw = runtime._read_input(
            node_id, "condition", properties.get("condition", False), game, dt, resolving
        )
        return runtime._condition(raw)
    return _UNHANDLED


def _evaluate_math_and_text(
    runtime: Any, node_id: str, _port: str, game: Any, dt: float,
    resolving: set[tuple[str, str]], properties: Mapping[str, Any], node_type: str,
) -> Any:
    if node_type in {"add_number", "subtract_number", "multiply_number", "divide_number"}:
        left = float(runtime._read_input(node_id, "a", properties.get("a", 0.0), game, dt, resolving))
        right = float(runtime._read_input(node_id, "b", properties.get("b", 0.0), game, dt, resolving))
        return _arithmetic(node_type, left, right)
    if node_type == "absolute_number":
        return abs(float(runtime._read_input(
            node_id, "value", properties.get("value", 0.0), game, dt, resolving
        )))
    if node_type == "clamp_number":
        raw = float(runtime._read_input(
            node_id, "value", properties.get("value", 0.0), game, dt, resolving
        ))
        minimum = float(runtime._read_input(
            node_id, "minimum", properties.get("minimum", 0.0), game, dt, resolving
        ))
        maximum = float(runtime._read_input(
            node_id, "maximum", properties.get("maximum", 1.0), game, dt, resolving
        ))
        if minimum > maximum:
            minimum, maximum = maximum, minimum
        return max(minimum, min(maximum, raw))
    if node_type == "random_number":
        minimum = float(runtime._read_input(
            node_id, "minimum", properties.get("minimum", 0.0), game, dt, resolving
        ))
        maximum = float(runtime._read_input(
            node_id, "maximum", properties.get("maximum", 1.0), game, dt, resolving
        ))
        return random.uniform(minimum, maximum)
    if node_type == "join_text":
        left = runtime._read_input(node_id, "a", properties.get("a", ""), game, dt, resolving)
        right = runtime._read_input(node_id, "b", properties.get("b", ""), game, dt, resolving)
        return f"{left}{right}"
    if node_type == "to_text":
        return str(runtime._read_input(
            node_id, "value", properties.get("value", ""), game, dt, resolving
        ))
    return _UNHANDLED


def _arithmetic(node_type: str, left: float, right: float) -> float:
    if node_type == "add_number":
        return left + right
    if node_type == "subtract_number":
        return left - right
    if node_type == "multiply_number":
        return left * right
    if right == 0.0:
        raise RuntimeError("Divisão por zero.")
    return left / right


def _evaluate_object(
    runtime: Any, node_id: str, port: str, game: Any, dt: float,
    resolving: set[tuple[str, str]], properties: Mapping[str, Any], node_type: str,
) -> Any:
    if node_type == "get_variable":
        return runtime.blackboard.get(
            str(properties.get("scope", "object")).lower(),
            str(properties.get("name", "value")),
            runtime.object_key,
        )
    if node_type in {"number_value", "bool_value", "text_value"}:
        return deepcopy(properties.get("value"))
    if node_type == "self_object":
        return game
    if node_type == "get_position":
        target = runtime._read_target(node_id, game, dt, resolving)
        return float(target.x if port == "x" else target.y)
    if node_type == "find_tag":
        return game.find(str(properties.get("tag", "Player")))
    if node_type == "get_tag":
        target = runtime._read_target(node_id, game, dt, resolving)
        return str(getattr(target, "tag", "Untagged"))
    if node_type == "get_prefab_parameter":
        target = runtime._read_target(node_id, game, dt, resolving)
        getter = getattr(target, "prefab_parameter", None)
        name = str(properties.get("name", "speed"))
        return getter(name, properties.get("default")) if callable(getter) else properties.get("default")
    if node_type in {"create_object", "create_prefab", "clone_object"}:
        return runtime.values.get((node_id, "object"))
    return _UNHANDLED
