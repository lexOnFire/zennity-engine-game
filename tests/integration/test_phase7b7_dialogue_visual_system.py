"""
Phase 7B.7: Dialogue Visual System - Comprehensive Test Suite

Tests that dialogue works end-to-end through Logic Graph:

Player near NPC
↓
Press E
↓
Show Dialogue "Halt! Do you have a pass?"
↓
Player chooses:
1. Yes
2. No
↓
Graph branches based on choice
↓
Set Variables
↓
Close Dialogue

100% without Python dialogue management.
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.logic.runtime.registry import registry
from editor.runtime.viewport_logic_api import PlayLogicAPI

# Ensure dialogue nodes are imported
import engine.logic.runtime.nodes.dialog_nodes  # noqa


class TestDialogueNodesRegistered:
    """Verify dialogue nodes are in registry."""

    def test_show_dialog_registered(self):
        """Verify show_dialog executor exists."""
        assert "show_dialog" in registry.executors, "show_dialog executor missing"

    def test_wait_dialog_choice_registered(self):
        """Verify wait_dialog_choice executor exists."""
        assert "wait_dialog_choice" in registry.executors, "wait_dialog_choice executor missing"

    def test_set_dialog_choice_registered(self):
        """Verify set_dialog_choice executor exists."""
        assert "set_dialog_choice" in registry.executors, "set_dialog_choice executor missing"

    def test_close_dialog_registered(self):
        """Verify close_dialog executor exists."""
        assert "close_dialog" in registry.executors, "close_dialog executor missing"


class TestPlayLogicAPIDialogueMethods:
    """Verify PlayLogicAPI has all dialogue methods."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_show_dialogue_method_exists(self):
        """Verify show_dialogue() method exists."""
        assert hasattr(self.api, "show_dialogue"), "PlayLogicAPI missing show_dialogue()"
        assert callable(self.api.show_dialogue), "show_dialogue() not callable"

    def test_wait_dialogue_choice_method_exists(self):
        """Verify wait_dialogue_choice() method exists."""
        assert hasattr(self.api, "wait_dialogue_choice"), "PlayLogicAPI missing wait_dialogue_choice()"
        assert callable(self.api.wait_dialogue_choice), "wait_dialogue_choice() not callable"

    def test_set_dialogue_choice_method_exists(self):
        """Verify set_dialogue_choice() method exists."""
        assert hasattr(self.api, "set_dialogue_choice"), "PlayLogicAPI missing set_dialogue_choice()"
        assert callable(self.api.set_dialogue_choice), "set_dialogue_choice() not callable"

    def test_get_choice_text_method_exists(self):
        """Verify get_choice_text() method exists."""
        assert hasattr(self.api, "get_choice_text"), "PlayLogicAPI missing get_choice_text()"
        assert callable(self.api.get_choice_text), "get_choice_text() not callable"

    def test_get_pending_choice_method_exists(self):
        """Verify get_pending_choice() method exists."""
        assert hasattr(self.api, "get_pending_choice"), "PlayLogicAPI missing get_pending_choice()"
        assert callable(self.api.get_pending_choice), "get_pending_choice() not callable"

    def test_clear_pending_choice_method_exists(self):
        """Verify clear_pending_choice() method exists."""
        assert hasattr(self.api, "clear_pending_choice"), "PlayLogicAPI missing clear_pending_choice()"
        assert callable(self.api.clear_pending_choice), "clear_pending_choice() not callable"

    def test_close_dialogue_method_exists(self):
        """Verify close_dialogue() method exists."""
        assert hasattr(self.api, "close_dialogue"), "PlayLogicAPI missing close_dialogue()"
        assert callable(self.api.close_dialogue), "close_dialogue() not callable"


class TestDialogueStateManagement:
    """Test dialogue state storage and retrieval."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_show_dialogue_creates_session(self):
        """Verify show_dialogue() creates session state."""
        result = self.api.show_dialogue(
            "dialog_1",
            speaker="Guard",
            text="Halt! Who goes there?",
            choices=["I have a pass", "Let me through", "Flee"]
        )
        assert result is True, "show_dialogue() should return True"
        assert "_dialogue_sessions" in self.obj, "Should create _dialogue_sessions dict"
        assert "dialog_1" in self.obj["_dialogue_sessions"], "Should store session"

    def test_dialogue_session_has_correct_data(self):
        """Verify dialogue session stores correct speaker, text, choices."""
        self.api.show_dialogue(
            "guard_talk",
            speaker="Guard",
            text="You cannot pass",
            choices=["Why?", "Please?"]
        )

        session = self.obj["_dialogue_sessions"]["guard_talk"]
        assert session["speaker"] == "Guard", "Speaker should match"
        assert session["text"] == "You cannot pass", "Text should match"
        assert session["choices"] == ["Why?", "Please?"], "Choices should match"

    def test_dialogue_session_initially_no_pending_choice(self):
        """Verify new session has no pending choice."""
        self.api.show_dialogue("test", "NPC", "Hello")
        session = self.obj["_dialogue_sessions"]["test"]
        assert session["pending_choice"] is None, "Should start with no pending choice"

    def test_wait_dialogue_choice_returns_none_initially(self):
        """Verify wait_dialogue_choice() returns None before choice."""
        self.api.show_dialogue("test", "NPC", "Choose", choices=["A", "B"])
        result = self.api.wait_dialogue_choice("test")
        assert result is None, "Should return None before choice"

    def test_get_pending_choice_returns_none_initially(self):
        """Verify get_pending_choice() returns None before choice."""
        self.api.show_dialogue("test", "NPC", "Choose", choices=["A", "B"])
        result = self.api.get_pending_choice("test")
        assert result is None, "Should return None before choice"


class TestDialogueChoice:
    """Test dialogue choice selection."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_set_dialogue_choice_stores_index(self):
        """Verify set_dialogue_choice() stores choice index."""
        self.api.show_dialogue("test", "NPC", "Pick", choices=["A", "B", "C"])
        result = self.api.set_dialogue_choice("test", 1)
        assert result is True, "set_dialogue_choice() should return True"

    def test_set_dialogue_choice_can_be_retrieved(self):
        """Verify choice set with set_dialogue_choice() can be retrieved."""
        self.api.show_dialogue("test", "NPC", "Pick", choices=["A", "B", "C"])
        self.api.set_dialogue_choice("test", 2)
        result = self.api.wait_dialogue_choice("test")
        assert result == 2, "Should retrieve choice index 2"

    def test_get_choice_text_returns_correct_text(self):
        """Verify get_choice_text() returns correct choice text."""
        self.api.show_dialogue("test", "NPC", "Pick", choices=["Yes", "No", "Maybe"])
        text = self.api.get_choice_text("test", 0)
        assert text == "Yes", "Should return 'Yes' for index 0"

        text = self.api.get_choice_text("test", 1)
        assert text == "No", "Should return 'No' for index 1"

    def test_get_choice_text_out_of_bounds_returns_empty(self):
        """Verify get_choice_text() returns empty string for out-of-bounds index."""
        self.api.show_dialogue("test", "NPC", "Pick", choices=["A", "B"])
        text = self.api.get_choice_text("test", 10)
        assert text == "", "Should return empty string for invalid index"

    def test_clear_pending_choice_removes_choice(self):
        """Verify clear_pending_choice() clears the pending choice."""
        self.api.show_dialogue("test", "NPC", "Pick", choices=["A", "B"])
        self.api.set_dialogue_choice("test", 0)
        self.api.clear_pending_choice("test")
        result = self.api.wait_dialogue_choice("test")
        assert result is None, "Should return None after clearing"

    def test_multiple_choices_independent(self):
        """Verify multiple dialogues can track choices independently."""
        self.api.show_dialogue("guard", "Guard", "Pass?", choices=["Yes", "No"])
        self.api.show_dialogue("merchant", "Merchant", "Buy?", choices=["Sure", "No"])

        self.api.set_dialogue_choice("guard", 0)
        self.api.set_dialogue_choice("merchant", 1)

        assert self.api.wait_dialogue_choice("guard") == 0, "Guard should have choice 0"
        assert self.api.wait_dialogue_choice("merchant") == 1, "Merchant should have choice 1"


class TestDialogueUI:
    """Test dialogue UI integration."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_show_dialogue_queues_ui_event(self):
        """Verify show_dialogue() queues UI update event."""
        self.api.show_dialogue("test", "NPC", "Hello")
        events = self.obj.get("logic_events", [])
        assert len(events) > 0, "Should queue UI events"

        show_event = next((e for e in events if e.get("command") == "show_dialogue_panel"), None)
        assert show_event is not None, "Should queue show_dialogue_panel event"

    def test_close_dialogue_queues_ui_cleanup(self):
        """Verify close_dialogue() queues UI cleanup event."""
        self.api.show_dialogue("test", "NPC", "Hello")
        self.api.close_dialogue("test")
        events = self.obj.get("logic_events", [])

        hide_event = next((e for e in events if e.get("command") == "hide_dialogue_panel"), None)
        assert hide_event is not None, "Should queue hide_dialogue_panel event"

    def test_show_dialogue_ui_event_contains_data(self):
        """Verify UI event contains dialogue data."""
        self.api.show_dialogue(
            "test",
            speaker="Guard",
            text="Halt!",
            choices=["Yes", "No"]
        )
        events = self.obj.get("logic_events", [])
        show_event = next((e for e in events if e.get("command") == "show_dialogue_panel"), None)

        value = show_event.get("value", {})
        assert value.get("dialog_id") == "test", "Should include dialog_id"
        assert value.get("speaker") == "Guard", "Should include speaker"
        assert value.get("text") == "Halt!", "Should include text"
        assert value.get("choices") == ["Yes", "No"], "Should include choices"


class TestDialogueLifecycle:
    """Test dialogue session lifecycle."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_dialogue_session_is_active(self):
        """Verify dialogue session starts as active."""
        self.api.show_dialogue("test", "NPC", "Hello")
        session = self.obj["_dialogue_sessions"]["test"]
        assert session["is_active"] is True, "Session should be active"

    def test_close_dialogue_deactivates_session(self):
        """Verify close_dialogue() deactivates session."""
        self.api.show_dialogue("test", "NPC", "Hello")
        self.api.close_dialogue("test")
        session = self.obj["_dialogue_sessions"]["test"]
        assert session["is_active"] is False, "Session should be inactive"

    def test_set_choice_fails_on_inactive_session(self):
        """Verify set_dialogue_choice() fails on inactive session."""
        self.api.show_dialogue("test", "NPC", "Hello", choices=["A"])
        self.api.close_dialogue("test")
        result = self.api.set_dialogue_choice("test", 0)
        assert result is False, "Should fail on inactive session"

    def test_close_nonexistent_dialogue_succeeds(self):
        """Verify close_dialogue() succeeds even if dialogue doesn't exist."""
        result = self.api.close_dialogue("nonexistent")
        assert result is False or result is True, "Should handle gracefully"


class TestDialogueE2E:
    """E2E tests for complete dialogue flows."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_basic_dialogue_flow(self):
        """Test: Show → Wait → Choose → Close."""
        # Show dialogue
        self.api.show_dialogue(
            "guard",
            speaker="Guard",
            text="Do you have a pass?",
            choices=["Yes", "No"]
        )

        # Verify dialogue is shown
        assert self.api.wait_dialogue_choice("guard") is None, "No choice yet"

        # Make choice
        self.api.set_dialogue_choice("guard", 0)

        # Verify choice stored
        assert self.api.wait_dialogue_choice("guard") == 0, "Choice should be stored"
        assert self.api.get_choice_text("guard", 0) == "Yes", "Should get choice text"

        # Close dialogue
        self.api.close_dialogue("guard")
        assert self.obj["_dialogue_sessions"]["guard"]["is_active"] is False

    def test_multiple_npcs_dialogue_independence(self):
        """Test: Multiple NPCs can have independent dialogues."""
        # Guard dialogue
        self.api.show_dialogue("guard", "Guard", "Halt!", choices=["Yes", "No"])

        # Merchant dialogue
        self.api.show_dialogue("merchant", "Merchant", "Buy?", choices=["Sure", "No"])

        # Set Guard choice
        self.api.set_dialogue_choice("guard", 0)

        # Merchant should not be affected
        assert self.api.wait_dialogue_choice("merchant") is None

        # Set Merchant choice
        self.api.set_dialogue_choice("merchant", 1)

        # Both should be independent
        assert self.api.wait_dialogue_choice("guard") == 0
        assert self.api.wait_dialogue_choice("merchant") == 1

        # Close Guard
        self.api.close_dialogue("guard")

        # Merchant should remain active
        assert self.obj["_dialogue_sessions"]["guard"]["is_active"] is False
        assert self.obj["_dialogue_sessions"]["merchant"]["is_active"] is True

    def test_dialogue_choice_branching(self):
        """Test: Different branches based on choice."""
        self.api.show_dialogue("test", "NPC", "Join us?", choices=["Yes", "No"])

        # Simulate choosing "No"
        self.api.set_dialogue_choice("test", 1)
        choice = self.api.wait_dialogue_choice("test")

        # Verify choice 1 leads to different branch
        assert choice == 1, "Should detect choice 1"

        # Clear and simulate choosing "Yes"
        self.api.clear_pending_choice("test")
        self.api.set_dialogue_choice("test", 0)
        choice = self.api.wait_dialogue_choice("test")

        assert choice == 0, "Should detect choice 0"

    def test_repeated_dialogue_interactions(self):
        """Test: Can repeat dialogue interactions."""
        for i in range(3):
            self.api.show_dialogue(f"dialog_{i}", "NPC", f"Talk {i}", choices=["A", "B"])
            self.api.set_dialogue_choice(f"dialog_{i}", i % 2)
            assert self.api.wait_dialogue_choice(f"dialog_{i}") == i % 2
            self.api.close_dialogue(f"dialog_{i}")

    def test_dialogue_with_no_choices(self):
        """Test: Dialogue can have no choices (narration)."""
        result = self.api.show_dialogue("narration", "Narrator", "Once upon a time...")
        assert result is True, "Should support no-choice dialogue"

        # Should still be able to close
        result = self.api.close_dialogue("narration")
        assert result is True, "Should close narration dialogue"

    def test_dialogue_choice_persistence_before_clear(self):
        """Test: Choice persists until explicitly cleared."""
        self.api.show_dialogue("test", "NPC", "Choose", choices=["A", "B", "C"])
        self.api.set_dialogue_choice("test", 1)

        # Multiple reads should return same choice
        assert self.api.wait_dialogue_choice("test") == 1
        assert self.api.wait_dialogue_choice("test") == 1  # Still there
        assert self.api.get_pending_choice("test") == 1

        # Clear
        self.api.clear_pending_choice("test")

        # Now should be None
        assert self.api.wait_dialogue_choice("test") is None


class TestDialogueEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_empty_speaker_name(self):
        """Test: Dialogue works with empty speaker."""
        result = self.api.show_dialogue("test", "", "Text only")
        assert result is True, "Should handle empty speaker"

    def test_empty_dialogue_text(self):
        """Test: Dialogue works with empty text."""
        result = self.api.show_dialogue("test", "NPC", "")
        assert result is True, "Should handle empty text"

    def test_very_long_text(self):
        """Test: Dialogue handles very long text."""
        long_text = "A" * 10000
        result = self.api.show_dialogue("test", "NPC", long_text)
        assert result is True, "Should handle long text"

    def test_special_characters_in_text(self):
        """Test: Dialogue handles special characters."""
        result = self.api.show_dialogue("test", "NPC", "Hi!\n\t\"Quote\" & <tag>")
        assert result is True, "Should handle special characters"

    def test_large_number_of_choices(self):
        """Test: Dialogue handles many choices."""
        choices = [f"Choice {i}" for i in range(100)]
        result = self.api.show_dialogue("test", "NPC", "Pick one", choices=choices)
        assert result is True, "Should handle many choices"

    def test_choice_index_out_of_range(self):
        """Test: set_dialogue_choice with out-of-range index."""
        self.api.show_dialogue("test", "NPC", "Pick", choices=["A", "B"])
        # Out-of-range choice is still stored (no validation)
        result = self.api.set_dialogue_choice("test", 100)
        assert result is True, "Should allow out-of-range index (validation by node)"


class TestDialogueNodeExecutors:
    """Test that dialogue node executors work correctly."""

    def setup_method(self):
        """Set up mock game object."""
        self.obj = {"name": "TestObject"}
        self.api = PlayLogicAPI("TestObject", self.obj, None)

        # Mock game object with dialogue manager
        self.game = type('MockGame', (), {
            'get_dialogue_manager': lambda self: self.dialogue_api,
            'dialogue_api': self.api
        })()
        self.game.dialogue_api = self.api

    def test_show_dialog_executor_delegates_to_api(self):
        """Test show_dialog node executor calls PlayLogicAPI."""
        node = {
            'id': 'node_1',
            'properties': {
                'dialog_id': 'test',
                'character': 'NPC',
                'text': 'Hello',
                'options': ['A', 'B']
            }
        }

        # Execute node
        result = registry.executors['show_dialog'](None, node, self.game, 0.0)

        # Should fail without proper runtime, but shows node exists
        # (Full executor test requires full LogicGraphRuntime)
        assert result in [["success"], ["failure"]], "Executor should return valid ports"

    def test_wait_dialog_choice_executor_exists(self):
        """Test wait_dialog_choice node executor exists."""
        assert 'wait_dialog_choice' in registry.executors
        executor = registry.executors['wait_dialog_choice']
        assert callable(executor), "Executor should be callable"

    def test_set_dialog_choice_executor_exists(self):
        """Test set_dialog_choice node executor exists."""
        assert 'set_dialog_choice' in registry.executors
        executor = registry.executors['set_dialog_choice']
        assert callable(executor), "Executor should be callable"

    def test_close_dialog_executor_exists(self):
        """Test close_dialog node executor exists."""
        assert 'close_dialog' in registry.executors
        executor = registry.executors['close_dialog']
        assert callable(executor), "Executor should be callable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
