"""
Phase 7B.7.3 Refinement 3: Scene Cleanup Validation

Tests dialogue state cleanup on scene changes:
- Scene unload removes all dialogue sessions
- UI cleanup validation
- Waiting dialogue cancellation
- Owner mapping cleanup
- Multi-NPC cleanup
- Asset/inline dialogue cleanup
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.dialogue.manager import get_dialogue_manager, set_dialogue_manager, DialogueManager


class TestSceneCleanup:
    """Test dialogue state cleanup on scene changes."""

    @pytest.fixture
    def manager(self):
        """Fresh DialogueManager for each test."""
        return DialogueManager()

    @pytest.fixture
    def guard_asset_path(self):
        """Path to GuardDialogue.zdialogue fixture."""
        return project_root / "tests" / "fixtures" / "GuardDialogue.zdialogue"

    def test_scene_unload_clears_dialogue_sessions(self, manager):
        """Verify scene unload removes all dialogue sessions."""
        # Scene A: Multiple dialogues active
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Halt!",
            choices=["Yes", "No"],
            owner_id="Guard"
        )

        manager.start_inline(
            session_id="greet",
            speaker="Merchant",
            text="Welcome!",
            choices=["Hi", "Later"],
            owner_id="Merchant"
        )

        # Verify sessions exist
        assert ("Guard", "talk") in manager._sessions
        assert ("Merchant", "greet") in manager._sessions
        assert len(manager._sessions) == 2

        # Simulate scene unload: reset() clears all
        manager.reset()

        # After scene unload
        assert len(manager._sessions) == 0
        assert manager._active_session_id is None

    def test_scene_unload_clears_owner_mappings(self, manager):
        """Verify owner mappings are cleared on scene unload."""
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Hi",
            choices=[],
            owner_id="Guard"
        )

        manager.start_inline(
            session_id="greet",
            speaker="Merchant",
            text="Hello",
            choices=[],
            owner_id="Merchant"
        )

        # Verify owner mappings
        assert "Guard" in manager._owner_sessions
        assert "Merchant" in manager._owner_sessions

        # Scene unload
        manager.reset()

        # Mappings cleared
        assert len(manager._owner_sessions) == 0
        assert manager._owner_sessions.get("Guard") is None
        assert manager._owner_sessions.get("Merchant") is None

    def test_scene_unload_clears_pending_choices(self, manager):
        """Verify pending choices cleared on scene unload."""
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Choose",
            choices=["A", "B"],
            owner_id="default"
        )

        # Register choice callback
        def callback(choice_idx):
            pass

        manager.register_choice_callback("test", callback, owner_id="default")

        # Verify callback registered
        assert len(manager._choice_callbacks) == 1

        # Scene unload
        manager.reset()

        # Callbacks cleared
        assert len(manager._choice_callbacks) == 0

    def test_scene_unload_clears_active_session_key(self, manager):
        """Verify active session key is cleared."""
        manager.start_inline(
            session_id="active",
            speaker="NPC",
            text="Active",
            choices=[],
            owner_id="default"
        )

        # Verify active
        assert manager._active_session_id is not None

        # Scene unload
        manager.reset()

        # Cleared
        assert manager._active_session_id is None

    def test_scene_change_cancels_waiting_dialogue(self, manager):
        """Test that waiting dialogue stops after scene change."""
        manager.start_inline(
            session_id="wait_test",
            speaker="NPC",
            text="Waiting...",
            choices=["OK"],
            owner_id="default"
        )

        composite_key = ("default", "wait_test")
        assert composite_key in manager._sessions

        # Simulate being in wait state
        session = manager._sessions[composite_key]
        original_active = session.active

        # Scene change
        manager.reset()

        # After change: session gone, no more waiting
        assert composite_key not in manager._sessions

    def test_old_choice_after_scene_change_does_nothing(self, manager):
        """Test that choosing after scene change doesn't execute."""
        manager.start_inline(
            session_id="old_choice",
            speaker="NPC",
            text="Choose",
            choices=["A", "B"],
            owner_id="default"
        )

        # Simulate scene change
        manager.reset()

        # Try to make choice from old scene
        result = manager.choose("old_choice", 0, owner_id="default")

        # Should fail (session doesn't exist)
        assert result is False

    def test_restart_scene_clears_dialogue(self, manager):
        """Test restart_scene clears dialogue."""
        manager.start_inline(
            session_id="restart_test",
            speaker="NPC",
            text="Before restart",
            choices=[],
            owner_id="default"
        )

        # Restart = reset
        manager.reset()

        # All cleared
        assert len(manager._sessions) == 0

        # New dialogue starts clean
        manager.start_inline(
            session_id="after_restart",
            speaker="NPC",
            text="After restart",
            choices=[],
            owner_id="default"
        )

        # New session should be clean (no old references)
        state = manager.get_state("after_restart", owner_id="default")
        assert state.get("speaker") == "NPC"
        assert state.get("text") == "After restart"

    def test_multi_npc_scene_cleanup(self, manager):
        """Test cleanup with multiple NPCs."""
        npcs = ["Guard", "Merchant", "Boss", "Innkeeper"]

        # Create dialogue for each NPC
        for i, npc in enumerate(npcs):
            manager.start_inline(
                session_id="talk",
                speaker=npc,
                text=f"{npc} speaks",
                choices=[],
                owner_id=npc
            )

        # Verify all exist
        assert len(manager._sessions) == len(npcs)

        # Scene unload
        manager.reset()

        # All gone
        assert len(manager._sessions) == 0
        assert len(manager._owner_sessions) == 0

    def test_same_id_multi_owner_cleanup(self, manager):
        """Test cleanup with same session_id, different owners."""
        # Guard/talk
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Halt",
            choices=[],
            owner_id="Guard"
        )

        # Merchant/talk (same ID, different owner)
        manager.start_inline(
            session_id="talk",
            speaker="Merchant",
            text="Trade",
            choices=[],
            owner_id="Merchant"
        )

        guard_key = ("Guard", "talk")
        merchant_key = ("Merchant", "talk")

        assert guard_key in manager._sessions
        assert merchant_key in manager._sessions

        # Scene unload
        manager.reset()

        # Both cleaned
        assert guard_key not in manager._sessions
        assert merchant_key not in manager._sessions

    def test_asset_dialogue_scene_cleanup(self, manager, guard_asset_path):
        """Test cleanup with asset dialogue."""
        if not guard_asset_path.exists():
            pytest.skip("GuardDialogue.zdialogue not found")

        manager.start_asset(
            session_id="asset_talk",
            asset_path=str(guard_asset_path),
            owner_id="Guard"
        )

        assert ("Guard", "asset_talk") in manager._sessions

        # Scene unload
        manager.reset()

        # Asset dialogue cleaned
        assert ("Guard", "asset_talk") not in manager._sessions

    def test_inline_dialogue_scene_cleanup(self, manager):
        """Test cleanup with inline dialogue."""
        manager.start_inline(
            session_id="inline",
            speaker="NPC",
            text="Hello",
            choices=["Hi"],
            owner_id="default"
        )

        assert ("default", "inline") in manager._sessions

        # Scene unload
        manager.reset()

        # Inline cleaned
        assert ("default", "inline") not in manager._sessions

    def test_mixed_asset_inline_cleanup(self, manager, guard_asset_path):
        """Test cleanup with mix of asset and inline."""
        if not guard_asset_path.exists():
            pytest.skip("GuardDialogue.zdialogue not found")

        manager.start_asset(
            session_id="asset",
            asset_path=str(guard_asset_path),
            owner_id="Guard"
        )

        manager.start_inline(
            session_id="inline",
            speaker="NPC",
            text="Hi",
            choices=[],
            owner_id="Merchant"
        )

        assert len(manager._sessions) == 2

        # Scene unload
        manager.reset()

        # Both cleaned
        assert len(manager._sessions) == 0

    def test_cleanup_idempotent(self, manager):
        """Test reset() twice doesn't crash."""
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Test",
            choices=[],
            owner_id="default"
        )

        # First reset
        manager.reset()
        assert len(manager._sessions) == 0

        # Second reset (should not crash)
        manager.reset()
        assert len(manager._sessions) == 0

    def test_cleanup_empty_manager_safe(self, manager):
        """Test reset() on empty manager is safe."""
        # No sessions
        assert len(manager._sessions) == 0

        # reset() should not crash
        manager.reset()

        # Still empty
        assert len(manager._sessions) == 0

    def test_cleanup_after_close(self, manager):
        """Test reset() after manual close still works."""
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Test",
            choices=[],
            owner_id="Guard"
        )

        # Manual close
        manager.close("test", owner_id="Guard")
        assert ("Guard", "test") not in manager._sessions

        # reset() after close should be safe
        manager.reset()
        assert len(manager._sessions) == 0

    def test_close_owner_alternative(self, manager):
        """Test close_owner as alternative for selective cleanup."""
        # Guard sessions
        manager.start_inline(
            session_id="talk1",
            speaker="Guard",
            text="Hi",
            choices=[],
            owner_id="Guard"
        )
        manager.start_inline(
            session_id="talk2",
            speaker="Guard",
            text="Hi2",
            choices=[],
            owner_id="Guard"
        )

        # Merchant session (should not be affected)
        manager.start_inline(
            session_id="trade",
            speaker="Merchant",
            text="Trade",
            choices=[],
            owner_id="Merchant"
        )

        # Verify all exist
        assert len(manager._sessions) == 3

        # Close only Guard
        manager.close_owner("Guard")

        # Guard sessions gone, Merchant remains
        assert ("Guard", "talk1") not in manager._sessions
        assert ("Guard", "talk2") not in manager._sessions
        assert ("Merchant", "trade") in manager._sessions


class TestSceneCleanupIntegration:
    """Integration tests for scene cleanup flow."""

    @pytest.fixture
    def manager(self):
        return DialogueManager()

    def test_scene_lifecycle_dialogue_flow(self, manager):
        """Test full scene lifecycle: Load → Dialogue → Unload → Load."""
        # Scene A
        manager.start_inline(
            session_id="scene_a",
            speaker="NPC_A",
            text="Scene A",
            choices=[],
            owner_id="Scene_A"
        )
        assert len(manager._sessions) == 1

        # Scene A unload
        manager.reset()
        assert len(manager._sessions) == 0

        # Scene B
        manager.start_inline(
            session_id="scene_b",
            speaker="NPC_B",
            text="Scene B",
            choices=[],
            owner_id="Scene_B"
        )
        assert len(manager._sessions) == 1

        # Verify clean start
        state = manager.get_state("scene_b", owner_id="Scene_B")
        assert state.get("speaker") == "NPC_B"

        # Scene B unload
        manager.reset()
        assert len(manager._sessions) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
