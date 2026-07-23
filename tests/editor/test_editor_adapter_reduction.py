"""The composition root must address controllers without shell pass-throughs."""

from __future__ import annotations

import ast
from pathlib import Path


REMOVED = {
    "_configure_logic_workspace",
    "_configure_main_menus",
    "_refresh_assets",
    "_open_logic_asset_item",
    "_refresh_prefabs",
    "_instantiate_prefab_item",
    "_open_prefab_menu",
    "_connect_existing_toolbar_actions",
    "_configure_tool_actions",
}


def test_bootstrap_uses_focused_controllers_directly() -> None:
    source = Path("editor/editor_bootstrap_controller.py").read_text(encoding="utf-8")
    for call in (
        "h._editor_commands.connect_toolbar_actions()",
        "h._editor_commands.configure_main_menus()",
        "h._editor_commands.configure_tools()",
        "h._asset_browser.refresh()",
        "h._prefab_workspace.refresh()",
        "h._logic_workspace_controller.connect()",
    ):
        assert call in source


def test_trivial_bootstrap_adapters_do_not_return() -> None:
    tree = ast.parse(Path("editor/editor_integration_adapters.py").read_text(encoding="utf-8"))
    assert not any(isinstance(node, ast.ClassDef) for node in tree.body)
