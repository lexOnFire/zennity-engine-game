#!/usr/bin/env python3
"""Test UI rendering in Play Mode - diagnostic script."""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Enable logging to see [UI] diagnostic messages
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)


def test_mainmenu_play_mode():
    """Simulate Play Mode startup for MainMenu."""
    print("\n" + "="*60)
    print("TEST: MainMenu Play Mode UI Rendering")
    print("="*60)

    try:
        # Import runtime classes
        from engine.runtime.runtime_scene import RuntimeScene
        from engine.scene.scene_loader import load_scene

        # Load scene
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        print(f"\n[1] Loading scene: {scene_path}")

        # Load editor scene
        scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
        print(f"[1] Scene loaded: {scene_data.get('scene_name')}")
        print(f"[1] Scene.ui field: {scene_data.get('ui')}")

        # Create runtime scene (this calls _compile_and_attach_ui)
        print(f"\n[2] Creating RuntimeScene...")

        runtime_scene = RuntimeScene(scene_path)

        print(f"[2] RuntimeScene created")
        print(f"[2] Scene game objects: {len(runtime_scene.scene.game_objects)}")
        for obj in runtime_scene.scene.game_objects:
            print(f"     - {obj.name}")

        # Check for Canvas
        print(f"\n[3] Searching for UICanvas...")

        ui_canvas = next((o for o in runtime_scene.scene.game_objects if "__UICanvas__" in o.name), None)

        if ui_canvas:
            print(f"[3] UICanvas FOUND: {ui_canvas.name}")
            print(f"[3] UICanvas children: {len(ui_canvas.children)}")
            for child in ui_canvas.children:
                print(f"     - {child.name}")
                if child.components:
                    for comp in child.components:
                        print(f"       component: {comp.component_type}")
        else:
            print(f"[3] UICanvas NOT FOUND")

        # Check scene game objects for widgets
        print(f"\n[4] Scanning for widget GameObjects...")
        widget_objects = [o for o in runtime_scene.scene.game_objects if o.name not in ["MainCamera", "MenuUI", "__UICanvas__"]]
        print(f"[4] Widget GameObjects found: {len(widget_objects)}")
        for obj in widget_objects[:10]:  # Show first 10
            print(f"     - {obj.name}")

        # Trace complete
        print(f"\n[5] UI RENDERING PIPELINE TRACE COMPLETE")
        print(f"[5] Canvas: {'FOUND' if ui_canvas else 'MISSING'}")
        print(f"[5] Widgets attached: {len(widget_objects)}")

        return True

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mainmenu_play_mode()
    sys.exit(0 if success else 1)
