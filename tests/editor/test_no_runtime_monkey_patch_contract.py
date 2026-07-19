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
