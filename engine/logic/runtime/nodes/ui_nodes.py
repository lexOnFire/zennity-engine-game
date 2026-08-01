"""Nós de manipulação de UI e HUD no Logic Graph (set_ui_text, set_ui_progress_bar, set_ui_visible, bind_ui_property)."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


def _input(runtime: Any, node_id: str, port: str, default: Any, game: Any, dt: float) -> Any:
    reader = getattr(runtime, "_read_input", None)
    if callable(reader):
        return reader(node_id, port, default, game, dt, set())
    evaluator = getattr(runtime, "_evaluate_input")
    value = evaluator(node_id, port, game, dt, set())
    return default if value is None else value


@registry.register_executor('set_ui_text')
def execute_set_ui_text(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Define o texto de um elemento de UI (UILabel / LabelComponent)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    text_val = str(_input(runtime, node_id, "text", properties.get("text", ""), game, dt))
    object_name = str(properties.get("object", properties.get("object_name", ""))).strip()

    if object_name and callable(getattr(game, "set_ui_text", None)):
        game.set_ui_text(object_name, text_val)
        return ["next"]

    target = runtime._read_target(node_id, game, dt, set())

    if target is not None:
        if hasattr(target, "text"):
            target.text = text_val
        elif hasattr(target, "set_text"):
            target.set_text(text_val)
        else:
            comp = target.get_component("Label") or target.get_component("LabelComponent") or target.get_component("UILabel")
            if comp is not None and hasattr(comp, "text"):
                comp.text = text_val

    return ["next"]


@registry.register_executor('set_ui_progress_bar')
def execute_set_ui_progress_bar(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Define o valor de uma barra de progresso de UI (ProgressBar)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    value_val = float(_input(runtime, node_id, "value", properties.get("value", 0.0), game, dt))
    maximum = float(properties.get("max_value", 100.0))
    object_name = str(properties.get("object", properties.get("object_name", ""))).strip()

    if object_name and callable(getattr(game, "set_ui_progress", None)):
        game.set_ui_progress(object_name, value_val, maximum)
        return ["next"]

    target = runtime._read_target(node_id, game, dt, set())

    if target is not None:
        if hasattr(target, "set_value"):
            target.set_value(value_val)
        elif hasattr(target, "value"):
            target.value = value_val
        else:
            comp = target.get_component("ProgressBar")
            if comp is not None:
                if hasattr(comp, "set_value"):
                    comp.set_value(value_val)
                elif hasattr(comp, "value"):
                    comp.value = value_val

    return ["next"]


@registry.register_executor('set_ui_visible')
def execute_set_ui_visible(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Alterna a visibilidade de um elemento de UI."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    target = runtime._read_target(node_id, game, dt, set())
    visible_val = bool(runtime._evaluate_input(node_id, "visible", game, dt, set()) if "visible" in node.get("inputs", {}) else properties.get("visible", True))

    if target is not None:
        if hasattr(target, "visible"):
            target.visible = visible_val
        if hasattr(target, "get_component"):
            comp = target.get_component("UIElement")
            if comp is not None:
                comp.visible = visible_val


    return ["next"]


@registry.register_executor('bind_ui_to_blackboard')
def execute_bind_ui_to_blackboard(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Vincula uma propriedade de um elemento de UI a uma chave do Blackboard."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    target = runtime._read_target(node_id, game, dt, set())
    widget_prop = str(properties.get("widget_property", "value"))
    bb_key = str(properties.get("blackboard_key", ""))

    if target is not None and bb_key and hasattr(runtime, "blackboard"):
        from engine.ui.data_binding import UIDataBindingManager
        UIDataBindingManager.instance().bind(
            widget=target,
            widget_property=widget_prop,
            blackboard_key=bb_key,
            blackboard=runtime.blackboard,
        )

    return ["next"]
