"""Testes para DialogueManager component."""

import pytest
from engine.ui.dialogue_manager import DialogueManager
from engine.game_object import GameObject
from engine.dialogue.runtime import DialogueSession


def test_dialogue_manager_creation():
    """Testa criação básica de DialogueManager."""
    manager = DialogueManager(
        dialogue_file="Assets/Dialogues/test.zdialogue",
        speaker_name="NPC",
        auto_start=False,
    )

    assert manager.dialogue_file == "Assets/Dialogues/test.zdialogue"
    assert manager.speaker_name == "NPC"
    assert manager.auto_start == False
    assert manager.is_active() == False


def test_dialogue_manager_flags():
    """Testa sistema de flags/variáveis."""
    manager = DialogueManager()

    # Cria uma sessão mock para testes
    manager._session = DialogueSession(
        {
            "format": "zennity.generic_graph",
            "category": "Dialogue",
            "nodes": [],
            "edges": [],
        }
    )

    # Define flags
    manager.set_flag("player_level", 5)
    manager.set_flag("has_quest", True)

    # Recupera flags
    assert manager.get_flag("player_level") == 5
    assert manager.get_flag("has_quest") == True
    assert manager.get_flag("nonexistent", "default") == "default"


def test_dialogue_manager_callbacks():
    """Testa callbacks do diálogo."""
    manager = DialogueManager()

    start_called = False
    end_called = False

    def on_start():
        nonlocal start_called
        start_called = True

    def on_end():
        nonlocal end_called
        end_called = True

    manager.on_dialogue_start(on_start)
    manager.on_dialogue_end(on_end)

    assert manager._on_dialogue_start is not None
    assert manager._on_dialogue_end is not None


def test_dialogue_manager_serialization():
    """Testa serialização e desserialização."""
    manager = DialogueManager(
        dialogue_file="Assets/Dialogues/test.zdialogue",
        speaker_name="NPC",
        auto_start=True,
        ui_text_element="DialogueText",
    )

    # Serializa
    data = manager.serialize()

    assert data["dialogue_file"] == "Assets/Dialogues/test.zdialogue"
    assert data["speaker_name"] == "NPC"
    assert data["auto_start"] == True
    assert data["ui_text_element"] == "DialogueText"

    # Desserializa
    manager2 = DialogueManager()
    manager2.deserialize(data)

    assert manager2.dialogue_file == "Assets/Dialogues/test.zdialogue"
    assert manager2.speaker_name == "NPC"
    assert manager2.auto_start == True


def test_dialogue_manager_snapshot():
    """Testa captura de estado do diálogo."""
    manager = DialogueManager()

    # Cria uma sessão mock
    manager._session = DialogueSession(
        {
            "format": "zennity.generic_graph",
            "category": "Dialogue",
            "nodes": [{"id": "node_1", "type": "dialogue.end", "inputs": {}}],
            "edges": [],
        }
    )

    snapshot = manager.get_current_snapshot()
    assert isinstance(snapshot, dict)


def test_dialogue_manager_is_active():
    """Testa estado ativo do diálogo."""
    manager = DialogueManager()
    assert manager.is_active() == False

    # Simula ativação
    manager._is_active = True
    assert manager.is_active() == True
