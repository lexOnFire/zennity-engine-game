from __future__ import annotations
import math
import random
from types import SimpleNamespace
from typing import Any, Mapping
from copy import deepcopy
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

# ``set_variable`` is implemented in scene_nodes, which wins by load order and
# is a strict superset of what lived here: identical blackboard write, plus the
# optional ``game.set_variable`` host hook that a public-contract test pins.
# Two executors for one node meant the losing body was dead code that still
# looked authoritative.

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

@registry.register_executor('find_tag')
def execute_find_tag(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Resolve o objeto e continua o fluxo.

    PHASE 9 recovery item 11 -- restaurado da linhagem Stage 1, que não é
    ancestral desta branch. O node declara pinos de fluxo ``in``/``next`` e só
    tinha evaluator: a cobertura o dava por atendido porque aceitava um
    evaluator para um ACTION, e a continuação só funcionava por acidente, pelo
    ``return ["next"]`` que ``_execute`` usa quando não há executor nenhum.

    Guardar o objeto aqui também evita resolver a mesma tag duas vezes quando a
    saída de dados é lida depois.
    """
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    runtime._store(node_id, "object", game.find(str(properties.get("tag", "Player"))))
    return ["next"]


@registry.register_evaluator('find_tag')
def evaluate_find_tag(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = game.find(str(properties.get("tag", "Player")))
    return value


def _world_objects(game: Any) -> Mapping[str, Any]:
    """The scene's objects as a mapping, however the host exposes them."""
    world = getattr(game, "_world", None)
    if not isinstance(world, Mapping):
        world = getattr(getattr(game, "runtime_world", None), "objects", None)
    return world if isinstance(world, Mapping) else {}


@registry.register_executor('find_nearest_object')
def execute_find_nearest_object(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Objeto mais próximo dentro de um raio, em qualquer direção.

    PHASE 9 recovery item 10 -- restaurado, não inventado. ``find_tag`` devolve a
    primeira correspondência e não a mais próxima, e um raycast só alcança o que
    estiver exatamente na linha do tiro; nenhum dos dois serve para um ataque
    corpo-a-corpo cercado por vários inimigos.

    A origem é o próprio objeto que executa, ele nunca escolhe a si mesmo, e um
    empate é resolvido pelo nome -- o original mantinha o primeiro encontrado, o
    que dependia da ordem do dicionário do mundo.
    """
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    wanted = str(runtime._read_input(node_id, "tag", properties.get("tag", ""), game, dt, set())).strip().lower()
    max_distance = float(runtime._read_input(node_id, "max_distance", properties.get("max_distance", 100.0), game, dt, set()))

    origin_x, origin_y = float(getattr(game, "x", 0.0)), float(getattr(game, "y", 0.0))
    own_name = str(getattr(game, "name", ""))

    nearest_name, nearest_distance = None, float("inf")
    for name, obj in sorted(_world_objects(game).items()):
        if not isinstance(obj, Mapping) or name == own_name or not obj.get("active", True):
            continue
        if wanted and wanted not in (
            str(obj.get("tag", "")).lower(), str(name).lower(), str(obj.get("name", "")).lower()
        ):
            continue
        distance = math.hypot(float(obj.get("x", 0.0)) - origin_x, float(obj.get("y", 0.0)) - origin_y)
        if distance <= max_distance and distance < nearest_distance:
            nearest_name, nearest_distance = name, distance

    if nearest_name is None:
        runtime._store(node_id, "object", None)
        runtime._store(node_id, "distance", 0.0)
        return ["exec_none"]

    # O resultado precisa expor ``.name``/``.tag`` para get_object_name e get_tag,
    # então nunca devolvemos a chave crua do mundo.
    found = None
    for accessor in ("find", "find_object"):
        resolver = getattr(game, accessor, None)
        if callable(resolver):
            found = resolver(nearest_name)
            if found is not None:
                break
    if found is None:
        source = _world_objects(game).get(nearest_name, {})
        found = SimpleNamespace(
            name=nearest_name,
            tag=str(source.get("tag", "Untagged")),
            x=float(source.get("x", 0.0)),
            y=float(source.get("y", 0.0)),
        )
    runtime._store(node_id, "object", found)
    runtime._store(node_id, "distance", nearest_distance)
    return ["exec_found"]


@registry.register_evaluator('find_nearest_object')
def evaluate_find_nearest_object(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    """The data pins the executor stored -- the same shape ``raycast`` uses."""
    return runtime.values.get((node_id, str(port)))
