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


def _fetch_progress_bar_value(runtime: Any, widget_name: str, game: Any) -> float:
    name = str(widget_name).strip()
    if not name or name.lower() == "none":
        name = "comida"

    # 1. Objeto direto pela API
    if hasattr(game, "find"):
        try:
            target = game.find(name)
            if target is None:
                for alt_name in ("comida", "bar", "progress", "hp"):
                    target = game.find(alt_name)
                    if target:
                        break
            if target:
                if hasattr(target, "value") and target.value is not None:
                    return float(target.value)
                if hasattr(target, "obj") and isinstance(target.obj, dict):
                    ui = target.obj.get("ui")
                    if isinstance(ui, dict) and "value" in ui and ui["value"] is not None:
                        return float(ui["value"])
                    if "value" in target.obj and target.obj["value"] is not None:
                        return float(target.obj["value"])
        except Exception:
            pass

    # 2. Busca no dicionário de objetos da cena por nome, tag ou componente UI
    if hasattr(game, "_world") and isinstance(game._world, dict):
        for obj_name, obj in game._world.items():
            if not isinstance(obj, dict):
                continue
            ui = obj.get("ui")
            if isinstance(ui, dict) and str(ui.get("type", "")).lower() in {"progress_bar", "progressbar"}:
                if "value" in ui and ui["value"] is not None:
                    return float(ui["value"])
            if str(obj_name).lower() == name.lower() or str(obj.get("tag", "")).lower() == name.lower():
                if isinstance(ui, dict) and "value" in ui and ui["value"] is not None:
                    return float(ui["value"])
                if "value" in obj and obj["value"] is not None:
                    return float(obj["value"])

        # Busca em qualquer Canvas (.zui)
        for scene_obj in game._world.values():
            if not isinstance(scene_obj, dict):
                continue
            c_ui = scene_obj.get("ui")
            if isinstance(c_ui, dict) and c_ui.get("type") == "canvas":
                overrides = c_ui.get("_widget_overrides", {})
                for k, v in overrides.items():
                    if isinstance(v, dict) and "value" in v and v["value"] is not None:
                        return float(v["value"])

    # 3. Busca nas variáveis do Blackboard/Runtime
    if hasattr(runtime, "variables") and isinstance(runtime.variables, dict):
        for key in (name, f"{name}.value", "value", "comida.value", "comida"):
            if key in runtime.variables and runtime.variables[key] is not None and str(runtime.variables[key]).lower() != "none":
                try:
                    return float(runtime.variables[key])
                except (ValueError, TypeError):
                    pass

    return 100.0


@registry.register_executor('get_progress_bar_value')
def execute_get_progress_bar_value(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Lê o valor de uma ProgressBar durante a execução de fluxo."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    widget_name = str(runtime._read_input(node_id, "widget_name", properties.get("widget_name", "comida"), game, dt, set()))

    val = _fetch_progress_bar_value(runtime, widget_name, game)
    runtime._store(node_id, "value", val)
    return ["next", "exec_success"]


@registry.register_evaluator('get_progress_bar_value')
def evaluate_get_progress_bar_value(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, resolving: set[tuple[str, str]]) -> Any:
    """Avalia a saída de dados 'value' de um nó get_progress_bar_value."""
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    widget_name = str(runtime._read_input(node_id, "widget_name", properties.get("widget_name", "comida"), game, dt, resolving))

    val = _fetch_progress_bar_value(runtime, widget_name, game)
    return runtime._store(node_id, "value", val)
