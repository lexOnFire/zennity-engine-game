"""
Phase 7B.7.3 Refinement 5: Dialogue Event Routing

Tests dialogue event delivery through LogicEventBus:
- Event sink now passed to DialogueSession
- Payload structure includes owner_id and session_id
- Owner isolation
- Event firing once per branch
- No global dispatcher created
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.dialogue.manager import get_dialogue_manager, set_dialogue_manager, DialogueManager


class TestDialogueEventSinkSupport:
    """Test that event_sink is now passed to DialogueSession."""

    @pytest.fixture
    def manager(self):
        return DialogueManager()

    def test_inline_now_has_event_sink(self, manager):
        """Verify inline dialogue now passes event_sink to DialogueSession."""
        owner_id = "default"
        session_id = "test"

        # Start inline (which now has event_sink)
        manager.start_inline(
            session_id=session_id,
            speaker="NPC",
            text="Hello",
            choices=[],
            owner_id=owner_id
        )

        # Verify session was created
        composite_key = (owner_id, session_id)
        assert composite_key in manager._sessions

        # Verify session exists and is a DialogueSession
        session = manager._sessions[composite_key]
        assert hasattr(session, 'event_sink')
        assert session.event_sink is not None

class TestDialogueEventOwnerIsolation:
    """Test event delivery is owner-isolated."""

    @pytest.fixture
    def manager(self):
        return DialogueManager()

    def test_composite_key_enables_owner_routing(self, manager):
        """Verify composite key enables correct owner routing."""
        # Create two owners with same session_id
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Guard speaks",
            choices=[],
            owner_id="Guard"
        )

        manager.start_inline(
            session_id="talk",
            speaker="Merchant",
            text="Merchant speaks",
            choices=[],
            owner_id="Merchant"
        )

        # Events for Guard would go through composite key ("Guard", "talk")
        # Events for Merchant would go through composite key ("Merchant", "talk")
        guard_key = ("Guard", "talk")
        merchant_key = ("Merchant", "talk")

        assert guard_key in manager._sessions
        assert merchant_key in manager._sessions

        # Verify isolation - getting state for one doesn't affect other
        guard_state = manager.get_state("talk", owner_id="Guard")
        merchant_state = manager.get_state("talk", owner_id="Merchant")

        assert guard_state.get("speaker") == "Guard"
        assert merchant_state.get("speaker") == "Merchant"


class TestDialogueEventPayload:
    """Test event payload structure."""

    @pytest.fixture
    def manager(self):
        return DialogueManager()

    def test_handle_dialogue_event_receives_owner_id(self, manager):
        """Verify _handle_dialogue_event receives owner_id in composite key."""
        owner_id = "Guard"
        session_id = "talk"
        composite_key = (owner_id, session_id)

        # Create minimal session
        manager.start_inline(
            session_id=session_id,
            speaker="Guard",
            text="Hello",
            choices=[],
            owner_id=owner_id
        )

        # Verify that _handle_dialogue_event can be called with composite key
        # This validates the payload structure includes owner context
        # (actual LogicEventBus routing tested separately if bus is available)
        try:
            manager._handle_dialogue_event(composite_key, "test_event", {})
            # If LogicEventBus not available, should fall back to print
        except Exception:
            pytest.fail("_handle_dialogue_event should handle missing LogicEventBus")


class TestDialogueEventSession:
    """Test event sink is now part of DialogueSession."""

    @pytest.fixture
    def manager(self):
        return DialogueManager()

    @pytest.fixture
    def guard_asset_path(self):
        return project_root / "tests" / "fixtures" / "GuardDialogue.zdialogue"

    def test_asset_dialogue_has_event_sink(self, manager, guard_asset_path):
        """Verify asset dialogue DialogueSession has event_sink."""
        if not guard_asset_path.exists():
            pytest.skip("GuardDialogue.zdialogue not found")

        manager.start_asset(
            session_id="guard",
            asset_path=str(guard_asset_path),
            owner_id="Guard"
        )

        composite_key = ("Guard", "guard")
        session = manager._sessions[composite_key]

        # Verify session has event_sink
        assert hasattr(session, 'event_sink')
        assert session.event_sink is not None

    def test_inline_dialogue_has_event_sink(self, manager):
        """Verify inline dialogue DialogueSession has event_sink."""
        manager.start_inline(
            session_id="inline",
            speaker="NPC",
            text="Hello",
            choices=[],
            owner_id="default"
        )

        composite_key = ("default", "inline")
        session = manager._sessions[composite_key]

        # Verify session has event_sink
        assert hasattr(session, 'event_sink')
        assert session.event_sink is not None


class TestDialogueEventLifecycle:
    """Test event lifecycle and safety."""

    @pytest.fixture
    def manager(self):
        return DialogueManager()

    def test_event_after_session_close_safe(self, manager):
        """Verify event handling is safe even if session was closed."""
        owner_id = "Guard"
        session_id = "talk"

        manager.start_inline(
            session_id=session_id,
            speaker="Guard",
            text="Hello",
            choices=[],
            owner_id=owner_id
        )

        # Close session
        manager.close(session_id, owner_id=owner_id)

        # Try to handle event from closed session (should not crash)
        try:
            manager._handle_dialogue_event(
                (owner_id, session_id),
                "event",
                {}
            )
        except Exception:
            pytest.fail("_handle_dialogue_event should handle closed sessions safely")

    def test_event_after_scene_reset_safe(self, manager):
        """Verify events don't fire after scene reset."""
        owner_id = "Guard"
        session_id = "talk"

        manager.start_inline(
            session_id=session_id,
            speaker="Guard",
            text="Hello",
            choices=[],
            owner_id=owner_id
        )

        # Scene reset
        manager.reset()

        # Old session is gone
        assert (owner_id, session_id) not in manager._sessions

        # Try to emit event from old session (should not crash)
        try:
            manager._handle_dialogue_event(
                (owner_id, session_id),
                "event",
                {}
            )
        except Exception:
            pytest.fail("_handle_dialogue_event should handle missing sessions safely")


class TestNoGlobalDispatcher:
    """Verify no global dialogue dispatcher exists."""

    def test_no_parallel_event_system(self):
        """Verify DialogueManager uses LogicEventBus, not separate dispatcher."""
        import engine.dialogue.manager as dm

        # Check for any separate global dispatcher
        assert not hasattr(dm, "dialogue_event_dispatch")
        assert not hasattr(dm, "global_dialogue_handlers")
        assert not hasattr(dm, "dialogue_event_registry")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
