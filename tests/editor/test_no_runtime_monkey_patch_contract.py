from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_phase1_editor_installs_extensions_without_runtime_method_replacement() -> None:
    source = (ROOT / "editor" / "phase1_editor.py").read_text(encoding="utf-8")

    assert "_install_editor_extensions" in source
    assert "_apply_runtime_patches" not in source
    assert "undo_redo_feedback_patch" not in source
    assert "tool_selection_stability_patch" not in source


def test_asset_inspector_registration_has_no_class_patch_for_tool_selection() -> None:
    source = (ROOT / "editor" / "inspector" / "asset_component_plugins.py").read_text(
        encoding="utf-8"
    )

    assert "apply_tool_selection_stability_patch" not in source
    assert "apply_editor2d_sprite_patch" not in source
    assert "apply_editor2d_sprite_no_border_patch" not in source
    assert "apply_phase1_sprite_overlay_patch" not in source
    assert "apply_viewport_transform_stability_patch" not in source


def test_transform_behaviour_is_composed_without_runtime_class_assignment() -> None:
    viewport = (ROOT / "editor" / "widgets" / "phase1_viewport.py").read_text(encoding="utf-8")
    support = (ROOT / "editor" / "widgets" / "transform_interaction.py").read_text(encoding="utf-8")

    assert "emit_transform_changed(self, obj)" in viewport
    assert "sync_camera_to_engine(self)" in viewport
    assert "Phase1ViewportWidget." not in support


def test_phase1_editor_does_not_assign_functions_to_instance_methods() -> None:
    tree = ast.parse((ROOT / "editor" / "phase1_editor.py").read_text(encoding="utf-8"))
    forbidden = {"undo", "redo", "_connect", "_on_runtime_tool_changed"}
    assigned = {
        node.targets[0].attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Attribute)
        and isinstance(node.value, (ast.Lambda, ast.FunctionDef))
    }

    assert assigned.isdisjoint(forbidden)


def test_runtime_patch_modules_are_removed() -> None:
    remaining = sorted(path.name for path in (ROOT / "editor" / "runtime").glob("*_patch.py"))

    assert remaining == []


def test_assets_panel_uses_explicit_controller_and_drag_drop_module() -> None:
    premium = (ROOT / "editor" / "premium_editor.py").read_text(encoding="utf-8")
    extensions = (ROOT / "editor" / "runtime" / "editor_extensions.py").read_text(
        encoding="utf-8"
    )

    assert "AssetsPanelController(self)" in premium
    assert "assets_panel_polish_patch" not in premium
    assert "editor.runtime.asset_drag_drop import install_asset_drag_drop" in extensions
    assert "asset_drag_drop_patch" not in extensions
