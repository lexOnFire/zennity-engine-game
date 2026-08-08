"""
Save/Load game state management for Phase 7B.5.

Handles:
- Save game to JSON files
- Load game state from JSON
- Multi-slot save system
- Project variable persistence
- Error handling and validation
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class SaveManager:
    """Manages game save/load state. Singleton pattern."""

    def __init__(self, save_directory: str | Path = None) -> None:
        """Initialize SaveManager with save directory."""
        if save_directory is None:
            save_directory = Path.home() / ".zennity" / "saves"
        else:
            save_directory = Path(save_directory)

        self.save_directory = Path(save_directory)
        self.save_directory.mkdir(parents=True, exist_ok=True)

    def save_game(
        self,
        slot_name: str,
        project_variables: Dict[str, Any],
        scene_name: Optional[str] = None,
        scene_variables: Optional[Dict[str, Any]] = None,
        object_state: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Save game state to JSON file.

        Args:
            slot_name: Save slot identifier (no path traversal allowed)
            project_variables: Project-level variables to persist
            scene_name: Current scene name
            scene_variables: Scene-level variables (optional)
            object_state: Object state dict (optional)

        Returns:
            True if save successful, False otherwise
        """
        try:
            # Sanitize slot name (prevent path traversal)
            if not self._validate_slot_name(slot_name):
                return False

            save_data = {
                "format_version": 1,
                "slot_name": str(slot_name),
                "scene": str(scene_name) if scene_name else None,
                "project_variables": dict(project_variables) if project_variables else {},
                "scene_variables": dict(scene_variables) if scene_variables else {},
                "object_state": dict(object_state) if object_state else {},
            }

            save_path = self.save_directory / f"{slot_name}.json"

            # Atomic write: write to temp, then replace
            temp_path = self.save_directory / f".{slot_name}.tmp"

            with open(temp_path, "w") as f:
                json.dump(save_data, f, indent=2)

            # Replace atomically
            if temp_path.exists():
                temp_path.replace(save_path)

            return True

        except Exception as e:
            print(f"[SaveManager] Error saving game '{slot_name}': {type(e).__name__}: {e}")
            return False

    def load_game(self, slot_name: str) -> Optional[Dict[str, Any]]:
        """
        Load game state from JSON file.

        Args:
            slot_name: Save slot identifier

        Returns:
            Save data dict if successful, None otherwise
        """
        try:
            # Sanitize slot name
            if not self._validate_slot_name(slot_name):
                return None

            save_path = self.save_directory / f"{slot_name}.json"

            if not save_path.exists():
                return None

            with open(save_path, "r") as f:
                save_data = json.load(f)

            # Validate schema
            if not self._validate_save_data(save_data):
                return None

            return save_data

        except json.JSONDecodeError as e:
            print(f"[SaveManager] Invalid JSON in '{slot_name}': {e}")
            return None
        except Exception as e:
            print(f"[SaveManager] Error loading game '{slot_name}': {type(e).__name__}: {e}")
            return None

    def save_exists(self, slot_name: str) -> bool:
        """Check if save slot exists."""
        try:
            if not self._validate_slot_name(slot_name):
                return False

            save_path = self.save_directory / f"{slot_name}.json"
            return save_path.exists() and save_path.is_file()

        except Exception:
            return False

    def delete_save(self, slot_name: str) -> bool:
        """Delete save slot. Returns True if deleted or didn't exist."""
        try:
            if not self._validate_slot_name(slot_name):
                return False

            save_path = self.save_directory / f"{slot_name}.json"

            if save_path.exists():
                save_path.unlink()

            return True

        except Exception as e:
            print(f"[SaveManager] Error deleting save '{slot_name}': {e}")
            return False

    def _validate_slot_name(self, slot_name: str) -> bool:
        """Validate slot name (prevent path traversal attacks)."""
        if not isinstance(slot_name, str) or not slot_name:
            return False

        # Slot name must be alphanumeric + underscore only
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")

        if not all(c in allowed_chars for c in slot_name):
            return False

        # Max length safety
        if len(slot_name) > 32:
            return False

        return True

    def _validate_save_data(self, save_data: Dict[str, Any]) -> bool:
        """Validate save data schema."""
        if not isinstance(save_data, dict):
            return False

        # Required fields
        required_fields = ["format_version", "project_variables"]
        if not all(field in save_data for field in required_fields):
            return False

        # Version check
        version = save_data.get("format_version")
        if not isinstance(version, int) or version != 1:
            print(f"[SaveManager] Unsupported save format version: {version}")
            return False

        # Validate variable dicts
        if not isinstance(save_data.get("project_variables"), dict):
            return False

        return True


# Singleton instance
_save_manager: Optional[SaveManager] = None


def get_save_manager() -> SaveManager:
    """Get or create SaveManager singleton."""
    global _save_manager
    if _save_manager is None:
        _save_manager = SaveManager()
    return _save_manager


def set_save_manager(manager: SaveManager) -> None:
    """Set SaveManager instance (for testing)."""
    global _save_manager
    _save_manager = manager
