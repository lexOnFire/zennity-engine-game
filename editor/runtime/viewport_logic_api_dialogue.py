"""Dialogue helper methods for PlayLogicAPI."""
from __future__ import annotations


class PlayDialogueRuntimeMixin:
    def show_dialogue(self, dialog_id: str, speaker: str, text: str, choices: list[str] = None) -> bool:
        """
        Show inline dialogue with speaker and text.

        Canonical path: DialogueManager → DialogueSession
        """
        try:
            if choices is None:
                choices = []

            from engine.dialogue.manager import get_dialogue_manager

            manager = get_dialogue_manager()
            owner_id = self.name

            success = manager.start_inline(
                session_id=dialog_id,
                speaker=speaker,
                text=text,
                choices=choices,
                owner_id=owner_id
            )

            if success:
                self.obj.setdefault("_dialogue_choices", {})[dialog_id] = choices
                state = manager.get_state(dialog_id, owner_id=owner_id)
                self.obj.setdefault("logic_events", []).append({
                    "command": "show_dialogue_panel",
                    "value": {
                        "dialog_id": dialog_id,
                        "speaker": state.get("speaker", speaker),
                        "text": state.get("text", text),
                        "choices": choices,
                    }
                })

            return success
        except Exception as e:
            print(f"[PlayLogicAPI.show_dialogue] Error: {e}")
            return False

    def wait_dialogue_choice(self, dialog_id: str) -> int | None:
        """
        Check if dialogue choice was selected (pure getter).

        Returns choice index if last choice was made, None if still active.
        Tracks via internal _pending_choices dict for synchronization.
        """
        try:
            pending = self.obj.get("_pending_choices", {}).get(dialog_id)
            if pending is not None:
                return pending
            return None
        except Exception as e:
            print(f"[PlayLogicAPI.wait_dialogue_choice] Error: {e}")
            return None

    def set_dialogue_choice(self, dialog_id: str, choice_index: int) -> bool:
        """
        Set dialogue choice programmatically.

        For testing, AI, keyboard shortcuts.
        Routes through DialogueManager with owner isolation.
        """
        try:
            owner_id = self.name
            self.obj.setdefault("_pending_choices", {})[dialog_id] = int(choice_index)

            from engine.dialogue.manager import get_dialogue_manager
            manager = get_dialogue_manager()
            return manager.choose(dialog_id, choice_index, owner_id=owner_id)
        except Exception as e:
            print(f"[PlayLogicAPI.set_dialogue_choice] Error: {e}")
            return False

    def get_choice_text(self, dialog_id: str, choice_index: int) -> str:
        """
        Get text of specific choice (pure getter).

        Reads from cached dialogue choices.
        """
        try:
            choices_cache = self.obj.get("_dialogue_choices", {})
            choices = choices_cache.get(dialog_id, [])

            if 0 <= choice_index < len(choices):
                return str(choices[choice_index])

            return ""
        except Exception as e:
            print(f"[PlayLogicAPI.get_choice_text] Error: {e}")
            return ""

    def get_pending_choice(self, dialog_id: str) -> int | None:
        """
        Get pending choice index (internal helper for nodes).

        DEPRECATED: Use wait_dialogue_choice() or check DialogueSession directly.
        """
        return self.wait_dialogue_choice(dialog_id)

    def clear_pending_choice(self, dialog_id: str) -> None:
        """
        Clear pending choice (no-op for DialogueSession).

        DialogueSession manages state automatically.
        """
        pass

    def close_dialogue(self, dialog_id: str) -> bool:
        """
        Close dialogue session and clean up UI.

        Routes through DialogueManager with owner isolation.
        """
        try:
            owner_id = self.name
            from engine.dialogue.manager import get_dialogue_manager

            manager = get_dialogue_manager()
            success = manager.close(dialog_id, owner_id=owner_id)

            if success:
                self.obj.setdefault("logic_events", []).append({
                    "command": "hide_dialogue_panel",
                    "value": dialog_id
                })

            return success
        except Exception as e:
            print(f"[PlayLogicAPI.close_dialogue] Error: {e}")
            return False

