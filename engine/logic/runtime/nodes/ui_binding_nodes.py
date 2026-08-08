"""Sistema de auto-binding: UI widgets vinculam automaticamente a variáveis."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('bind_ui_to_variable')
def execute_bind_ui_to_variable(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Vincula um widget UI a uma variável automaticamente."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        widget_name = str(properties.get("widget_name", ""))
        variable_name = str(properties.get("variable_name", widget_name))  # padrão: mesmo nome
        property_to_bind = str(properties.get("property", "value"))  # padrão: "value"

        if not widget_name or not variable_name:
            return ["failure"]

        # Procurar o widget
        widget = None
        if hasattr(game, "find"):
            widget = game.find(widget_name)

        if not widget:
            return ["not_found"]

        # Ler a propriedade do widget
        if hasattr(widget, property_to_bind):
            value = getattr(widget, property_to_bind)
            # Salvar na variável
            runtime.set_variable(variable_name, value)
            print(f"✓ Auto-bind: {widget_name}.{property_to_bind} → variável '{variable_name}' = {value}")
            return ["success"]

        return ["property_not_found"]

    except Exception as e:
        print(f"Erro em bind_ui_to_variable: {e}")
        return ["failure"]


@registry.register_executor('update_ui_binding')
def execute_update_ui_binding(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Atualiza o binding de um widget (sincroniza valor com variável)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        widget_name = str(properties.get("widget_name", ""))
        variable_name = str(properties.get("variable_name", widget_name))
        property_to_sync = str(properties.get("property", "value"))

        if not widget_name or not variable_name:
            return ["failure"]

        # Procurar widget
        widget = None
        if hasattr(game, "find"):
            widget = game.find(widget_name)

        if not widget:
            return ["not_found"]

        # Sincronizar: ler do widget, salvar na variável
        if hasattr(widget, property_to_sync):
            value = getattr(widget, property_to_sync)
            runtime.set_variable(variable_name, value)
            return ["success"]

        return ["property_not_found"]

    except Exception as e:
        print(f"Erro em update_ui_binding: {e}")
        return ["failure"]
