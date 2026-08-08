"""
Phase 7B.7.1: DialogueManager - Unified dialogue orchestration.

Consolidates all dialogue management through DialogueSession.
Single source of truth for dialogue state.

Replaces parallel implementations:
- .zdialogue files via DialogueSession
- Logic Graph inline dialogue via PlayLogicAPI adapter

Architecture:
  .zdialogue asset → DialogueManager.start_asset()
  Inline dialogue  → DialogueManager.start_inline()

  Both route through DialogueSession
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Callable

try:
    from engine.dialogue.runtime import DialogueSession
except ImportError:
    from .runtime import DialogueSession


class DialogueManager:
    """
    Unified dialogue management orchestrator.

    Canonical source of truth for all dialogue state.
    Routes both asset-based (.zdialogue) and inline conversations
    through DialogueSession.
    """

    def __init__(self) -> None:
        """Initialize dialogue manager."""
        self._sessions: Dict[str, DialogueSession] = {}
        self._active_session_id: Optional[str] = None
        self._owner_sessions: Dict[str, str] = {}  # owner_id → session_id
        self._choice_callbacks: Dict[str, Callable[[int], None]] = {}

    def start_inline(
        self,
        session_id: str,
        speaker: str,
        text: str,
        choices: list[str],
        owner_id: str = "default",
        variables: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Start inline dialogue (simple Logic Graph case).

        Creates minimal DialogueSession for inline conversation.
        """
        try:
            if session_id in self._sessions:
                return False  # Already active

            # Build minimal dialogue graph JSON
            nodes = []
            edges = []

            # Speech node
            nodes.append({
                "id": "speech_0",
                "type": "dialogue.speech",
                "inputs": {
                    "speaker": speaker,
                    "text": text,
                },
                "outputs": ["out"],
            })

            # Choice node if choices provided
            if choices:
                choice_inputs = {"prompt": "Choose:"}
                choice_outputs = [f"option_{i}" for i in range(len(choices))]

                nodes.append({
                    "id": "choice_1",
                    "type": "dialogue.choice",
                    "inputs": choice_inputs,
                    "outputs": choice_outputs,
                })

                # Connect speech → choice
                edges.append({
                    "source_node": "speech_0",
                    "source_port": "out",
                    "target_node": "choice_1",
                    "target_port": "in",
                })

                # End node
                nodes.append({
                    "id": "end_2",
                    "type": "dialogue.end",
                    "inputs": {"in": None},
                    "outputs": [],
                })

                # Connect choice → end for all options
                for i in range(len(choices)):
                    edges.append({
                        "source_node": "choice_1",
                        "source_port": f"option_{i}",
                        "target_node": "end_2",
                        "target_port": "in",
                    })
            else:
                # No choices, just speech → end
                nodes.append({
                    "id": "end_2",
                    "type": "dialogue.end",
                    "inputs": {"in": None},
                    "outputs": [],
                })

                edges.append({
                    "source_node": "speech_0",
                    "source_port": "out",
                    "target_node": "end_2",
                    "target_port": "in",
                })

            # Build dialogue graph
            graph = {
                "format": "zennity.generic_graph",
                "category": "Dialogue",
                "nodes": nodes,
                "edges": edges,
                "variables": variables or {},
            }

            # Create DialogueSession (canonical runtime)
            session = DialogueSession(graph, variables=variables or {})

            # IMPORTANT: Start the session to initialize state
            session.start()

            self._sessions[session_id] = session
            self._active_session_id = session_id
            self._owner_sessions[owner_id] = session_id

            return True
        except Exception as e:
            print(f"[DialogueManager.start_inline] Error: {e}")
            return False

    def start_asset(
        self,
        session_id: str,
        asset_path: str,
        owner_id: str = "default",
        variables: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Start dialogue from .zdialogue asset file.

        Loads dialogue graph JSON and creates DialogueSession.
        """
        try:
            if session_id in self._sessions:
                return False  # Already active

            # Resolve asset path
            asset_file = Path(asset_path)
            if not asset_file.exists():
                return False

            # Load dialogue graph JSON
            graph_data = json.loads(asset_file.read_text(encoding="utf-8"))

            # Create DialogueSession (canonical runtime)
            session = DialogueSession(
                graph_data,
                variables=variables or {},
                event_sink=self._handle_dialogue_event
            )

            # IMPORTANT: Start the session to initialize state
            session.start()

            self._sessions[session_id] = session
            self._active_session_id = session_id
            self._owner_sessions[owner_id] = session_id

            return True
        except Exception as e:
            print(f"[DialogueManager.start_asset] Error: {e}")
            return False

    def get_state(self, session_id: str) -> Dict[str, Any]:
        """
        Get current dialogue state (pure getter).

        Returns DialogueSession snapshot.
        """
        try:
            session = self._sessions.get(session_id)
            if session:
                return session.snapshot()
            return {}
        except Exception as e:
            print(f"[DialogueManager.get_state] Error: {e}")
            return {}

    def choose(self, session_id: str, choice_index: int) -> bool:
        """
        Player chooses an option.

        Advances DialogueSession through choice.
        """
        try:
            session = self._sessions.get(session_id)
            if not session or not session.active:
                return False

            # DialogueSession.choose() advances graph
            session.choose(choice_index)

            # Call choice callback if registered
            if session_id in self._choice_callbacks:
                callback = self._choice_callbacks[session_id]
                callback(choice_index)

            return True
        except Exception as e:
            print(f"[DialogueManager.choose] Error: {e}")
            return False

    def close(self, session_id: str) -> bool:
        """
        Close dialogue session.

        Removes session and clears owner routing.
        """
        try:
            if session_id not in self._sessions:
                return False

            del self._sessions[session_id]

            if self._active_session_id == session_id:
                self._active_session_id = None

            # Clear owner routing
            owner_id = next(
                (owner for owner, sid in self._owner_sessions.items() if sid == session_id),
                None
            )
            if owner_id:
                del self._owner_sessions[owner_id]

            # Clear choice callback
            if session_id in self._choice_callbacks:
                del self._choice_callbacks[session_id]

            return True
        except Exception as e:
            print(f"[DialogueManager.close] Error: {e}")
            return False

    def get_active_session_id(self) -> Optional[str]:
        """Get currently active session ID (pure getter)."""
        return self._active_session_id

    def get_session_for_owner(self, owner_id: str) -> Optional[str]:
        """Get session ID for a specific owner (pure getter)."""
        return self._owner_sessions.get(owner_id)

    def register_choice_callback(
        self,
        session_id: str,
        callback: Callable[[int], None]
    ) -> None:
        """Register callback for when choice is made."""
        self._choice_callbacks[session_id] = callback

    def _handle_dialogue_event(self, event_name: str, payload: Any) -> None:
        """Handle dialogue events (dialogue.event nodes)."""
        # Dispatch via LogicEventBus if available
        # For now, just log
        print(f"[DialogueManager] Event: {event_name}, payload: {payload}")

    def set_variable(self, session_id: str, name: str, value: Any) -> bool:
        """Set dialogue variable."""
        try:
            session = self._sessions.get(session_id)
            if session:
                session.set_variable(name, value)
                return True
            return False
        except Exception:
            return False

    def get_variable(self, session_id: str, name: str, default: Any = None) -> Any:
        """Get dialogue variable."""
        try:
            session = self._sessions.get(session_id)
            if session:
                return session.variables.get(name, default)
            return default
        except Exception:
            return default


# Singleton instance
_dialogue_manager: Optional[DialogueManager] = None


def get_dialogue_manager() -> DialogueManager:
    """Get or create DialogueManager singleton."""
    global _dialogue_manager
    if _dialogue_manager is None:
        _dialogue_manager = DialogueManager()
    return _dialogue_manager


def set_dialogue_manager(manager: Optional[DialogueManager]) -> None:
    """Set DialogueManager instance (for testing)."""
    global _dialogue_manager
    _dialogue_manager = manager
