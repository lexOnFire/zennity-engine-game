"""The official editor must not regain a shell pass-through layer."""

from __future__ import annotations

import ast
from pathlib import Path


def test_official_window_has_no_integration_adapter_mixin() -> None:
    source = Path("editor/isolated_editor_main.py").read_text(encoding="utf-8")
    assert "EditorIntegrationAdapters" not in source


def test_migration_marker_defines_no_runtime_classes_or_functions() -> None:
    tree = ast.parse(Path("editor/editor_integration_adapters.py").read_text(encoding="utf-8"))
    assert not any(isinstance(node, (ast.ClassDef, ast.FunctionDef)) for node in tree.body)


def test_hierarchy_addresses_prefab_controller_directly() -> None:
    source = Path("editor/hierarchy_controller.py").read_text(encoding="utf-8")
    assert "self.host._prefab_workspace.save_selected()" in source
    assert "_save_selected_as_prefab" not in source
