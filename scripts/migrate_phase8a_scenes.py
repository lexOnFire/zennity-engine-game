#!/usr/bin/env python3
"""
Migrate Phase 8A benchmark scenes from legacy schema to canonical format.

The benchmark scenes were created with a custom JSON schema that doesn't match
the canonical Zennity scene format. This tool converts them to the canonical
format using the real engine serializers.

Usage:
    python scripts/migrate_phase8a_scenes.py
"""

import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.scene.scene_format import SCENE_FORMAT_VERSION, ENGINE_VERSION, DEFAULT_SCENE_NAME
from engine.game_object import GameObject
from engine.scene.scene_serializer import serialize_game_object


def migrate_legacy_scene_to_canonical(legacy_data: dict) -> dict:
    """
    Convert legacy benchmark scene format to canonical Zennity format.

    Legacy format example (WRONG):
    {
        "format": "zennity.scene",
        "name": "Main Menu",
        "objects": [...],
        "variables": {...}
    }

    Canonical format (CORRECT):
    {
        "format_version": 2,
        "scene_name": "Main Menu",
        "engine_version": "Zennity 0.1.0",
        "blackboard": {"variables": {...}},
        "objects": [...]
    }
    """

    # Extract scene metadata
    scene_name = legacy_data.get("name") or legacy_data.get("scene_name") or DEFAULT_SCENE_NAME

    # Extract variables (legacy had them at root, canonical puts in blackboard)
    variables = legacy_data.get("variables", {})

    # Extract and convert objects
    legacy_objects = legacy_data.get("objects", [])
    canonical_objects = []
    scene_ui_asset = None  # Track UI asset for scene root

    for obj in legacy_objects:
        canonical_obj = _convert_legacy_object(obj)
        if canonical_obj:
            canonical_objects.append(canonical_obj)
            # Extract UI asset from Canvas object if present
            obj_type = obj.get("type")
            has_ui = "ui" in obj
            if obj_type == "Canvas" and has_ui:
                scene_ui_asset = obj["ui"].get("asset")

    # Build canonical scene
    canonical_scene = {
        "format_version": SCENE_FORMAT_VERSION,
        "scene_name": str(scene_name),
        "engine_version": ENGINE_VERSION,
        "blackboard": {
            "variables": variables
        },
        "objects": canonical_objects
    }

    # CRITICAL: Keep UI asset at scene root for RuntimeScene.ui lookup
    # RuntimeScene._compile_and_attach_ui() expects scene.ui (root level)
    if scene_ui_asset:
        canonical_scene["ui"] = scene_ui_asset

    return canonical_scene


def _convert_legacy_object(legacy_obj: dict) -> dict[str, Any]:
    """Convert a legacy object to canonical format."""

    canonical_obj = {
        "id": legacy_obj.get("id", "obj_" + legacy_obj.get("name", "unknown")),
        "name": legacy_obj.get("name", "GameObject"),
        "active": legacy_obj.get("active", True),
        "tag": legacy_obj.get("tag", ""),
    }

    # Handle transform
    if "x" in legacy_obj or "y" in legacy_obj or "transform" in legacy_obj:
        transform = legacy_obj.get("transform")
        if isinstance(transform, dict):
            # Already in canonical format
            canonical_obj["transform"] = transform
        else:
            # Convert from x, y format
            x = legacy_obj.get("x", 0)
            y = legacy_obj.get("y", 0)
            z = legacy_obj.get("z", 0)

            canonical_obj["transform"] = {
                "position": [float(x), float(y), float(z)],
                "rotation": [0.0, 0.0, 0.0],
                "rz": 0.0,
                "scale": [1.0, 1.0, 1.0]
            }
    else:
        # Default transform
        canonical_obj["transform"] = {
            "position": [0.0, 0.0, 0.0],
            "rotation": [0.0, 0.0, 0.0],
            "rz": 0.0,
            "scale": [1.0, 1.0, 1.0]
        }

    # Handle components
    components = {}

    # Special handling for legacy "type" field
    legacy_type = legacy_obj.get("type")
    if legacy_type:
        if legacy_type == "Camera2D":
            camera_data = legacy_obj.get("camera", {})
            components["camera"] = {
                "zoom": camera_data.get("zoom", 1.0),
                "background_color": camera_data.get("clear_color", [30, 30, 30]),
                "viewport_rect": [0.0, 0.0, 1.0, 1.0],
                "priority": 0,
                "active": True
            }
        elif legacy_type == "Canvas":
            # Canvas becomes canvas component with type field for deserialization
            ui_data = legacy_obj.get("ui", {})
            asset_path = ui_data.get("asset", "") or legacy_obj.get("layout_path", "")
            components["canvas"] = {
                "type": "Canvas",  # CRITICAL: Required for component_registry.create()
                "layout_path": asset_path,
                "ui_asset": asset_path,
                "visible": True,
                "z_order": 0,
                "render_mode": "Screen Space",
                "layer_mask": 0xFFFFFFFF
            }

            # Logic graphs attach to canvas
            if "logic_graphs" in legacy_obj:
                components["logic_graphs"] = legacy_obj.get("logic_graphs", [])

    # Standard components (handle both dict and list formats)
    if "components" in legacy_obj:
        legacy_components = legacy_obj.get("components", {})
        if isinstance(legacy_components, dict):
            components.update(legacy_components)
        elif isinstance(legacy_components, list):
            # Convert list of components to dict format
            for comp in legacy_components:
                if isinstance(comp, dict):
                    comp_type = comp.get("type", "unknown").lower()
                    components[comp_type] = comp

    if components:
        canonical_obj["components"] = components

    # Copy other standard fields
    if "enabled" in legacy_obj:
        canonical_obj["enabled"] = legacy_obj.get("enabled", True)

    if "static" in legacy_obj:
        canonical_obj["static"] = legacy_obj.get("static", False)

    if "layer" in legacy_obj:
        canonical_obj["layer"] = legacy_obj.get("layer", "Default")

    # Handle prefab references
    if "prefab" in legacy_obj:
        canonical_obj["prefab"] = legacy_obj.get("prefab")

    return canonical_obj


def migrate_file(filepath: Path) -> bool:
    """
    Migrate a single .zscene file from legacy to canonical format.

    Returns:
        True if successful, False otherwise.
    """
    print(f"\n Migrating: {filepath.name}")

    # Read legacy file
    try:
        legacy_data = json.loads(filepath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"   Failed to parse JSON: {e}")
        return False
    except Exception as e:
        print(f"   Failed to read file: {e}")
        return False

    # Convert to canonical
    try:
        canonical_data = migrate_legacy_scene_to_canonical(legacy_data)
    except Exception as e:
        print(f"   Failed to convert: {e}")
        return False

    # Write canonical file (backup original first)
    try:
        backup_path = filepath.with_suffix(".zscene.bak")
        if not backup_path.exists():
            filepath.write_text(
                json.dumps(legacy_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            backup_path = filepath.parent / f"{filepath.stem}_legacy.zscene"
            if not backup_path.exists():
                filepath.rename(backup_path)
                print(f"   Backup saved: {backup_path.name}")

        # Write canonical version
        canonical_json = json.dumps(canonical_data, indent=2, ensure_ascii=False)
        filepath.write_text(canonical_json, encoding="utf-8")

        print(f"   Migrated to canonical format")
        print(f"     - format_version: {canonical_data.get('format_version')}")
        print(f"     - scene_name: {canonical_data.get('scene_name')}")
        print(f"     - objects: {len(canonical_data.get('objects', []))}")

        return True

    except Exception as e:
        print(f"   Failed to write file: {e}")
        return False


def main():
    """Migrate all Phase 8A benchmark scenes."""

    print("[MIGRATE] Phase 8A Benchmark Scene Migration Tool")
    print("=" * 60)

    benchmark_scenes = [
        project_root / "Assets" / "Scenes" / "MainMenu.zscene",
        project_root / "Assets" / "Scenes" / "Level1.zscene",
        project_root / "Assets" / "Scenes" / "Level2.zscene",
        project_root / "Assets" / "Scenes" / "GameOver.zscene",
        project_root / "Assets" / "Scenes" / "Victory.zscene",
    ]

    results = []
    for scene_path in benchmark_scenes:
        if not scene_path.exists():
            print(f"\n  Not found: {scene_path.name}")
            results.append((scene_path.name, False))
            continue

        success = migrate_file(scene_path)
        results.append((scene_path.name, success))

    # Summary
    print("\n" + "=" * 60)
    print(" Migration Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)

    for name, success in results:
        status = " PASS" if success else " FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed} migrated, {failed} failed")

    if failed == 0:
        print("\n All scenes successfully migrated!")
        print("Next step: Verify all scenes open in Zennity editor")
        return 0
    else:
        print(f"\n  {failed} scene(s) failed to migrate")
        return 1


if __name__ == "__main__":
    sys.exit(main())
