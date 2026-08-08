#!/usr/bin/env python3
"""Debug UI rendering pipeline stage by stage."""

import sys
import json
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def stage_1_load_asset():
    """Stage 1: Load .zui asset file."""
    print("\n" + "="*60)
    print("STAGE 1: LOAD ZUI ASSET")
    print("="*60)

    from engine.ui.asset_loader import UIAssetLoader, UIAssetLoaderError

    try:
        loader = UIAssetLoader(project_root=project_root)
        ui_document = loader.load("Assets/UI/MainMenu.zui")

        print(f"[PASS] UIAssetLoader.load() returned: {type(ui_document)}")
        print(f"       Document type: {type(ui_document).__name__}")

        if hasattr(ui_document, 'widgets'):
            print(f"       Widget count: {len(ui_document.widgets)}")
            for widget in ui_document.widgets[:3]:
                print(f"         - {widget}")

        return ui_document

    except UIAssetLoaderError as e:
        print(f"[FAIL] UIAssetLoader.load() FAILED: {e}")
        return None
    except Exception as e:
        print(f"[FAIL] UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def stage_2_compile_widgets(ui_document):
    """Stage 2: Compile UI document to runtime widgets."""
    print("\n" + "="*60)
    print("STAGE 2: COMPILE WIDGETS")
    print("="*60)

    if ui_document is None:
        print("[SKIP] No UI document to compile (stage 1 failed)")
        return None

    try:
        from engine.ui.runtime_compiler import UIRuntimeCompiler, UICompilerError

        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(ui_document)

        print(f"[PASS] UIRuntimeCompiler.compile() returned: {type(compiled_widgets)}")
        print(f"       Compiled widget count: {len(compiled_widgets)}")

        for i, widget in enumerate(compiled_widgets[:3]):
            print(f"       [{i}] {type(widget).__name__}")
            if hasattr(widget, 'name'):
                print(f"           name: {widget.name}")

        return compiled_widgets

    except Exception as e:
        print(f"[FAIL] COMPILATION FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def stage_3_check_canvas():
    """Stage 3: Check if Canvas component exists in MenuUI."""
    print("\n" + "="*60)
    print("STAGE 3: CANVAS COMPONENT IN MAINMENU")
    print("="*60)

    try:
        mainmenu_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(mainmenu_path.read_text(encoding="utf-8"))

        menu_ui = next((o for o in data["objects"] if o.get("name") == "MenuUI"), None)

        if menu_ui is None:
            print("[FAIL] MenuUI object not found in scene")
            return None

        print(f"[PASS] MenuUI object found")
        print(f"       id: {menu_ui.get('id')}")
        print(f"       active: {menu_ui.get('active')}")
        print(f"       enabled: {menu_ui.get('enabled')}")

        components = menu_ui.get("components", {})
        print(f"       component types: {list(components.keys())}")

        if "canvas" in components:
            canvas = components["canvas"]
            print(f"[PASS] Canvas component found")
            print(f"       ui_asset: {canvas.get('ui_asset')}")
        else:
            print(f"[FAIL] Canvas component NOT FOUND")

        return menu_ui

    except Exception as e:
        print(f"[FAIL] Canvas check failed: {type(e).__name__}: {e}")
        return None


def stage_4_validate_zui():
    """Stage 4: Validate MainMenu.zui schema."""
    print("\n" + "="*60)
    print("STAGE 4: ZUI SCHEMA VALIDATION")
    print("="*60)

    try:
        mainmenu_zui = project_root / "Assets" / "UI" / "MainMenu.zui"

        if not mainmenu_zui.exists():
            print(f"[FAIL] MainMenu.zui not found")
            return None

        data = json.loads(mainmenu_zui.read_text(encoding="utf-8"))

        print(f"[PASS] MainMenu.zui loaded")
        print(f"       Top-level keys: {list(data.keys())}")
        print(f"       format_version: {data.get('format_version')}")

        widgets = data.get("widgets", [])
        print(f"       widget count: {len(widgets)}")

        for i, widget in enumerate(widgets[:3]):
            print(f"       [{i}] type={widget.get('type')}, name={widget.get('name')}")

        if len(widgets) == 0:
            print(f"[WARN] No widgets in MainMenu.zui!")

        return data

    except Exception as e:
        print(f"[FAIL] ZUI validation failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("\n" + "="*60)
    print("UI RENDERING PIPELINE DEBUG")
    print("="*60)
    print(f"Project: {project_root}")

    # Run stages
    ui_document = stage_1_load_asset()
    compiled_widgets = stage_2_compile_widgets(ui_document)
    menu_ui_object = stage_3_check_canvas()
    zui_schema = stage_4_validate_zui()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    results = {
        "LOAD_ASSET": "PASS" if ui_document is not None else "FAIL",
        "COMPILE_WIDGETS": "PASS" if compiled_widgets is not None and len(compiled_widgets) > 0 else "FAIL",
        "CANVAS_FOUND": "PASS" if menu_ui_object is not None and "canvas" in menu_ui_object.get("components", {}) else "FAIL",
        "ZUI_VALID": "PASS" if zui_schema is not None else "FAIL",
    }

    for stage, result in results.items():
        print(f"  {stage:20} {result}")

    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    if ui_document is None:
        print("  MainMenu.zui cannot load. Asset path or schema issue.")
    elif compiled_widgets is None or len(compiled_widgets) == 0:
        print("  Widgets compile to 0 items. Compiler or schema issue.")
    else:
        print("  Widgets load and compile OK.")
        print("  Next: Check UICanvas attachment and renderer integration.")
        print("  Problem likely in: Runtime attachment or render calls.")


if __name__ == "__main__":
    main()
