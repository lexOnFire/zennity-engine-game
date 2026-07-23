from __future__ import annotations
from typing import Any, Mapping
from copy import deepcopy
from ..registry import registry

@registry.register_executor('set_hud')
def execute_set_hud(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    text = runtime._read_input(node_id, "text", properties.get("text", "Texto"), game, dt, set())
    game.set_hud(f"logic:{node_id}", str(text))
    return ["next"]

@registry.register_executor('emit_event')
def execute_emit_event(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    name = str(properties.get("name", "evento")).strip()
    payload = runtime._read_input(node_id, "payload", properties.get("payload"), game, dt, set())
    runtime.event_bus.emit(name, payload, runtime.object_key)
    return ["next"]

@registry.register_executor('call_subgraph')
def execute_call_subgraph(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    path = str(properties.get("path", "")).strip()
    if not path or runtime.subgraph_loader is None:
        raise RuntimeError("Subgrafo não configurado.")
    identity = path.casefold()
    if identity in runtime.call_stack:
        chain = " → ".join((*runtime.call_stack, identity))
        raise RuntimeError(f"Referência circular entre subgrafos: {chain}")
    graph = runtime.subgraph_loader(path)
    declared_inputs = properties.get("inputs", []) if isinstance(properties.get("inputs"), list) else []
    input_values: dict[str, Any] = {}
    for definition in declared_inputs:
        if not isinstance(definition, Mapping):
            continue
        name = str(definition.get("name", "")).strip()
        if name:
            input_values[name] = runtime._read_input(
                node_id, name, definition.get("default"), game, dt, set()
            )
    from engine.logic.runtime.core import LogicGraphRuntime
    child = LogicGraphRuntime(
        graph,
        runtime.blackboard,
        runtime.object_key,
        runtime.event_bus,
        runtime.subgraph_loader,
        (*runtime.call_stack, identity),
    )
    outputs = child.run_subgraph(game, dt, input_values)
    for name, value in outputs.items():
        runtime._store(node_id, str(name), value)
    return ["next"]

@registry.register_executor('subgraph_return')
def execute_subgraph_return(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    name = str(properties.get("name", "resultado")).strip()
    value = runtime._read_input(node_id, "value", properties.get("default"), game, dt, set())
    runtime._subgraph_outputs[name] = deepcopy(value)
    runtime._store(node_id, "value", value)
    return []

@registry.register_executor('set_variable')
def execute_set_variable(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    name = str(properties.get("name", "value"))
    scope = str(properties.get("scope", "object")).lower()
    value = runtime._read_input(node_id, "value", properties.get("value"), game, dt, set())
    value = runtime.blackboard.set(scope, name, value, runtime.object_key)
    runtime.variables = runtime.blackboard.values_for_object(runtime.object_key)
    if scope != "object":
        # ``variables`` predates scoped blackboards and remains a public debug
        # view of values written by the graph.
        runtime.variables[name] = deepcopy(value)
    runtime._store(node_id, "value", value)
    return ["next"]

@registry.register_executor('get_variable')
def execute_get_variable(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    runtime._evaluate_output(node_id, "value", game, dt, set())
    return ["next"]

@registry.register_executor('sequence')
def execute_sequence(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    outputs = max(1, int(properties.get("outputs", 2)))
    return [f"then_{index}" for index in range(outputs)] + ["next"]

@registry.register_evaluator(('event_collision_enter', 'event_collision_exit', 'event_trigger_enter', 'event_trigger_exit'))
def evaluate_event_collision_enter_or_event_collision_exit_or_event_trigger_enter_or_event_trigger_exit(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = runtime.values.get((node_id, "other"))
    return value

@registry.register_evaluator('subgraph_input')
def evaluate_subgraph_input(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = deepcopy(runtime.values.get((node_id, "value"), properties.get("default")))
    return value

@registry.register_evaluator('call_subgraph')
def evaluate_call_subgraph(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = deepcopy(runtime.values.get((node_id, port)))
    return value

@registry.register_evaluator('event_custom')
def evaluate_event_custom(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = deepcopy(runtime.values.get((node_id, "payload")))
    return value

@registry.register_evaluator('and')
def evaluate_and(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    left = bool(runtime._read_input(node_id, "a", False, game, dt, branch))
    right = bool(runtime._read_input(node_id, "b", False, game, dt, branch))
    value = left and right
    return value

@registry.register_evaluator('or')
def evaluate_or(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    left = bool(runtime._read_input(node_id, "a", False, game, dt, branch))
    right = bool(runtime._read_input(node_id, "b", False, game, dt, branch))
    value = left or right
    return value

@registry.register_evaluator('not')
def evaluate_not(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = not bool(runtime._read_input(node_id, "value", False, game, dt, branch))
    return value

@registry.register_evaluator('get_variable')
def evaluate_get_variable(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = runtime.blackboard.get(
        str(properties.get("scope", "object")).lower(),
        str(properties.get("name", "value")),
        runtime.object_key,
    )
    return value

@registry.register_evaluator(('number_value', 'bool_value', 'text_value'))
def evaluate_number_value_or_bool_value_or_text_value(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = deepcopy(properties.get("value"))
    return value

@registry.register_evaluator('self_object')
def evaluate_self_object(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = game
    return value

@registry.register_evaluator('find_tag')
def evaluate_find_tag(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = game.find(str(properties.get("tag", "Player")))
    return value

