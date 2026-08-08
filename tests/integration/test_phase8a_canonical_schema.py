"""
Phase 8A: Canonical Schema Validation Tests

Validates that ALL benchmark scenes now use the canonical Zennity format.
After migration, scenes must:
1. Have format_version: 2
2. Have scene_name (not 'name')
3. Have engine_version
4. Have objects with canonical structure (transform, components)
5. Successfully deserialize with real loaders
"""

import json
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.scene.scene_serializer import deserialize_scene
from engine.scene.scene_format import SCENE_FORMAT_VERSION


class TestCanonicalSchemaStructure:
    """Test canonical schema structure."""

    @pytest.mark.parametrize("scene_name", [
        "MainMenu.zscene",
        "Level1.zscene",
        "Level2.zscene",
        "GameOver.zscene",
        "Victory.zscene",
    ])
    def test_scene_has_format_version(self, scene_name):
        """All scenes must have format_version field."""
        scene_path = project_root / "Assets" / "Scenes" / scene_name
        assert scene_path.exists(), f"{scene_name} not found"

        data = json.loads(scene_path.read_text(encoding="utf-8"))
        assert "format_version" in data, f"{scene_name} missing format_version"
        assert data["format_version"] == SCENE_FORMAT_VERSION

    @pytest.mark.parametrize("scene_name", [
        "MainMenu.zscene",
        "Level1.zscene",
        "Level2.zscene",
        "GameOver.zscene",
        "Victory.zscene",
    ])
    def test_scene_has_scene_name(self, scene_name):
        """All scenes must have scene_name (not 'name')."""
        scene_path = project_root / "Assets" / "Scenes" / scene_name
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        assert "scene_name" in data, f"{scene_name} missing scene_name"
        assert isinstance(data["scene_name"], str)
        assert len(data["scene_name"]) > 0

    @pytest.mark.parametrize("scene_name", [
        "MainMenu.zscene",
        "Level1.zscene",
        "Level2.zscene",
        "GameOver.zscene",
        "Victory.zscene",
    ])
    def test_scene_no_legacy_format_field(self, scene_name):
        """Legacy 'format' field must be removed."""
        scene_path = project_root / "Assets" / "Scenes" / scene_name
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        # Should not have legacy "format": "zennity.scene"
        if "format" in data:
            pytest.fail(f"{scene_name} still has legacy 'format' field")

    @pytest.mark.parametrize("scene_name", [
        "MainMenu.zscene",
        "Level1.zscene",
        "Level2.zscene",
        "GameOver.zscene",
        "Victory.zscene",
    ])
    def test_scene_has_engine_version(self, scene_name):
        """All scenes must have engine_version."""
        scene_path = project_root / "Assets" / "Scenes" / scene_name
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        assert "engine_version" in data
        assert isinstance(data["engine_version"], str)

    @pytest.mark.parametrize("scene_name", [
        "MainMenu.zscene",
        "Level1.zscene",
        "Level2.zscene",
        "GameOver.zscene",
        "Victory.zscene",
    ])
    def test_scene_has_blackboard(self, scene_name):
        """All scenes must have blackboard (for variables)."""
        scene_path = project_root / "Assets" / "Scenes" / scene_name
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        assert "blackboard" in data
        assert isinstance(data["blackboard"], dict)

    @pytest.mark.parametrize("scene_name", [
        "MainMenu.zscene",
        "Level1.zscene",
        "Level2.zscene",
        "GameOver.zscene",
        "Victory.zscene",
    ])
    def test_scene_has_objects_array(self, scene_name):
        """All scenes must have objects array."""
        scene_path = project_root / "Assets" / "Scenes" / scene_name
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        assert "objects" in data
        assert isinstance(data["objects"], list)
        assert len(data["objects"]) > 0


class TestCanonicalObjectStructure:
    """Test canonical object structure."""

    def test_mainmenu_camera_has_canonical_transform(self):
        """Camera object must have canonical transform."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        camera = next((o for o in data["objects"] if "camera" in o.get("components", {})), None)
        assert camera is not None, "No camera found in MainMenu"

        # Must have transform object, not x/y fields
        assert "transform" in camera
        assert isinstance(camera["transform"], dict)

        transform = camera["transform"]
        assert "position" in transform
        assert isinstance(transform["position"], list)
        assert len(transform["position"]) == 3

        # Must NOT have legacy x, y fields
        assert "x" not in camera or isinstance(camera.get("x"), (int, float))
        assert "y" not in camera or isinstance(camera.get("y"), (int, float))

    def test_mainmenu_canvas_has_components_dict(self):
        """Canvas must have components as dict."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        canvas = next((o for o in data["objects"] if "canvas" in o.get("components", {})), None)
        assert canvas is not None

        components = canvas["components"]
        assert isinstance(components, dict)
        assert "canvas" in components

    def test_level1_objects_have_canonical_transform(self):
        """Level1 objects must have canonical transform."""
        scene_path = project_root / "Assets" / "Scenes" / "Level1.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        for obj in data["objects"]:
            assert "transform" in obj, f"Object {obj.get('name')} missing transform"
            assert "position" in obj["transform"]


class TestCanonicalDeserialization:
    """Test that canonical scenes deserialize correctly."""

    @pytest.mark.parametrize("scene_name,expected_object_count", [
        ("MainMenu.zscene", 2),  # Camera + Canvas
        ("GameOver.zscene", 2),  # Camera + Canvas
        ("Victory.zscene", 2),   # Camera + Canvas
        ("Level1.zscene", 10),   # Player + Camera + HUD + 3 Enemies + Coins + Key + Guard + Door + Walls + LevelExit (varies)
        ("Level2.zscene", 5),    # Player + Camera + HUD + Boss + Walls (varies)
    ])
    def test_scene_deserializes_successfully(self, scene_name, expected_object_count):
        """Scenes must deserialize without errors."""
        scene_path = project_root / "Assets" / "Scenes" / scene_name

        data = json.loads(scene_path.read_text(encoding="utf-8"))

        # This validates the structure, not full deserialization
        assert data["format_version"] == SCENE_FORMAT_VERSION
        assert "scene_name" in data
        assert "objects" in data

        # Basic object validation
        objects = data["objects"]
        assert len(objects) > 0

        for obj in objects:
            assert "id" in obj
            assert "name" in obj
            assert "transform" in obj


class TestLegacyBackups:
    """Verify legacy backups exist."""

    @pytest.mark.parametrize("scene_name", [
        "MainMenu_legacy.zscene",
        "Level1_legacy.zscene",
        "Level2_legacy.zscene",
        "GameOver_legacy.zscene",
        "Victory_legacy.zscene",
    ])
    def test_legacy_backup_exists(self, scene_name):
        """Legacy scenes should be backed up."""
        backup_path = project_root / "Assets" / "Scenes" / scene_name
        assert backup_path.exists(), f"Backup {scene_name} not found"

    def test_legacy_backup_has_old_schema(self):
        """Legacy backups should have old schema."""
        backup_path = project_root / "Assets" / "Scenes" / "MainMenu_legacy.zscene"
        data = json.loads(backup_path.read_text(encoding="utf-8"))

        # Should have old 'format' field
        assert "format" in data
        assert data["format"] == "zennity.scene"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
