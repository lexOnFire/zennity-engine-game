from __future__ import annotations

import types
from types import SimpleNamespace

from editor.services.workspace_registry import WorkspaceRegistry, default_workspace_definitions


class _Widget:
    def __init__(self, parent=None) -> None:
        self.parent = parent
        self.shown = 0
        self.raised = 0
        self.activated = 0
        self.opened_tools: list[str] = []

    def show(self) -> None:
        self.shown += 1

    def raise_(self) -> None:
        self.raised += 1

    def activateWindow(self) -> None:
        self.activated += 1

    def open_graph_tool(self, tool_id: str) -> None:
        self.opened_tools.append(tool_id)


def test_workspace_registry_reuses_visual_graph_hub(monkeypatch) -> None:
    host = SimpleNamespace()

    def import_module(name: str):
        assert name == "editor.visual_scripting.visual_scripting_dock"
        return types.SimpleNamespace(VisualScriptingEditorDock=_Widget)

    monkeypatch.setattr("editor.services.workspace_registry.importlib.import_module", import_module)
    registry = WorkspaceRegistry(host)

    logic = registry.open("logic")
    behavior = registry.open("behavior_tree")

    assert logic is behavior
    assert logic.opened_tools == ["logic_graph", "behavior_tree"]
    assert logic.shown == 2


def test_workspace_registry_contains_phase1_workspace_targets() -> None:
    ids = {definition.workspace_id for definition in default_workspace_definitions()}

    assert {"logic", "behavior_tree", "dialogue", "material_graph", "ui_builder", "animation_studio"} <= ids


def test_workspace_registry_prefers_existing_animation_window() -> None:
    window = _Widget()
    host = SimpleNamespace(animation_window=window)
    registry = WorkspaceRegistry(host)

    assert registry.open("animation") is window
    assert window.shown == 1
