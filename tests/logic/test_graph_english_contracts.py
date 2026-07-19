"""Tests validation of English node category/title contracts and migrations."""
from __future__ import annotations

import pytest
from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    NODE_PORT_DEFINITIONS,
    _migrate_category,
    normalize_logic_graph,
)
from engine.logic.recipes import LOGIC_RECIPES
from engine.logic.runtime import LogicGraphRuntime


def test_all_node_definitions_have_english_categories() -> None:
    """Validate that every built-in node definition uses English categories."""
    invalid_categories = {"Ação", "Condição", "Eventos", "Lógica", "Matemática", "Movimento", "Objetos", "Posição", "Subgrafos", "Texto", "Variáveis"}
    for node_type, definition in NODE_DEFINITIONS.items():
        category = definition.get("category", "")
        assert category not in invalid_categories, f"Node type '{node_type}' has Portuguese category '{category}'"


def test_all_node_port_definitions_match_node_definitions() -> None:
    """Validate that every node definition has matching port definitions (except dynamic sequencer)."""
    for node_type in NODE_DEFINITIONS:
        # sequence and custom nodes are dynamic, but basic definition exists
        assert node_type in NODE_PORT_DEFINITIONS or node_type == "event_custom", f"Node type '{node_type}' is missing from NODE_PORT_DEFINITIONS"


def test_category_migration_normalizes_portuguese() -> None:
    """Validate that the category migration correctly translates legacy categories."""
    assert _migrate_category("Ação") == "Action"
    assert _migrate_category("Condição") == "Condition"
    assert _migrate_category("Eventos") == "Events"
    assert _migrate_category("Lógica") == "Logic"
    assert _migrate_category("Matemática") == "Math"
    assert _migrate_category("Movimento") == "Movement"
    assert _migrate_category("Objetos") == "Objects"
    assert _migrate_category("Posição") == "Position"
    assert _migrate_category("Subgrafos") == "Subgraphs"
    assert _migrate_category("Texto") == "Text"
    assert _migrate_category("Variáveis") == "Variables"
    # Keep unknown categories as is
    assert _migrate_category("CustomCategory") == "CustomCategory"


def test_normalize_logic_graph_applies_migration() -> None:
    """Validate that normalizing a logic graph updates node categories on the fly."""
    legacy_graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [
            {
                "id": "node1",
                "type": "event_start",
                "category": "Eventos",
            }
        ]
    }
    normalized = normalize_logic_graph(legacy_graph)
    assert normalized["nodes"][0]["category"] == "Events"


def test_recipes_have_english_titles_and_categories() -> None:
    """Validate that all logic graph recipes are localized in English (no non-ASCII or Portuguese tags)."""
    for recipe in LOGIC_RECIPES:
        category = recipe.get("category", "")
        # Categories should be translated
        assert " e " not in category, f"Recipe category '{category}' in recipe '{recipe['id']}' is in Portuguese"
        assert " & " in category or category in {"Animation", "Audio", "Variables"}, f"Recipe category '{category}' in recipe '{recipe['id']}' does not match English standard"
        
        # Topics should be translated
        for topic in recipe.get("topics", ()):
            assert topic not in {"Objetos", "Criação", "Movimento", "Posição", "Imagem", "Cenário", "Ação", "Eventos", "Lógica", "Condição", "Variáveis", "Matemática", "Texto", "Depuração", "Tempo"}, f"Recipe topic '{topic}' in recipe '{recipe['id']}' is in Portuguese"


def test_runtime_error_messages_in_english() -> None:
    """Validate that RuntimeGraph raises errors with English messages."""
    graph_data = {
        "format": "zennity.logic_graph",
        "version": 1,
        "nodes": [
            {"id": "n1", "type": "event_start"},
            {"id": "n2", "type": "log_message", "properties": {"text": "hello"}},
            {"id": "n3", "type": "log_message", "properties": {"text": "world"}},
        ],
        "edges": [
            {"id": "e1", "from_node": "n1", "from_port": "next", "to_node": "n2", "to_port": "in"},
            {"id": "e2", "from_node": "n2", "from_port": "next", "to_node": "n3", "to_port": "in"},
            {"id": "e3", "from_node": "n3", "from_port": "next", "to_node": "n2", "to_port": "in"},
        ]
    }
    
    runtime = LogicGraphRuntime(graph_data)
    
    class DummyGame:
        def log(self, *args, **kwargs):
            pass
        
    with pytest.raises(RuntimeError) as exc_info:
        runtime.start(DummyGame())
        
    assert "infinite execution loop" in str(exc_info.value)
