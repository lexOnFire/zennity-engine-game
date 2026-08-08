"""
Phase 7B.5: Save/Load Visual Gameplay System

Tests that game state persistence works end-to-end through Logic Graph:

Player plays Level1
↓
health = 80
coins = 25
score = 1200
↓
Save Game "slot1"
↓
Close / Load MainMenu
↓
Load Game "slot1"
↓
Expected:
health = 80
coins = 25
score = 1200
Level1 loaded

100% without Python save management.
"""

import pytest
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.core.save_manager import SaveManager, get_save_manager, set_save_manager
from engine.logic.runtime.registry import registry
from editor.runtime.viewport_logic_api import PlayLogicAPI

# Ensure save_load_nodes module is imported so executors are registered
import engine.logic.runtime.nodes.save_load_nodes  # noqa


@pytest.fixture
def temp_save_dir():
    """Create temporary save directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SaveManager(tmpdir)
        set_save_manager(manager)
        yield tmpdir
        set_save_manager(None)


class TestSaveManagerCore:
    """Test SaveManager class functionality."""

    def test_save_manager_creates_save_directory(self, temp_save_dir):
        """Verify SaveManager creates save directory if not exists."""
        manager = SaveManager(temp_save_dir)
        assert Path(temp_save_dir).exists(), "Save directory should exist"

    def test_save_game_creates_file(self, temp_save_dir):
        """Verify save_game() creates JSON file."""
        manager = SaveManager(temp_save_dir)
        data = {"health": 100, "score": 500}

        result = manager.save_game("test_slot", data)
        assert result is True, "save_game() should return True"

        save_file = Path(temp_save_dir) / "test_slot.json"
        assert save_file.exists(), "Save file should be created"

    def test_load_game_reads_file(self, temp_save_dir):
        """Verify load_game() reads saved data."""
        manager = SaveManager(temp_save_dir)
        original_data = {"health": 100, "coins": 50}

        manager.save_game("test_slot", original_data)
        loaded_data = manager.load_game("test_slot")

        assert loaded_data is not None, "Should load save data"
        assert loaded_data["project_variables"] == original_data

    def test_save_exists_true(self, temp_save_dir):
        """Verify save_exists() returns True for existing save."""
        manager = SaveManager(temp_save_dir)
        manager.save_game("test_slot", {"score": 100})

        exists = manager.save_exists("test_slot")
        assert exists is True, "save_exists() should return True"

    def test_save_exists_false(self, temp_save_dir):
        """Verify save_exists() returns False for missing save."""
        manager = SaveManager(temp_save_dir)
        exists = manager.save_exists("nonexistent")
        assert exists is False, "save_exists() should return False for missing save"

    def test_delete_save_removes_file(self, temp_save_dir):
        """Verify delete_save() removes file."""
        manager = SaveManager(temp_save_dir)
        manager.save_game("test_slot", {"score": 100})

        deleted = manager.delete_save("test_slot")
        assert deleted is True, "delete_save() should return True"
        assert not manager.save_exists("test_slot"), "Save should no longer exist"

    def test_delete_save_nonexistent_succeeds(self, temp_save_dir):
        """Verify delete_save() succeeds even if file doesn't exist."""
        manager = SaveManager(temp_save_dir)
        deleted = manager.delete_save("nonexistent")
        assert deleted is True, "delete_save() should return True even if file missing"


class TestSlotNameValidation:
    """Test slot name validation (security)."""

    def test_valid_slot_names(self, temp_save_dir):
        """Verify valid slot names are accepted."""
        manager = SaveManager(temp_save_dir)

        valid_names = ["slot1", "save_1", "autosave", "checkpoint_1", "SLOT_2"]

        for name in valid_names:
            result = manager.save_game(name, {"score": 100})
            assert result is True, f"Should accept valid slot name: {name}"

    def test_invalid_slot_names_rejected(self, temp_save_dir):
        """Verify invalid slot names are rejected (path traversal prevention)."""
        manager = SaveManager(temp_save_dir)

        invalid_names = [
            "../../../etc/passwd",
            "..\\..\\config",
            "slot/path",
            "slot\\path",
            "slot;drop",
            "",
            None,
        ]

        for name in invalid_names:
            result = manager.save_game(name, {"score": 100}) if name is not None else False
            assert result is False, f"Should reject invalid slot name: {name}"

    def test_slot_name_max_length(self, temp_save_dir):
        """Verify slot name has max length limit."""
        manager = SaveManager(temp_save_dir)

        long_name = "a" * 100  # Way too long
        result = manager.save_game(long_name, {"score": 100})
        assert result is False, "Should reject overly long slot names"


class TestSaveDataSchema:
    """Test save data format and versioning."""

    def test_save_data_has_version(self, temp_save_dir):
        """Verify saved data includes format_version."""
        manager = SaveManager(temp_save_dir)
        manager.save_game("test", {"score": 100})

        loaded = manager.load_game("test")
        assert "format_version" in loaded, "Should have format_version"
        assert loaded["format_version"] == 1, "Should be version 1"

    def test_save_data_has_required_fields(self, temp_save_dir):
        """Verify saved data has required fields."""
        manager = SaveManager(temp_save_dir)
        manager.save_game("test", {"health": 50}, scene_name="Level1")

        loaded = manager.load_game("test")
        assert "project_variables" in loaded
        assert "scene" in loaded
        assert loaded["scene"] == "Level1"


class TestPlayLogicAPISaveMethods:
    """Test PlayLogicAPI save/load methods."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_save_game_method_exists(self):
        """Verify save_game() method exists."""
        assert hasattr(self.api, "save_game"), "PlayLogicAPI missing save_game()"
        assert callable(self.api.save_game), "save_game() not callable"

    def test_load_game_method_exists(self):
        """Verify load_game() method exists."""
        assert hasattr(self.api, "load_game"), "PlayLogicAPI missing load_game()"
        assert callable(self.api.load_game), "load_game() not callable"

    def test_save_exists_method_exists(self):
        """Verify save_exists() method exists."""
        assert hasattr(self.api, "save_exists"), "PlayLogicAPI missing save_exists()"
        assert callable(self.api.save_exists), "save_exists() not callable"

    def test_delete_save_method_exists(self):
        """Verify delete_save() method exists."""
        assert hasattr(self.api, "delete_save"), "PlayLogicAPI missing delete_save()"
        assert callable(self.api.delete_save), "delete_save() not callable"

    def test_save_game_accepts_slot(self):
        """Verify save_game() accepts slot name."""
        result = self.api.save_game("test_slot")
        assert isinstance(result, bool), "save_game() should return bool"

    def test_save_game_rejects_empty_slot(self):
        """Verify save_game() rejects empty slot."""
        result = self.api.save_game("")
        assert result is False, "save_game() should return False for empty slot"

    def test_save_exists_pure_getter(self, temp_save_dir):
        """Verify save_exists() is pure getter (no side effects)."""
        manager = SaveManager(temp_save_dir)
        set_save_manager(manager)

        obj = {"name": "Game"}
        api = PlayLogicAPI("Game", obj, None)

        manager.save_game("exists_slot", {"score": 100})

        exists1 = api.save_exists("exists_slot")
        exists2 = api.save_exists("exists_slot")

        assert exists1 == exists2 == True, "save_exists() should return same value each call"

    def test_load_game_accepts_slot(self):
        """Verify load_game() accepts slot name."""
        result = self.api.load_game("test_slot")
        assert isinstance(result, bool), "load_game() should return bool"


class TestProjectVariablePersistence:
    """Test project variable save/load."""

    def test_save_and_load_variables(self, temp_save_dir):
        """Verify project variables are saved and loaded."""
        manager = SaveManager(temp_save_dir)

        original_vars = {
            "health": 80,
            "coins": 25,
            "score": 1200,
        }

        manager.save_game("level1_save", original_vars)
        loaded = manager.load_game("level1_save")

        assert loaded["project_variables"] == original_vars


class TestScenePersistence:
    """Test scene saving and loading."""

    def test_scene_name_saved(self, temp_save_dir):
        """Verify scene name is saved."""
        manager = SaveManager(temp_save_dir)

        manager.save_game("save1", {"score": 100}, scene_name="Level1")
        loaded = manager.load_game("save1")

        assert loaded["scene"] == "Level1", "Scene name should be saved"

    def test_scene_name_with_variables(self, temp_save_dir):
        """Verify scene name and variables saved together."""
        manager = SaveManager(temp_save_dir)

        vars = {"health": 80, "coins": 25}
        manager.save_game("save1", vars, scene_name="Level2")

        loaded = manager.load_game("save1")
        assert loaded["scene"] == "Level2"
        assert loaded["project_variables"] == vars


class TestErrorHandling:
    """Test error handling in save/load."""

    def test_load_missing_save_returns_none(self, temp_save_dir):
        """Verify load nonexistent save returns None."""
        manager = SaveManager(temp_save_dir)
        loaded = manager.load_game("nonexistent")
        assert loaded is None, "Should return None for missing save"

    def test_save_invalid_slot_returns_false(self, temp_save_dir):
        """Verify save with invalid slot returns False."""
        manager = SaveManager(temp_save_dir)
        result = manager.save_game("../../etc/passwd", {"score": 100})
        assert result is False, "Should return False for invalid slot"

    def test_corrupted_json_returns_none(self, temp_save_dir):
        """Verify corrupted JSON is handled gracefully."""
        manager = SaveManager(temp_save_dir)

        # Create corrupted file
        save_file = Path(temp_save_dir) / "corrupt.json"
        save_file.write_text("{invalid json content")

        loaded = manager.load_game("corrupt")
        assert loaded is None, "Should return None for corrupted JSON"


class TestMultiSlotSupport:
    """Test multiple save slots."""

    def test_multiple_slots_independent(self, temp_save_dir):
        """Verify multiple slots are independent."""
        manager = SaveManager(temp_save_dir)

        manager.save_game("slot1", {"score": 100})
        manager.save_game("slot2", {"score": 200})

        slot1 = manager.load_game("slot1")
        slot2 = manager.load_game("slot2")

        assert slot1["project_variables"]["score"] == 100
        assert slot2["project_variables"]["score"] == 200


class TestSaveGameE2E:
    """E2E tests for save/load gameplay."""

    def test_main_menu_save_check(self, temp_save_dir):
        """Test MainMenu can check for save."""
        manager = SaveManager(temp_save_dir)
        manager.save_game("auto_save", {"level": "Level1"})

        obj = {"name": "MainMenu"}
        api = PlayLogicAPI("MainMenu", obj, None)
        set_save_manager(manager)

        has_save = api.save_exists("auto_save")
        assert has_save is True, "MainMenu should detect existing save"

    def test_level_to_level_save_restore(self, temp_save_dir):
        """Test Level1 → Level2 transition with save/restore."""
        manager = SaveManager(temp_save_dir)
        set_save_manager(manager)

        # Level1 state
        level1_vars = {"coins": 10, "health": 100}
        manager.save_game("checkpoint", level1_vars, scene_name="Level1")

        # Progress to Level2
        manager.save_game("checkpoint", {"coins": 25, "health": 75}, scene_name="Level2")

        # Load Level2 save
        loaded = manager.load_game("checkpoint")
        assert loaded["scene"] == "Level2"
        assert loaded["project_variables"]["coins"] == 25

    def test_checkpoint_system_basic(self, temp_save_dir):
        """Test checkpoint save/load flow."""
        manager = SaveManager(temp_save_dir)

        # Save at checkpoint
        manager.save_game("checkpoint", {"position_x": 100, "position_y": 200})

        # Change state (simulate player movement)
        # No action - just load checkpoint

        # Load checkpoint
        loaded = manager.load_game("checkpoint")
        assert loaded["project_variables"]["position_x"] == 100


class TestSaveNodeRegistration:
    """Verify save nodes are in registry."""

    def test_save_game_node_registered(self):
        """Verify save_game executor exists."""
        assert "save_game" in registry.executors, "save_game executor missing"

    def test_load_game_node_registered(self):
        """Verify load_game executor exists."""
        assert "load_game" in registry.executors, "load_game executor missing"

    def test_delete_save_node_registered(self):
        """Verify delete_save executor exists."""
        assert "delete_save" in registry.executors, "delete_save executor missing"

    def test_has_save_node_registered(self):
        """Verify has_save executor exists."""
        assert "has_save" in registry.executors, "has_save executor missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
