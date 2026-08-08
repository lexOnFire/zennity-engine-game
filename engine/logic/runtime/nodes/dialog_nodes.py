"""
Phase 7B.7: Nós de diálogo para Logic Graph - Sistema de diálogo visual 100%.

Integração com DialogueSession (fonte canônica).
Semântica: Nodes delegam para DialogueManager → DialogueSession.
"""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry


def _get_dialogue_manager(game: Any) -> Any:
    """Get DialogueManager from PlayLogicAPI via game object."""
    if hasattr(game, "get_dialogue_manager"):
        return game.get_dialogue_manager()
    if hasattr(game, "_dialogue_manager"):
        return game._dialogue_manager
    return None


@registry.register_executor("show_dialog")
def execute_show_dialog(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Mostra um diálogo com opções para o player escolher.

    Delegado a DialogueManager (via PlayLogicAPI).
    """
    node_id = str(node["id"])
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))
        character = str(properties.get("character", "NPC"))
        text = str(properties.get("text", "Olá!"))
        options = properties.get("options", [])

        manager = _get_dialogue_manager(game)
        if manager and hasattr(manager, "show_dialogue"):
            success = manager.show_dialogue(
                dialog_id=dialog_id,
                speaker=character,
                text=text,
                choices=options
            )
            if success:
                runtime._store(node_id, "dialog_id", dialog_id)
                runtime._store(node_id, "is_showing", True)
                return ["success"]

        return ["failure"]
    except Exception as e:
        print(f"Erro em show_dialog: {e}")
        return ["failure"]


@registry.register_executor("wait_dialog_choice")
def execute_wait_dialog_choice(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Aguarda o player escolher uma opção de diálogo.

    Retorna ["waiting"] enquanto aguardando.
    Retorna ["chosen"] quando escolha é feita.
    Retorna ["failure"] em caso de erro.

    Semântica: Node retorna "waiting" e aguarda external trigger (UI button).
    Framework espera edge "waiting" → "wait_dialog_choice" (loop).
    Quando escolha é feita, próxima execução retorna "chosen".
    """
    node_id = str(node["id"])
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))

        manager = _get_dialogue_manager(game)
        if not manager:
            return ["failure"]

        # Check if dialogue is active and has a pending choice
        choice_index = manager.get_pending_choice(dialog_id)

        if choice_index is not None:
            # Choice was made
            chosen_text = manager.get_choice_text(dialog_id, choice_index)
            runtime._store(node_id, "choice_index", choice_index)
            runtime._store(node_id, "chosen_text", str(chosen_text or ""))

            # Clear pending choice
            manager.clear_pending_choice(dialog_id)

            return ["chosen"]
        else:
            # Still waiting for choice
            return ["waiting"]

    except Exception as e:
        print(f"Erro em wait_dialog_choice: {e}")
        return ["failure"]


@registry.register_executor("set_dialog_choice")
def execute_set_dialog_choice(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Define a escolha do player no diálogo.

    Pode ser usado para:
    - Testes automatizados
    - AI fazendo escolhas
    - Keyboard shortcuts (1/2/3 para escolhas)
    """
    node_id = str(node["id"])
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))
        choice_index = int(properties.get("choice_index", 0))

        manager = _get_dialogue_manager(game)
        if not manager:
            return ["failure"]

        success = manager.set_dialogue_choice(dialog_id, choice_index)
        return ["success" if success else "failure"]

    except Exception as e:
        print(f"Erro em set_dialog_choice: {e}")
        return ["failure"]


@registry.register_executor("close_dialog")
def execute_close_dialog(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Fecha o diálogo ativo.

    Limpa UI e cancela qualquer escolha pendente.
    """
    node_id = str(node["id"])
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))

        manager = _get_dialogue_manager(game)
        if manager and hasattr(manager, "close_dialogue"):
            manager.close_dialogue(dialog_id)

        return ["success"]
    except Exception as e:
        print(f"Erro em close_dialog: {e}")
        return ["failure"]
