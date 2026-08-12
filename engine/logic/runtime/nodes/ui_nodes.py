"""Nós de manipulação de UI e HUD no Logic Graph (set_ui_text, set_ui_progress_bar, set_ui_visible, bind_ui_property)."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry

# BUG FIX: this module used to call target.get_component("Label"),
# .get_component("ProgressBar") and .get_component("UIElement") with plain
# strings. GameObject.get_component() does `isinstance(comp, component_type)`
# internally, so passing a string instead of the actual class raised
# `TypeError: isinstance() arg 2 must be a type...` every time this fallback
# path executed (whenever a set_ui_text/set_ui_progress_bar/set_ui_visible
# node's "object" property was left empty) — the exception then propagates
# out of _execute() and aborts the whole Logic Graph. Import the real classes
# instead.
try:
    from engine.ui.runtime_components import LabelComponent, ProgressBarComponent, RuntimeUIElement
except ModuleNotFoundError:
    # Runtime autocontido criado pelo exportador (engine/build/project_exporter.py)
    # não empacota engine.ui.runtime_components (ela subclassa o Component
    # completo da engine, que o build exportado não inclui -- o jogo exportado
    # usa editor/runtime/native_ui.py, um sistema de UI baseado em dicts).
    # Placeholders mantêm o import seguro; os nodes de UI viram no-op nesse
    # runtime em vez de derrubar o jogo inteiro na inicialização.
    class RuntimeUIElement:  # type: ignore[no-redef]
        pass

    class LabelComponent(RuntimeUIElement):  # type: ignore[no-redef]
        pass

    class ProgressBarComponent(RuntimeUIElement):  # type: ignore[no-redef]
        pass


def _find_widget(target: Any, component_type: type, widget_name: str) -> Any:
    """Resolve QUAL componente de UI usar quando `target` tem vários do
    mesmo tipo (ex.: GameObject "HUD" com duas LabelComponent — título e
    contador de moedas). Sem isso, get_component() sempre pegava o primeiro
    da lista, então um Logic Graph não conseguia atualizar especificamente
    a segunda Label/ProgressBar de um HUD composto.

    Se `widget_name` for informado (propriedade "widget"/"widget_name" no
    nó), procura entre TODOS os componentes desse tipo o que tiver
    `.widget_name` igual. Caso contrário — ou se nenhum bater — cai no
    comportamento antigo (primeiro componente do tipo), preservando
    compatibilidade com cenas/nós existentes que não usam widget_name.
    """
    if target is None or not hasattr(target, "get_components"):
        return target.get_component(component_type) if target is not None else None

    candidates = target.get_components(component_type)
    if widget_name:
        for comp in candidates:
            if str(getattr(comp, "widget_name", "")) == widget_name:
                return comp
    return candidates[0] if candidates else None


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
    widget_name = str(properties.get("widget", properties.get("widget_name", ""))).strip()

    if target is not None:
        if hasattr(target, "text") and not widget_name:
            target.text = text_val
        elif hasattr(target, "set_text") and not widget_name:
            target.set_text(text_val)
        else:
            comp = _find_widget(target, LabelComponent, widget_name)
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
    widget_name = str(properties.get("widget", properties.get("widget_name", ""))).strip()

    if target is not None:
        if hasattr(target, "set_value") and not widget_name:
            target.set_value(value_val)
        elif hasattr(target, "value") and not widget_name:
            target.value = value_val
        else:
            comp = _find_widget(target, ProgressBarComponent, widget_name)
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
    widget_name = str(properties.get("widget", properties.get("widget_name", ""))).strip()

    if target is not None:
        if hasattr(target, "visible") and not widget_name:
            target.visible = visible_val
        if hasattr(target, "get_components"):
            comp = _find_widget(target, RuntimeUIElement, widget_name)
            if comp is not None:
                comp.visible = visible_val

    return ["exec_done"]


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

    return ["exec_done"]
