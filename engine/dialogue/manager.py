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
        # Key: composite (owner_id, session_id) to allow same dialog_id with different owners
        self._sessions: Dict[tuple[str, str], DialogueSession] = {}
        self._active_session_id: Optional[tuple[str, str]] = None
        self._owner_sessions: Dict[str, tuple[str, str]] = {}  # owner_id → (owner_id, session_id)
        self._choice_callbacks: Dict[tuple[str, str], Callable[[int], None]] = {}
        self._session_counter = 0  # For generating unique session IDs

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
        Supports same session_id with different owner_id (via composite key).
        """
        try:
            # Composite key allows same dialog_id with different owners
            composite_key = (owner_id, session_id)

            if composite_key in self._sessions:
                return False  # Already active for this owner

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

            self._sessions[composite_key] = session
            self._active_session_id = composite_key
            self._owner_sessions[owner_id] = composite_key

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
        Uses composite key (owner_id, session_id) for owner isolation.
        """
        try:
            # Composite key allows same dialog_id with different owners
            composite_key = (owner_id, session_id)

            if composite_key in self._sessions:
                return False  # Already active for this owner

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
                event_sink=lambda event, payload: self._handle_dialogue_event(
                    composite_key, event, payload
                )
            )

            # IMPORTANT: Start the session to initialize state
            session.start()

            self._sessions[composite_key] = session
            self._active_session_id = composite_key
            self._owner_sessions[owner_id] = composite_key

            return True
        except Exception as e:
            print(f"[DialogueManager.start_asset] Error: {e}")
            return False

    def get_state(self, session_id: str, owner_id: str = "default") -> Dict[str, Any]:
        """
        Get current dialogue state (pure getter).

        Returns DialogueSession snapshot.
        Uses composite key (owner_id, session_id).
        """
        try:
            # Composite key lookup
            composite_key = (owner_id, session_id)
            session = self._sessions.get(composite_key)
            if session:
                return session.snapshot()
            return {}
        except Exception as e:
            print(f"[DialogueManager.get_state] Error: {e}")
            return {}

    def choose(self, session_id: str, choice_index: int, owner_id: str = "default") -> bool:
        """
        Player chooses an option.

        Advances DialogueSession through choice.
        Uses composite key (owner_id, session_id).
        """
        try:
            # Composite key lookup
            composite_key = (owner_id, session_id)
            session = self._sessions.get(composite_key)
            if not session or not session.active:
                return False

            # DialogueSession.choose() advances graph
            session.choose(choice_index)

            # Call choice callback if registered
            if composite_key in self._choice_callbacks:
                callback = self._choice_callbacks[composite_key]
                callback(choice_index)

            return True
        except Exception as e:
            print(f"[DialogueManager.choose] Error: {e}")
            return False

    def close(self, session_id: str, owner_id: str = "default") -> bool:
        """
        Close dialogue session.

        Removes session and clears owner routing.
        Uses composite key (owner_id, session_id).
        """
        try:
            # Composite key lookup
            composite_key = (owner_id, session_id)

            if composite_key not in self._sessions:
                return False

            del self._sessions[composite_key]

            if self._active_session_id == composite_key:
                self._active_session_id = None

            # Clear owner routing
            if self._owner_sessions.get(owner_id) == composite_key:
                del self._owner_sessions[owner_id]

            # Clear choice callback
            if composite_key in self._choice_callbacks:
                del self._choice_callbacks[composite_key]

            return True
        except Exception as e:
            print(f"[DialogueManager.close] Error: {e}")
            return False

    def get_active_session_key(self) -> Optional[tuple[str, str]]:
        """Get currently active session composite key (owner_id, session_id)."""
        return self._active_session_id

    def get_session_for_owner(self, owner_id: str) -> Optional[tuple[str, str]]:
        """Get composite session key (owner_id, session_id) for owner."""
        return self._owner_sessions.get(owner_id)

    def register_choice_callback(
        self,
        session_id: str,
        callback: Callable[[int], None],
        owner_id: str = "default"
    ) -> None:
        """Register callback for when choice is made (composite key)."""
        composite_key = (owner_id, session_id)
        self._choice_callbacks[composite_key] = callback

    def _handle_dialogue_event(
        self,
        composite_key: tuple[str, str],
        event_name: str,
        payload: Any
    ) -> None:
        """
        Handle dialogue events from DialogueSession.

        Routes to LogicEventBus with owner isolation.
        Composite key: (owner_id, session_id)
        """
        owner_id, session_id = composite_key
        try:
            # Try to dispatch via LogicEventBus
            from engine.logic.event_bus import LogicEventBus
            bus = LogicEventBus.get_instance()

            # Emit event with owner context
            event_data = {
                "owner_id": owner_id,
                "session_id": session_id,
                "event_name": event_name,
                "payload": payload,
            }
            bus.emit(f"dialogue:{event_name}", event_data)

        except ImportError:
            # LogicEventBus not available, just log
            print(f"[DialogueManager] Event: {event_name} (owner={owner_id}, session={session_id})")
        except Exception as e:
            print(f"[DialogueManager._handle_dialogue_event] Error: {e}")

    def set_variable(
        self,
        session_id: str,
        name: str,
        value: Any,
        owner_id: str = "default"
    ) -> bool:
        """Set dialogue variable (composite key)."""
        try:
            composite_key = (owner_id, session_id)
            session = self._sessions.get(composite_key)
            if session:
                session.set_variable(name, value)
                return True
            return False
        except Exception:
            return False

    def get_variable(
        self,
        session_id: str,
        name: str,
        default: Any = None,
        owner_id: str = "default"
    ) -> Any:
        """Get dialogue variable (composite key)."""
        try:
            composite_key = (owner_id, session_id)
            session = self._sessions.get(composite_key)
            if session:
                return session.variables.get(name, default)
            return default
        except Exception:
            return default

    def close_owner(self, owner_id: str) -> None:
        """
        Close all dialogue sessions for a specific owner.

        Used when scene changes or owner is destroyed.
        """
        try:
            # Find all sessions belonging to this owner
            keys_to_close = [
                key for key in self._sessions.keys()
                if key[0] == owner_id
            ]

            # Close each session
            for composite_key in keys_to_close:
                del self._sessions[composite_key]

                if self._active_session_id == composite_key:
                    self._active_session_id = None

                if composite_key in self._choice_callbacks:
                    del self._choice_callbacks[composite_key]

            # Clear owner mapping
            if owner_id in self._owner_sessions:
                del self._owner_sessions[owner_id]

        except Exception as e:
            print(f"[DialogueManager.close_owner] Error: {e}")

    def reset(self) -> None:
        """
        Reset all dialogue state.

        Used on Play/Stop/Play transitions or system shutdown.
        """
        try:
            self._sessions.clear()
            self._active_session_id = None
            self._owner_sessions.clear()
            self._choice_callbacks.clear()
            self._session_counter = 0
        except Exception as e:
            print(f"[DialogueManager.reset] Error: {e}")


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
