#!/usr/bin/env python3
"""Test UI loading with correct schema format."""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from engine.ui.asset_loader import UIAssetLoader
from engine.ui.runtime_compiler import UIRuntimeCompiler


# Schema 1: What MainMenu.zui currently has (BROKEN)
BROKEN_SCHEMA = {
    "format": "zennity.ui",
    "widgets": [
        {
            "type": "Label",
            "name": "Title",
            "text": "ZENNITY ARENA",
            "x": 640,
            "y": 100,
            "width": 400,
            "height": 50,
            "font_size": 48,
            "text_color": "#00FF00",
            "visible": True
        },
        {
            "type": "Button",
            "name": "NewGameButton",
            "text": "NEW GAME",
            "x": 560,
            "y": 300,
            "width": 160,
            "height": 50,
            "color": "#0088FF",
            "visible": True
        }
    ]
}

# Schema 2: What compiler expects (WORKING)
CORRECT_SCHEMA = {
    "format_version": 2,
    "canvas": {
        "type": "canvas",
        "children": [
            {
                "type": "Label",
                "name": "Title",
                "text": "ZENNITY ARENA",
                "x": 640,
                "y": 100,
                "width": 400,
                "height": 50,
                "font_size": 48,
                "text_color": "#00FF00",
                "visible": True
            },
            {
                "type": "Button",
                "name": "NewGameButton",
                "text": "NEW GAME",
                "x": 560,
                "y": 300,
                "width": 160,
                "height": 50,
                "color": "#0088FF",
                "visible": True
            }
        ]
    }
}


def test_schema(name, schema):
    print("\n" + "="*60)
    print(f"Testing: {name}")
    print("="*60)

    compiler = UIRuntimeCompiler()

    try:
        # Compile
        compiled = compiler.compile(schema)

        print(f"[PASS] Compiled successfully")
        print(f"       Widget count: {len(compiled)}")

        for i, widget in enumerate(compiled):
            print(f"       [{i}] {widget.get('type')}: {widget.get('widget_name')}")

        return len(compiled) > 0

    except Exception as e:
        print(f"[FAIL] Compilation failed")
        print(f"       {type(e).__name__}: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("UI SCHEMA COMPATIBILITY TEST")
    print("="*60)

    # Test both schemas
    broken_works = test_schema("BROKEN_SCHEMA (widgets array)", BROKEN_SCHEMA)
    correct_works = test_schema("CORRECT_SCHEMA (canvas.children)", CORRECT_SCHEMA)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print(f"BROKEN_SCHEMA works:  {broken_works}")
    print(f"CORRECT_SCHEMA works: {correct_works}")

    if not broken_works and correct_works:
        print("\n[CONCLUSION]")
        print("MainMenu.zui uses wrong schema.")
        print("Compiler expects:")
        print('  {')
        print('    "canvas": {')
        print('      "children": [...]')
        print('    }')
        print('  }')
        print("\nBut MainMenu.zui has:")
        print('  {')
        print('    "format": "...",')
        print('    "widgets": [...]')
        print('  }')
        print("\n[REQUIRED FIX]")
        print("Either:")
        print("  1. Fix MainMenu.zui to use canvas.children structure")
        print("  2. OR update UIRuntimeCompiler to handle widgets array")


if __name__ == "__main__":
    main()
