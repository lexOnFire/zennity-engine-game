#!/usr/bin/env python3
"""Integration test: MainMenu UI rendering pipeline end-to-end."""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pygame
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def test_mainmenu_ui_pipeline():
    """Full integration test of MainMenu UI rendering."""
    print("\n" + "="*60)
    print("INTEGRATION TEST: MainMenu UI Rendering Pipeline")
    print("="*60)

    try:
        pygame.init()

        # Step 1: Load MainMenu.zscene
        print("\n[1] Loading MainMenu.zscene...")
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        scene_data = json.loads(scene_path.read_text(encoding="utf-8"))
        print(f"    Scene: {scene_data.get('scene_name')}")
        print(f"    UI asset: {scene_data.get('ui')}")

        # Step 2: Load and compile UI
        print("\n[2] Loading and compiling MainMenu.zui...")
        from engine.ui.asset_loader import UIAssetLoader
        from engine.ui.runtime_compiler import UIRuntimeCompiler

        loader = UIAssetLoader(project_root=project_root)
        ui_doc = loader.load(scene_data.get("ui"))
        print(f"    Document loaded")

        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(ui_doc)
        print(f"    Widgets compiled: {len(compiled_widgets)}")

        # Step 3: Create mock runtime scene with proper structure
        print("\n[3] Creating mock runtime scene with UI components...")
        from engine.ui.runtime_components import Canvas, LabelComponent, ButtonComponent, ImageComponent
        from engine.game_object import GameObject

        class MockScene:
            def __init__(self):
                self.game_objects = []
                self.editable_objects = []

        scene = MockScene()

        # Add Canvas
        canvas = Canvas()
        canvas_go = GameObject("Canvas")
        canvas_go.add_component(canvas)
        scene.game_objects.append(canvas_go)
        scene.editable_objects.append(canvas_go)
        print(f"    Canvas added")

        # Add widgets based on compiled data
        widget_count = 0
        for widget_def in compiled_widgets:
            if not widget_def:
                continue

            widget_type = widget_def.get("type")
            widget_name = widget_def.get("widget_name")
            props = widget_def.get("properties", {})

            # Skip unknown types for this test
            if widget_type not in ["LabelComponent", "ButtonComponent", "ImageComponent"]:
                continue

            go = GameObject(widget_name)

            if widget_type == "LabelComponent":
                comp = LabelComponent(text=props.get("text", ""))
            elif widget_type == "ButtonComponent":
                comp = ButtonComponent(text=props.get("text", "Button"))
            elif widget_type == "ImageComponent":
                comp = ImageComponent()
            else:
                continue

            # Set properties
            comp.x = float(props.get("x", 0))
            comp.y = float(props.get("y", 0))
            comp.width = float(props.get("width", 100))
            comp.height = float(props.get("height", 100))
            comp.visible = bool(props.get("visible", True))

            go.add_component(comp)
            scene.game_objects.append(go)
            scene.editable_objects.append(go)
            widget_count += 1

        print(f"    Widgets created: {widget_count}")

        # Step 4: Render UI to surface
        print("\n[4] Rendering UI to surface...")
        screen = pygame.Surface((1280, 720))
        screen.fill((0, 0, 0))

        from engine.ui.ui_renderer import UIRenderer

        class MockRuntimeScene:
            def __init__(self):
                self.scene = scene

        runtime_scene = MockRuntimeScene()
        renderer = UIRenderer()
        renderer.render(runtime_scene, screen)

        # Step 5: Count non-black pixels
        print("\n[5] Analyzing rendered pixels...")
        import numpy as np
        arr = pygame.surfarray.array3d(screen)
        non_black = ((arr[:,:,0] > 0) | (arr[:,:,1] > 0) | (arr[:,:,2] > 0)).sum()
        print(f"    Non-black pixels: {int(non_black)}")

        if non_black > 0:
            print(f"\n[PASS] MainMenu UI renders visible pixels!")
            print(f"\nPipeline Summary:")
            print(f"  Load: PASS")
            print(f"  Compile: PASS ({len(compiled_widgets)} widgets)")
            print(f"  Create: PASS ({widget_count} widgets)")
            print(f"  Render: PASS ({int(non_black)} pixels)")
            print(f"\nExpected in Play Mode:")
            print(f"  - ZENNITY ARENA title (green text)")
            print(f"  - NEW GAME button (blue)")
            print(f"  - CONTINUE button (gray)")
            print(f"  - EXIT button (red)")
            print(f"  - Version label (gray text)")
            return True
        else:
            print(f"\n[FAIL] No pixels rendered")
            return False

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mainmenu_ui_pipeline()
    sys.exit(0 if success else 1)
