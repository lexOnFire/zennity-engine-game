"""Sistema de auto-binding: UI widgets vinculam automaticamente a variáveis."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping
from ..registry import registry


def _fetch_widget_property(game: Any, widget_name: str, property_name: str) -> tuple[bool, Any]:
    if not widget_name:
        return False, None
    # 1. Objeto direto pela tag/nome (ex: "comida")
    target = game.find(widget_name) if hasattr(game, "find") else None
    if target and hasattr(target, "obj"):
        ui = target.obj.get("ui")
        if isinstance(ui, dict) and property_name in ui:
            return True, ui[property_name]
        if hasattr(target, property_name):
            return True, getattr(target, property_name)
        if isinstance(target.obj, dict) and property_name in target.obj:
            return True, target.obj[property_name]

    # 2. Widgets dentro de Canvas (.zui)
    if hasattr(game, "_world"):
        for scene_obj in game._world.values():
            if not isinstance(scene_obj, dict):
                continue
            c_ui = scene_obj.get("ui")
            if isinstance(c_ui, dict) and c_ui.get("type") == "canvas":
                overrides = c_ui.get("_widget_overrides", {})
                if widget_name in overrides and property_name in overrides[widget_name]:
                    return True, overrides[widget_name][property_name]

    return False, None


def _write_runtime_variable(runtime: Any, variable_name: str, value: Any) -> None:
    if hasattr(runtime, "blackboard"):
        runtime.blackboard.set("object", variable_name, value, runtime.object_key)
        runtime.variables = runtime.blackboard.values_for_object(runtime.object_key)
    if hasattr(runtime, "variables"):
        runtime.variables[variable_name] = deepcopy(value)


@registry.register_executor('bind_ui_to_variable')
def execute_bind_ui_to_variable(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Vincula um widget UI a uma variável automaticamente."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        widget_name = str(runtime._read_input(node_id, "widget_name", properties.get("widget_name", "comida"), game, dt, set()))
        variable_name = str(runtime._read_input(node_id, "variable_name", properties.get("variable_name", widget_name), game, dt, set()))
        property_name = str(runtime._read_input(node_id, "property", properties.get("property", "value"), game, dt, set()))

        found, val = _fetch_widget_property(game, widget_name, property_name)
        if not found:
            return ["exec_not_found"]

        _write_runtime_variable(runtime, variable_name, val)
        runtime._store(node_id, "value", val)
        return ["next"]

    except Exception as e:
        print(f"Erro em bind_ui_to_variable: {e}")
        return ["exec_failure"]


@registry.register_executor('update_ui_binding')
def execute_update_ui_binding(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Atualiza o binding de um widget (sincroniza valor com variável a cada frame)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        widget_name = str(runtime._read_input(node_id, "widget_name", properties.get("widget_name", "comida"), game, dt, set()))
        variable_name = str(runtime._read_input(node_id, "variable_name", properties.get("variable_name", widget_name), game, dt, set()))
        property_name = str(runtime._read_input(node_id, "property", properties.get("property", "value"), game, dt, set()))

        found, val = _fetch_widget_property(game, widget_name, property_name)
        if not found:
            return ["exec_not_found"]

        _write_runtime_variable(runtime, variable_name, val)
        runtime._store(node_id, "value", val)
        return ["next"]

    except Exception as e:
        print(f"Erro em update_ui_binding: {e}")
        return ["exec_failure"]

