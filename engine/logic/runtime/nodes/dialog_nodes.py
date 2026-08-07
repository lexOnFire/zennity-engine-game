"""Nós de diálogo para Logic Graph - Sistema de diálogo visual 100%."""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('show_dialog')
def execute_show_dialog(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Mostra um diálogo com opções para o player escolher."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))
        character = str(properties.get("character", "NPC"))
        text = str(properties.get("text", "Olá!"))
        options = properties.get("options", [])  # Lista de opções

        # Armazenar diálogo ativo
        if not hasattr(runtime, "_active_dialog"):
            runtime._active_dialog = {}

        runtime._active_dialog[dialog_id] = {
            "character": character,
            "text": text,
            "options": options,
            "chosen": False,
            "choice_index": -1
        }

        runtime._store(node_id, "dialog_id", dialog_id)
        runtime._store(node_id, "is_showing", True)

        return ["showing"]
    except Exception as e:
        print(f"Erro em show_dialog: {e}")
        return ["failure"]


@registry.register_executor('wait_dialog_choice')
def execute_wait_dialog_choice(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Aguarda o player escolher uma opção de diálogo."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))

        if not hasattr(runtime, "_active_dialog"):
            return ["failure"]

        dialog = runtime._active_dialog.get(dialog_id)
        if not dialog:
            return ["failure"]

        # Se player escolheu
        if dialog.get("chosen"):
            choice_index = dialog.get("choice_index", -1)
            runtime._store(node_id, "choice_index", choice_index)
            runtime._store(node_id, "chosen_text", dialog["options"][choice_index] if choice_index >= 0 else "")

            # Limpar diálogo
            del runtime._active_dialog[dialog_id]
            return ["chosen"]
        else:
            return ["waiting"]

    except Exception as e:
        print(f"Erro em wait_dialog_choice: {e}")
        return ["failure"]


@registry.register_executor('set_dialog_choice')
def execute_set_dialog_choice(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Define a escolha do player no diálogo (usado internamente)."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))
        choice_index = int(properties.get("choice_index", 0))

        if hasattr(runtime, "_active_dialog") and dialog_id in runtime._active_dialog:
            runtime._active_dialog[dialog_id]["chosen"] = True
            runtime._active_dialog[dialog_id]["choice_index"] = choice_index
            return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro em set_dialog_choice: {e}")
        return ["failure"]


@registry.register_executor('close_dialog')
def execute_close_dialog(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Fecha o diálogo ativo."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))

        if hasattr(runtime, "_active_dialog") and dialog_id in runtime._active_dialog:
            del runtime._active_dialog[dialog_id]
            return ["success"]

        return ["success"]  # OK mesmo se não existe
    except Exception as e:
        print(f"Erro em close_dialog: {e}")
        return ["failure"]
