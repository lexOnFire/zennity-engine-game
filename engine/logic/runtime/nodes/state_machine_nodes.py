"""Nós de state machine para Logic Graph - State Machine 100% visual."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('create_state_machine')
def execute_create_state_machine(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Cria uma nova state machine."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        machine_id = str(properties.get("machine_id", f"sm_{node_id}"))
        initial_state = str(properties.get("initial_state", "idle"))

        if not hasattr(runtime, "_state_machines"):
            runtime._state_machines = {}

        runtime._state_machines[machine_id] = {
            "current_state": initial_state,
            "previous_state": None,
            "transitions": {},
            "state_timers": {}
        }

        runtime._store(node_id, "machine_id", machine_id)
        runtime._store(node_id, "current_state", initial_state)

        return ["exec_created"]
    except Exception as e:
        print(f"Erro em create_state_machine: {e}")
        return ["exec_failure"]


@registry.register_executor('add_transition')
def execute_add_transition(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Adiciona uma transição entre estados."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        machine_id = str(properties.get("machine_id", ""))
        from_state = str(properties.get("from_state", ""))
        to_state = str(properties.get("to_state", ""))
        condition = str(properties.get("condition", "always"))  # always, on_key, on_event

        if not hasattr(runtime, "_state_machines"):
            return ["exec_failure"]

        if machine_id not in runtime._state_machines:
            return ["exec_failure"]

        machine = runtime._state_machines[machine_id]
        if from_state not in machine["transitions"]:
            machine["transitions"][from_state] = []

        machine["transitions"][from_state].append({
            "target": to_state,
            "condition": condition
        })

        return ["next"]
    except Exception as e:
        print(f"Erro em add_transition: {e}")
        return ["exec_failure"]


@registry.register_executor('change_state')
def execute_change_state(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Muda o estado atual."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        machine_id = str(properties.get("machine_id", ""))
        new_state = str(properties.get("state", ""))
        force = bool(properties.get("force", False))  # Ignorar verificação de transição?

        if not hasattr(runtime, "_state_machines"):
            return ["exec_failure"]

        if machine_id not in runtime._state_machines:
            return ["exec_failure"]

        machine = runtime._state_machines[machine_id]
        current = machine["current_state"]

        # Verificar se transição é válida (exceto se force=true)
        if not force:
            transitions = machine["transitions"].get(current, [])
            valid = any(t["target"] == new_state for t in transitions)
            if not valid:
                return ["exec_invalid_transition"]

        # Fazer transição
        machine["previous_state"] = current
        machine["current_state"] = new_state
        runtime._store(node_id, "previous_state", current)
        runtime._store(node_id, "new_state", new_state)

        return ["exec_changed"]
    except Exception as e:
        print(f"Erro em change_state: {e}")
        return ["exec_failure"]


@registry.register_executor('get_state')
def execute_get_state(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Retorna o estado atual."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        machine_id = str(properties.get("machine_id", ""))

        if not hasattr(runtime, "_state_machines"):
            return ["exec_failure"]

        if machine_id not in runtime._state_machines:
            return ["exec_failure"]

        current_state = runtime._state_machines[machine_id]["current_state"]
        runtime._store(node_id, "state", current_state)

        return ["exec_got_state"]
    except Exception as e:
        print(f"Erro em get_state: {e}")
        return ["exec_failure"]


@registry.register_executor('is_in_state')
def execute_is_in_state(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Verifica se está em um estado específico."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        machine_id = str(properties.get("machine_id", ""))
        state = str(properties.get("state", ""))

        if not hasattr(runtime, "_state_machines"):
            return ["exec_not_in_state"]

        if machine_id not in runtime._state_machines:
            return ["exec_not_in_state"]

        current_state = runtime._state_machines[machine_id]["current_state"]

        if current_state == state:
            return ["exec_in_state"]
        else:
            return ["exec_not_in_state"]
    except Exception as e:
        print(f"Erro em is_in_state: {e}")
        return ["exec_failure"]
