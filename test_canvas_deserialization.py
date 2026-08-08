#!/usr/bin/env python3
"""Test that Canvas component deserializes correctly from scene JSON."""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from engine.core.component_registry import component_registry
from engine.ui.runtime_components import Canvas


def test_canvas_deserialization():
    """Test that Canvas component can be deserialized from scene data."""
    print("\n" + "="*60)
    print("TEST: Canvas Component Deserialization")
    print("="*60)

    # Load MainMenu scene
    scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
    data = json.loads(scene_path.read_text(encoding="utf-8"))

    # Find MenuUI object
    menu_ui = next((o for o in data["objects"] if o.get("name") == "MenuUI"), None)

    if not menu_ui:
        print("[FAIL] MenuUI object not found")
        return False

    print(f"[1] Found MenuUI object")

    # Get canvas component data
    components = menu_ui.get("components", {})
    canvas_data = components.get("canvas")

    if not canvas_data:
        print(f"[FAIL] No canvas component in MenuUI")
        return False

    print(f"[2] Found canvas component data")
    print(f"    Canvas data keys: {list(canvas_data.keys())}")
    print(f"    type field: {canvas_data.get('type')}")

    # Check for required type field
    if "type" not in canvas_data:
        print(f"[FAIL] Canvas component missing 'type' field")
        return False

    if canvas_data.get("type") != "Canvas":
        print(f"[FAIL] Canvas type incorrect: {canvas_data.get('type')}")
        return False

    print(f"[3] Canvas type field present and correct")

    # Try to create Canvas from component data
    try:
        print(f"[4] Attempting to deserialize Canvas component...")
        canvas = component_registry.create(canvas_data)

        # Check what type was created
        actual_type = type(canvas).__name__
        print(f"    Created type: {actual_type}")

        if isinstance(canvas, Canvas):
            print(f"[PASS] Canvas component correctly deserialized!")
            print(f"       Canvas.visible: {canvas.visible}")
            print(f"       Canvas.z_order: {canvas.z_order}")
            return True
        else:
            print(f"[FAIL] Wrong component type: {actual_type}")
            print(f"       Expected Canvas, got {type(canvas)}")
            return False

    except Exception as e:
        print(f"[FAIL] Deserialization failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_canvas_deserialization()
    sys.exit(0 if success else 1)
