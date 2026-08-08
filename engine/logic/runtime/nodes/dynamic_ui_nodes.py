"""Nós de UI Dinâmica para Logic Graph - criar/remover widgets em runtime 100% visualmente."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('create_ui_label')
def execute_create_ui_label(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Cria um Label dinâmico na UI em runtime."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        parent_name = str(properties.get("parent", ""))
        widget_name = str(properties.get("name", "label_dynamic"))
        text = str(properties.get("text", "Dynamic"))
        x = float(properties.get("x", 0.0))
        y = float(properties.get("y", 0.0))
        font_size = int(properties.get("font_size", 24))
        color = properties.get("color", [255, 255, 255])

        # Procura o parent na cena
        if parent_name and hasattr(game, "find_object"):
            parent = game.find_object(parent_name)
            if parent and hasattr(parent, "add_child"):
                # Criar novo Label
                from engine.ui.runtime import UILabel
                label = UILabel(name=widget_name)
                label.x = x
                label.y = y
                label.text = text
                label.font_size = font_size
                label.text_color = f"rgb({color[0]},{color[1]},{color[2]})"
                label.widget_name = widget_name

                parent.add_child(label)
                return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro ao criar label: {e}")
        return ["failure"]


@registry.register_executor('create_ui_progress_bar')
def execute_create_ui_progress_bar(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Cria uma ProgressBar dinâmica na UI em runtime."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        parent_name = str(properties.get("parent", ""))
        widget_name = str(properties.get("name", "progress_dynamic"))
        x = float(properties.get("x", 0.0))
        y = float(properties.get("y", 0.0))
        width = float(properties.get("width", 200.0))
        height = float(properties.get("height", 20.0))
        value = float(properties.get("value", 50.0))
        max_value = float(properties.get("max_value", 100.0))
        fill_color = properties.get("fill_color", [46, 204, 113])
        bg_color = properties.get("bg_color", [28, 35, 48])

        # Procura o parent na cena
        if parent_name and hasattr(game, "find_object"):
            parent = game.find_object(parent_name)
            if parent and hasattr(parent, "add_child"):
                # Criar novo ProgressBar
                from engine.ui.runtime import UIProgressBar
                progress = UIProgressBar(name=widget_name)
                progress.x = x
                progress.y = y
                progress.width = width
                progress.height = height
                progress.value = value
                progress.max_value = max_value
                progress.fill_color = f"rgb({fill_color[0]},{fill_color[1]},{fill_color[2]})"
                progress.bg_color = f"rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})"
                progress.widget_name = widget_name

                parent.add_child(progress)
                return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro ao criar progress bar: {e}")
        return ["failure"]


@registry.register_executor('create_ui_button')
def execute_create_ui_button(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Cria um Button dinâmico na UI em runtime."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        parent_name = str(properties.get("parent", ""))
        widget_name = str(properties.get("name", "button_dynamic"))
        text = str(properties.get("text", "Click Me"))
        x = float(properties.get("x", 0.0))
        y = float(properties.get("y", 0.0))
        width = float(properties.get("width", 120.0))
        height = float(properties.get("height", 40.0))

        # Procura o parent na cena
        if parent_name and hasattr(game, "find_object"):
            parent = game.find_object(parent_name)
            if parent and hasattr(parent, "add_child"):
                # Criar novo Button
                from engine.ui.runtime import UIButton
                button = UIButton(name=widget_name)
                button.x = x
                button.y = y
                button.width = width
                button.height = height
                button.text = text
                button.widget_name = widget_name

                parent.add_child(button)
                return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro ao criar botão: {e}")
        return ["failure"]


@registry.register_executor('create_ui_image')
def execute_create_ui_image(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Cria uma Image dinâmica na UI em runtime."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        parent_name = str(properties.get("parent", ""))
        widget_name = str(properties.get("name", "image_dynamic"))
        texture_path = str(properties.get("texture_path", ""))
        x = float(properties.get("x", 0.0))
        y = float(properties.get("y", 0.0))
        width = float(properties.get("width", 100.0))
        height = float(properties.get("height", 100.0))

        # Procura o parent na cena
        if parent_name and hasattr(game, "find_object"):
            parent = game.find_object(parent_name)
            if parent and hasattr(parent, "add_child"):
                # Criar nova Image
                from engine.ui.runtime import UIImage
                image = UIImage(name=widget_name)
                image.x = x
                image.y = y
                image.width = width
                image.height = height
                image.texture_path = texture_path
                image.widget_name = widget_name

                parent.add_child(image)
                return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro ao criar imagem: {e}")
        return ["failure"]


@registry.register_executor('destroy_ui_widget')
def execute_destroy_ui_widget(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Remove um widget da UI em runtime."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        parent_name = str(properties.get("parent", ""))
        widget_name = str(properties.get("widget_name", ""))

        # Procura o parent na cena
        if parent_name and hasattr(game, "find_object"):
            parent = game.find_object(parent_name)
            if parent and hasattr(parent, "children"):
                # Procura e remove o widget
                for child in parent.children[:]:  # cópia para iterar com segurança
                    if getattr(child, "widget_name", None) == widget_name or getattr(child, "name", None) == widget_name:
                        parent.remove_child(child)
                        return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro ao remover widget: {e}")
        return ["failure"]


@registry.register_executor('update_ui_widget_property')
def execute_update_ui_widget_property(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Atualiza uma propriedade de widget dinâmico."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        parent_name = str(properties.get("parent", ""))
        widget_name = str(properties.get("widget_name", ""))
        property_name = str(properties.get("property", ""))
        value = properties.get("value", "")

        # Procura o widget
        if parent_name and hasattr(game, "find_object"):
            parent = game.find_object(parent_name)
            if parent and hasattr(parent, "children"):
                for child in parent.children:
                    if getattr(child, "widget_name", None) == widget_name or getattr(child, "name", None) == widget_name:
                        if hasattr(child, property_name):
                            setattr(child, property_name, value)
                            return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro ao atualizar propriedade: {e}")
        return ["failure"]


@registry.register_executor('get_ui_widget_property')
def execute_get_ui_widget_property(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Lê uma propriedade de um widget."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        parent_name = str(properties.get("parent", ""))
        widget_name = str(properties.get("widget_name", ""))
        property_name = str(properties.get("property", ""))

        # Procura o widget
        if parent_name and hasattr(game, "find_object"):
            parent = game.find_object(parent_name)
            if parent and hasattr(parent, "children"):
                for child in parent.children:
                    if getattr(child, "widget_name", None) == widget_name or getattr(child, "name", None) == widget_name:
                        if hasattr(child, property_name):
                            value = getattr(child, property_name)
                            # Guardar valor em variável global
                            if hasattr(runtime, "set_parameter"):
                                runtime.set_parameter(f"{widget_name}_{property_name}", value)
                            return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro ao ler propriedade: {e}")
        return ["failure"]


@registry.register_executor('get_progress_bar_value')
def execute_get_progress_bar_value(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Lê o valor de uma ProgressBar."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        widget_name = str(properties.get("widget_name", ""))

        # Procura o widget em toda a cena
        if hasattr(game, "find_object"):
            widget = game.find_object(widget_name)
            if widget:
                # Tentar ler o valor
                if hasattr(widget, "value"):
                    value = float(widget.value)
                elif hasattr(widget, "text"):
                    try:
                        value = float(widget.text)
                    except:
                        value = 0.0
                else:
                    return ["failure"]

                runtime._store(node_id, "value", value)
                return ["success"]

        return ["not_found"]
    except Exception as e:
        print(f"Erro ao ler ProgressBar: {e}")
        return ["failure"]
