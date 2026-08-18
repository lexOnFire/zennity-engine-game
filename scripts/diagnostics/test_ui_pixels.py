#!/usr/bin/env python3
"""Test UI pixel rendering - verify non-black pixels appear."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pygame


def count_non_black_pixels(surface: pygame.Surface) -> int:
    """Count pixels that are not pure black (0, 0, 0)."""
    array = pygame.surfarray.array3d(surface)
    # Count pixels where at least one channel is > 0
    non_black = ((array[:,:,0] > 0) | (array[:,:,1] > 0) | (array[:,:,2] > 0)).sum()
    return int(non_black)


def test_ui_renderer_golden():
    """Test that UIRenderer can render widgets without errors."""
    print("\n" + "="*60)
    print("TEST: UIRenderer Golden Path")
    print("="*60)

    try:
        from engine.ui.ui_renderer import UIRenderer
        from engine.ui.runtime_components import LabelComponent, ButtonComponent
        from engine.game_object import GameObject

        # Create test surface
        screen = pygame.Surface((1280, 720))
        screen.fill((0, 0, 0))  # Black background

        # Create mock scene with UI components
        class MockScene:
            def __init__(self):
                self.game_objects = []

        scene = MockScene()

        # Create Canvas component (required for UI to render)
        from engine.ui.runtime_components import Canvas
        canvas = Canvas()

        # Create a label
        label = LabelComponent(text="HELLO ZENNITY", x=100, y=100)

        # Create GameObjects
        canvas_go = GameObject("Canvas")
        canvas_go.add_component(canvas)
        scene.game_objects.append(canvas_go)

        label_go = GameObject("Label")
        label_go.add_component(label)
        scene.game_objects.append(label_go)

        # Create mock runtime scene
        class MockRuntimeScene:
            def __init__(self):
                self.scene = scene

        runtime_scene = MockRuntimeScene()

        # Render UI
        print(f"[1] Rendering UI...")
        renderer = UIRenderer()
        renderer.render(runtime_scene, screen)

        # Count non-black pixels
        non_black = count_non_black_pixels(screen)
        print(f"[2] Non-black pixels: {non_black}")

        if non_black > 0:
            print(f"[PASS] UI rendered {non_black} non-black pixels")
            return True
        else:
            print(f"[FAIL] No pixels rendered (still black screen)")
            return False

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_button_rendering():
    """Test that buttons render."""
    print("\n" + "="*60)
    print("TEST: UIRenderer Button Rendering")
    print("="*60)

    try:
        from engine.ui.ui_renderer import UIRenderer
        from engine.ui.runtime_components import Canvas, ButtonComponent
        from engine.game_object import GameObject

        # Create test surface
        screen = pygame.Surface((1280, 720))
        screen.fill((0, 0, 0))

        # Create scene with button
        class MockScene:
            def __init__(self):
                self.game_objects = []

        scene = MockScene()

        # Add canvas
        canvas = Canvas()
        canvas_go = GameObject("Canvas")
        canvas_go.add_component(canvas)
        scene.game_objects.append(canvas_go)

        # Add button
        button = ButtonComponent(text="NEW GAME", x=500, y=300, width=250, height=60)
        button_go = GameObject("NewGameButton")
        button_go.add_component(button)
        scene.game_objects.append(button_go)

        # Render
        class MockRuntimeScene:
            def __init__(self):
                self.scene = scene

        runtime_scene = MockRuntimeScene()
        renderer = UIRenderer()
        renderer.render(runtime_scene, screen)

        # Check pixels
        non_black = count_non_black_pixels(screen)
        print(f"[1] Non-black pixels: {non_black}")

        if non_black > 0:
            print(f"[PASS] Button rendered")
            return True
        else:
            print(f"[FAIL] No button pixels")
            return False

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    pygame.init()

    result1 = test_ui_renderer_golden()
    result2 = test_ui_button_rendering()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Golden path: {'PASS' if result1 else 'FAIL'}")
    print(f"Button rendering: {'PASS' if result2 else 'FAIL'}")

    all_pass = result1 and result2
    sys.exit(0 if all_pass else 1)
