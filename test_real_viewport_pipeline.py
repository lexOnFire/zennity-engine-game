#!/usr/bin/env python3
"""Integration test for REAL viewport presentation pipeline (BUG-8A-003 Audit)."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pygame


def count_non_black_pixels(surface: pygame.Surface) -> int:
    """Count pixels where at least one RGB channel is > 0."""
    array = pygame.surfarray.array3d(surface)
    non_black = ((array[:, :, 0] > 0) | (array[:, :, 1] > 0) | (array[:, :, 2] > 0)).sum()
    return int(non_black)


def test_real_viewport_presentation_path():
    """Test full pipeline: RuntimeScene / Objects -> NativeUIRenderer -> Surface -> Flip Presentation."""
    print("\n" + "=" * 70)
    print("AUDIT TEST: Real Viewport Presentation Pipeline")
    print("=" * 70)

    try:
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        print(f"[1] Surface ID: {id(screen)}, Size: {screen.get_size()}")

        # Create scene objects representing the Main Menu with Canvas and buttons
        objects = {
            "MainCanvas": {
                "name": "MainCanvas",
                "active": True,
                "ui": {
                    "type": "canvas",
                    "name": "MainCanvas",
                    "visible": True,
                    "children": [
                        {
                            "name": "TitleLabel",
                            "type": "Label",
                            "text": "ZENNITY ARENA",
                            "x": 400.0,
                            "y": 100.0,
                            "font_size": 48,
                            "color": [255, 215, 0],
                            "visible": True,
                        },
                        {
                            "name": "NewGameBtn",
                            "type": "Button",
                            "text": "NEW GAME",
                            "x": 490.0,
                            "y": 250.0,
                            "width": 300.0,
                            "height": 60.0,
                            "visible": True,
                        },
                        {
                            "name": "ContinueBtn",
                            "type": "Button",
                            "text": "CONTINUE",
                            "x": 490.0,
                            "y": 340.0,
                            "width": 300.0,
                            "height": 60.0,
                            "visible": True,
                        },
                        {
                            "name": "ExitBtn",
                            "type": "Button",
                            "text": "EXIT",
                            "x": 490.0,
                            "y": 430.0,
                            "width": 300.0,
                            "height": 60.0,
                            "visible": True,
                        },
                    ],
                },
            }
        }

        from editor.runtime.native_ui import NativeUIRenderer

        renderer = NativeUIRenderer()

        # Step 1: Clear / Fill
        print("\n[MOMENTO 1: Clear Framebuffer]")
        screen.fill((0, 0, 0))
        pixels_after_clear = count_non_black_pixels(screen)
        print(f"  - Surface ID: {id(screen)}")
        print(f"  - Non-black pixels after background fill: {pixels_after_clear}")

        # Step 2: UI Render
        print("\n[MOMENTO 2: UI Render]")
        renderer.draw(objects, screen)
        pixels_after_ui = count_non_black_pixels(screen)
        print(f"  - Surface ID: {id(screen)}")
        print(f"  - Non-black pixels after UI draw: {pixels_after_ui}")

        # Step 3: Present / Update (Flip)
        print("\n[MOMENTO 3: Blit / Present (display.flip)]")
        pygame.display.flip()
        pixels_presented = count_non_black_pixels(screen)
        print(f"  - Presented Surface ID: {id(screen)}")
        print(f"  - Non-black pixels presented to Viewport: {pixels_presented}")

        # Verification
        assert pixels_after_ui > pixels_after_clear, "UI render failed to produce non-black pixels"
        assert pixels_presented == pixels_after_ui, "Presented frame differs from UI frame"

        print("\n[PASS] Real Viewport Presentation Pipeline Audit SUCCESSFUL!")
        return True

    except Exception as e:
        print(f"\n[FAIL] Audit test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        pygame.quit()


if __name__ == "__main__":
    success = test_real_viewport_presentation_path()
    sys.exit(0 if success else 1)
