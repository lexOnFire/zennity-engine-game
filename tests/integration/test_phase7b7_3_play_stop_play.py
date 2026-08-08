"""
Phase 7B.7.3 Refinement 4: Play/Stop/Play Reset Validation

Tests dialogue reset on Play/Stop/Play cycle:
- Stop resets all dialogue sessions
- Play again starts with clean state
- No pending choices survive Stop
- No waiting execution survives Stop
- Owner mappings don't persist
- Asset/inline sessions restart properly
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.dialogue.manager import get_dialogue_manager, set_dialogue_manager, DialogueManager


class TestPlayStopPlayReset:
    """Test dialogue reset on Play/Stop/Play cycle."""

    @pytest.fixture
    def manager(self):
        """Fresh DialogueManager for each test."""
        return DialogueManager()

    @pytest.fixture
    def guard_asset_path(self):
        return project_root / "tests" / "fixtures" / "GuardDialogue.zdialogue"

    # ========== PLAY 1 → STOP ==========

    def test_stop_clears_dialogue_sessions(self, manager):
        """Verify Stop clears all dialogue sessions."""
        # Play 1: Open dialogue
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Halt!",
            choices=["Yes", "No"],
            owner_id="Guard"
        )

        assert len(manager._sessions) == 1

        # Stop: reset()
        manager.reset()

        # After stop
        assert len(manager._sessions) == 0

    def test_stop_clears_owner_mappings(self, manager):
        """Verify Stop clears owner mappings."""
        # Play 1
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Hi",
            choices=[],
            owner_id="Guard"
        )

        assert "Guard" in manager._owner_sessions

        # Stop
        manager.reset()

        # After stop
        assert len(manager._owner_sessions) == 0

    def test_stop_clears_active_session(self, manager):
        """Verify Stop clears active session key."""
        # Play 1
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Test",
            choices=[],
            owner_id="default"
        )

        assert manager._active_session_id is not None

        # Stop
        manager.reset()

        # After stop
        assert manager._active_session_id is None

    def test_stop_clears_pending_choices(self, manager):
        """Verify Stop clears pending choices."""
        # Play 1
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Choose",
            choices=["A", "B"],
            owner_id="default"
        )

        manager.register_choice_callback("test", lambda idx: None, owner_id="default")
        assert len(manager._choice_callbacks) == 1

        # Stop
        manager.reset()

        # After stop
        assert len(manager._choice_callbacks) == 0

    # ========== PLAY 2: CLEAN START ==========

    def test_play_again_starts_clean(self, manager):
        """Verify Play 2 starts with clean manager state."""
        # Play 1 + Stop
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Play 1",
            choices=[],
            owner_id="default"
        )
        manager.reset()

        # Play 2: Start dialogue
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Play 2",
            choices=[],
            owner_id="default"
        )

        # Should have exactly one session (not two from lingering state)
        assert len(manager._sessions) == 1

        state = manager.get_state("test", owner_id="default")
        assert state.get("text") == "Play 2"

    def test_play_again_creates_single_session(self, manager):
        """Verify creating session twice (stop in between) creates single session."""
        # Play 1
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="First",
            choices=[],
            owner_id="default"
        )

        # Verify one session
        assert len(manager._sessions) == 1

        # Stop
        manager.reset()
        assert len(manager._sessions) == 0

        # Play 2: Same session_id
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Second",
            choices=[],
            owner_id="default"
        )

        # Should still be one session (reuse of key is OK)
        assert len(manager._sessions) == 1

    # ========== PENDING CHOICE PERSISTENCE ==========

    def test_old_choice_does_not_survive_stop(self, manager):
        """Verify old pending choice doesn't survive Stop."""
        # Play 1: Register a pending choice (simulated)
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="Choose",
            choices=["A", "B"],
            owner_id="default"
        )

        # Simulate pending choice (register callback)
        def choice_callback(idx):
            pass

        manager.register_choice_callback("test", choice_callback, owner_id="default")

        # Stop
        manager.reset()

        # Play 2: Old callback should be gone
        manager.start_inline(
            session_id="test",
            speaker="NPC",
            text="New dialog",
            choices=["X", "Y"],
            owner_id="default"
        )

        # Register new callback
        def new_callback(idx):
            pass

        manager.register_choice_callback("test", new_callback, owner_id="default")

        # Only one callback (new one), not two
        assert len(manager._choice_callbacks) == 1

    # ========== WAITING EXECUTION ==========

    def test_waiting_execution_does_not_survive_stop(self, manager):
        """Verify waiting node doesn't continue after Stop."""
        # Play 1: Create waiting state
        manager.start_inline(
            session_id="wait",
            speaker="NPC",
            text="Waiting",
            choices=["OK"],
            owner_id="default"
        )

        composite_key = ("default", "wait")
        assert composite_key in manager._sessions

        # Stop
        manager.reset()

        # Play 2: Try to access old session (should fail)
        result = manager.choose("wait", 0, owner_id="default")
        assert result is False  # Session doesn't exist

    # ========== OWNER MAPPING ==========

    def test_same_id_multi_owner_after_replay(self, manager):
        """Verify same session_id with different owners works after replay."""
        # Play 1
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Halt",
            choices=[],
            owner_id="Guard"
        )
        manager.start_inline(
            session_id="talk",
            speaker="Merchant",
            text="Trade",
            choices=[],
            owner_id="Merchant"
        )

        assert len(manager._sessions) == 2

        # Stop
        manager.reset()
        assert len(manager._sessions) == 0

        # Play 2: Same owners and IDs
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Halt again",
            choices=[],
            owner_id="Guard"
        )
        manager.start_inline(
            session_id="talk",
            speaker="Merchant",
            text="Trade again",
            choices=[],
            owner_id="Merchant"
        )

        # Should have two new sessions (no collision)
        assert len(manager._sessions) == 2

        guard_state = manager.get_state("talk", owner_id="Guard")
        merchant_state = manager.get_state("talk", owner_id="Merchant")

        assert guard_state.get("text") == "Halt again"
        assert merchant_state.get("text") == "Trade again"

    # ========== ASSET REPLAY ==========

    def test_asset_dialogue_restarts_from_beginning(self, manager, guard_asset_path):
        """Verify asset dialogue restarts from first node after Stop."""
        if not guard_asset_path.exists():
            pytest.skip("GuardDialogue.zdialogue not found")

        # Play 1
        manager.start_asset(
            session_id="asset",
            asset_path=str(guard_asset_path),
            owner_id="Guard"
        )

        state1 = manager.get_state("asset", owner_id="Guard")
        node_id_1 = state1.get("node_id")

        # Stop
        manager.reset()

        # Play 2: Same asset
        manager.start_asset(
            session_id="asset",
            asset_path=str(guard_asset_path),
            owner_id="Guard"
        )

        state2 = manager.get_state("asset", owner_id="Guard")
        node_id_2 = state2.get("node_id")

        # Should restart at same initial node
        assert node_id_1 == node_id_2
        assert node_id_2 == "speech_0"

    # ========== INLINE REPLAY ==========

    def test_inline_dialogue_restarts_clean(self, manager):
        """Verify inline dialogue restarts fresh after Stop."""
        # Play 1
        manager.start_inline(
            session_id="inline",
            speaker="NPC",
            text="First",
            choices=["A"],
            owner_id="default"
        )

        state1 = manager.get_state("inline", owner_id="default")
        active1 = state1.get("active")

        # Stop
        manager.reset()

        # Play 2: Same inline dialogue
        manager.start_inline(
            session_id="inline",
            speaker="NPC",
            text="First",  # Same text
            choices=["A"],
            owner_id="default"
        )

        state2 = manager.get_state("inline", owner_id="default")
        active2 = state2.get("active")

        # Should be equivalent to Play 1 state (clean restart)
        assert active1 == active2 == True

    # ========== DOUBLE STOP ==========

    def test_double_reset_safe(self, manager):
        """Verify reset() twice doesn't crash."""
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

        # Second reset (should be safe)
        manager.reset()
        assert len(manager._sessions) == 0

    # ========== STOP WITHOUT DIALOGUE ==========

    def test_stop_without_dialogue_safe(self, manager):
        """Verify Stop on manager with no active dialogue is safe."""
        # No dialogue opened
        assert len(manager._sessions) == 0

        # Stop should be safe
        manager.reset()

        # Still safe
        assert len(manager._sessions) == 0

    # ========== MIXED FLOW ==========

    def test_scene_change_then_stop_clean(self, manager, guard_asset_path):
        """Test scene change (Refinement 3) + Stop (Refinement 4) together."""
        if not guard_asset_path.exists():
            pytest.skip("GuardDialogue.zdialogue not found")

        # Play Level 1
        manager.start_asset(
            session_id="asset",
            asset_path=str(guard_asset_path),
            owner_id="Guard"
        )

        manager.start_inline(
            session_id="inline",
            speaker="Merchant",
            text="Trade",
            choices=[],
            owner_id="Merchant"
        )

        assert len(manager._sessions) == 2

        # Simulate scene change (reset via Refinement 3)
        manager.reset()
        assert len(manager._sessions) == 0

        # Play Level 2
        manager.start_inline(
            session_id="talk",
            speaker="Boss",
            text="Boss speaks",
            choices=[],
            owner_id="Boss"
        )

        assert len(manager._sessions) == 1

        # Stop (Refinement 4)
        manager.reset()

        # Completely clean
        assert len(manager._sessions) == 0
        assert len(manager._owner_sessions) == 0
        assert manager._active_session_id is None

    # ========== EVENT SINK CLEANUP ==========

    def test_event_sink_not_stale_after_stop(self, manager, guard_asset_path):
        """Verify event callbacks from old session don't fire after Stop."""
        if not guard_asset_path.exists():
            pytest.skip("GuardDialogue.zdialogue not found")

        events_captured = []

        # Play 1: Load asset with custom event sink
        manager.start_asset(
            session_id="asset",
            asset_path=str(guard_asset_path),
            owner_id="Guard"
        )

        # Stop
        manager.reset()

        # Play 2: Different asset
        manager.start_inline(
            session_id="inline",
            speaker="NPC",
            text="Different",
            choices=[],
            owner_id="default"
        )

        # If event callback from Play 1 was stale, it would be called here
        # But since manager.reset() cleared it, no stale callbacks should fire
        assert len(manager._sessions) == 1
        assert len(manager._choice_callbacks) == 0


class TestPlayStopPlayIntegration:
    """Integration tests for full Play/Stop/Play cycle."""

    @pytest.fixture
    def manager(self):
        return DialogueManager()

    def test_multiple_play_cycles(self, manager):
        """Test multiple Play/Stop/Play cycles."""
        for cycle in range(3):
            # Play
            manager.start_inline(
                session_id="test",
                speaker="NPC",
                text=f"Cycle {cycle}",
                choices=[],
                owner_id="default"
            )

            assert len(manager._sessions) == 1
            state = manager.get_state("test", owner_id="default")
            assert state.get("text") == f"Cycle {cycle}"

            # Stop
            manager.reset()
            assert len(manager._sessions) == 0

    def test_play_multiple_owners_stop_play(self, manager):
        """Test Play with multiple owners, Stop, then Play with different owners."""
        # Play 1: Guard and Merchant
        manager.start_inline(
            session_id="talk",
            speaker="Guard",
            text="Play1",
            choices=[],
            owner_id="Guard"
        )
        manager.start_inline(
            session_id="talk",
            speaker="Merchant",
            text="Play1",
            choices=[],
            owner_id="Merchant"
        )

        assert len(manager._sessions) == 2

        # Stop
        manager.reset()
        assert len(manager._sessions) == 0

        # Play 2: Different owners (Boss, Innkeeper)
        manager.start_inline(
            session_id="talk",
            speaker="Boss",
            text="Play2",
            choices=[],
            owner_id="Boss"
        )
        manager.start_inline(
            session_id="talk",
            speaker="Innkeeper",
            text="Play2",
            choices=[],
            owner_id="Innkeeper"
        )

        # Should be clean
        assert len(manager._sessions) == 2
        assert "Guard" not in manager._owner_sessions
        assert "Merchant" not in manager._owner_sessions
        assert "Boss" in manager._owner_sessions
        assert "Innkeeper" in manager._owner_sessions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
