#!/usr/bin/env python3
"""Automated tests for BUG-8A-005 Canonical UI representation."""

import json
from pathlib import Path
import pytest


def test_mainmenu_has_canonical_ui_component():
    """Verify that MainMenu.zscene has a canonical Canvas component with layout_path."""
    scene_file = Path("Assets/Scenes/MainMenu.zscene")
    assert scene_file.exists()

    data = json.loads(scene_file.read_text(encoding="utf-8"))
    objects = data.get("objects", [])

    menu_ui_obj = next((obj for obj in objects if obj.get("name") == "MenuUI"), None)
    assert menu_ui_obj is not None, "MenuUI object not found in MainMenu.zscene"

    components = menu_ui_obj.get("components", {})
    # Check both dict and list representation
    has_canvas = "canvas" in components or any(
        isinstance(item, dict) and item.get("type") in {"Canvas", "UICanvas"}
        for item in components.get("items", [])
    )
    assert has_canvas, "MenuUI does not have a canonical Canvas component"


def test_mainmenu_ui_asset_assigned_to_canvas():
    """Verify that MainMenu.zui asset is assigned to the Canvas component."""
    scene_file = Path("Assets/Scenes/MainMenu.zscene")
    data = json.loads(scene_file.read_text(encoding="utf-8"))
    objects = data.get("objects", [])

    menu_ui_obj = next((obj for obj in objects if obj.get("name") == "MenuUI"), None)
    assert menu_ui_obj is not None

    components = menu_ui_obj.get("components", {})
    canvas_comp = components.get("canvas")
    if not canvas_comp and "items" in components:
        for item in components["items"]:
            if isinstance(item, dict) and item.get("type") in {"Canvas", "UICanvas"}:
                canvas_comp = item.get("properties", {})
                break

    assert isinstance(canvas_comp, dict), "Canvas component data invalid"
    asset_path = canvas_comp.get("layout_path") or canvas_comp.get("ui_asset")
    assert asset_path == "Assets/UI/MainMenu.zui", f"Expected Assets/UI/MainMenu.zui, got {asset_path}"


def test_mainmenu_scene_runtime_compiles_ui():
    """Verify NativeUIRenderer compiles UI elements from MainMenu.zscene."""
    from editor.runtime.native_ui import NativeUIRenderer

    scene_file = Path("Assets/Scenes/MainMenu.zscene")
    data = json.loads(scene_file.read_text(encoding="utf-8"))
    objects = data.get("objects", [])

    renderer = NativeUIRenderer()
    widgets = renderer.components(objects)

    assert len(widgets) > 0, "NativeUIRenderer failed to extract UI widgets from MainMenu.zscene"
    widget_names = [w[1].get("name") for w in widgets if isinstance(w[1], dict)]
    assert "Title" in widget_names or "NewGameButton" in widget_names or "Background" in widget_names
