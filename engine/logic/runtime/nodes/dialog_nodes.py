"""
Phase 7B.7.1: Dialogue nodes - Consolidated architecture.

All dialogue nodes route through DialogueManager → DialogueSession.
Single canonical source of truth for dialogue state.
"""
from __future__ import annotations

from typing import Any, Mapping
from ..registry import registry

try:
    from engine.dialogue.manager import get_dialogue_manager
except ImportError:
    from ...dialogue.manager import get_dialogue_manager


@registry.register_executor("show_dialog")
def execute_show_dialog(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Mostra um diálogo com opções para o player escolher.

    Routes through DialogueManager → DialogueSession (canonical).
    """
    node_id = str(node["id"])
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))
        character = str(properties.get("character", "NPC"))
        text = str(properties.get("text", "Olá!"))
        options = properties.get("options", [])

        # Use DialogueManager singleton (canonical)
        manager = get_dialogue_manager()
        owner_id = "dialogue_node"  # Simple owner for now

        success = manager.start_inline(
            session_id=dialog_id,
            speaker=character,
            text=text,
            choices=options if isinstance(options, list) else [],
            owner_id=owner_id
        )

        if success:
            runtime._store(node_id, "dialog_id", dialog_id)
            runtime._store(node_id, "is_showing", True)
            return ["exec_showing"]

        return ["exec_failure"]
    except Exception as e:
        print(f"Erro em show_dialog: {e}")
        return ["exec_failure"]


@registry.register_executor("wait_dialog_choice")
def execute_wait_dialog_choice(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Aguarda o player escolher uma opção de diálogo.

    Checks DialogueSession state directly (canonical).
    Uses composite key (owner_id, dialog_id).

    Returns:
    - ["waiting"] if dialogue still active (no choice yet)
    - ["chosen"] if dialogue finished (choice made)
    - ["failure"] if error or dialogue not found
    """
    node_id = str(node["id"])
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))
        owner_id = "dialogue_node"  # Owner context for composite key

        manager = get_dialogue_manager()
        state = manager.get_state(dialog_id, owner_id=owner_id)

        if not state:
            return ["exec_failure"]  # Dialogue not found

        # Check DialogueSession state directly
        if state.get("active", False):
            # Still active, waiting for choice
            return ["exec_waiting"]
        else:
            # Dialogue ended (choice was made)
            # Store choice result
            runtime._store(node_id, "choice_index", 0)  # Choice processed
            runtime._store(node_id, "chosen_text", "")
            return ["exec_chosen"]

    except Exception as e:
        print(f"Erro em wait_dialog_choice: {e}")
        return ["exec_failure"]


@registry.register_executor("set_dialog_choice")
def execute_set_dialog_choice(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Define a escolha do player no diálogo.

    Routes through DialogueManager → DialogueSession.choose()
    Uses composite key (owner_id, dialog_id).
    Can be used for testing, AI, keyboard shortcuts.
    """
    node_id = str(node["id"])
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))
        choice_index = int(properties.get("choice_index", 0))
        owner_id = "dialogue_node"  # Owner context for composite key

        manager = get_dialogue_manager()
        success = manager.choose(dialog_id, choice_index, owner_id=owner_id)
        return ["next" if success else "exec_failure"]

    except Exception as e:
        print(f"Erro em set_dialog_choice: {e}")
        return ["exec_failure"]


@registry.register_executor("close_dialog")
def execute_close_dialog(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """
    Fecha o diálogo ativo.

    Routes through DialogueManager (canonical).
    Uses composite key (owner_id, dialog_id).
    Cleans up session and UI.
    """
    node_id = str(node["id"])
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

    try:
        dialog_id = str(properties.get("dialog_id", "dialog_1"))
        owner_id = "dialogue_node"  # Owner context for composite key

        manager = get_dialogue_manager()
        success = manager.close(dialog_id, owner_id=owner_id)

        return ["next" if success else "exec_failure"]
    except Exception as e:
        print(f"Erro em close_dialog: {e}")
        return ["exec_failure"]
