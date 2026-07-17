from __future__ import annotations

from editor.workspace import (
    ANIMATION_LAYOUT,
    COMPACT_LAYOUT,
    DEFAULT_LAYOUT,
    WorkspaceLayout,
    WorkspaceManager,
    animation_workspace_layout,
    compact_workspace_layout,
    default_workspace_layout,
)


def test_workspace_layout_roundtrip() -> None:
    layout = WorkspaceLayout(name="Custom")
    layout.set_panel_visible("Console", False)
    layout.set_splitter_sizes("main", [1, 2, 3])
    layout.set_active_tab("viewport", "Game")

    restored = WorkspaceLayout.from_dict(layout.to_dict())

    assert restored.name == "Custom"
    assert restored.is_panel_visible("Console") is False
    assert restored.splitter_sizes["main"] == [1, 2, 3]
    assert restored.active_tabs["viewport"] == "Game"


def test_default_workspace_contains_core_panels() -> None:
    layout = default_workspace_layout()

    assert layout.name == DEFAULT_LAYOUT
    assert layout.is_panel_visible("Hierarchy")
    assert layout.is_panel_visible("Inspector")
    assert layout.is_panel_visible("Console")
    assert layout.splitter_sizes["main"] == [260, 850, 300]


def test_compact_workspace_hides_secondary_panels() -> None:
    layout = compact_workspace_layout()

    assert layout.name == COMPACT_LAYOUT
    assert layout.is_panel_visible("Profiler") is False
    assert layout.is_panel_visible("Preview") is False


def test_animation_workspace_keeps_preview_visible() -> None:
    layout = animation_workspace_layout()

    assert layout.name == ANIMATION_LAYOUT
    assert layout.is_panel_visible("Preview") is True
    assert layout.active_tabs["viewport"] == "Scene"


def test_workspace_manager_applies_and_resets() -> None:
    manager = WorkspaceManager()

    assert DEFAULT_LAYOUT in manager.available_layouts()
    assert COMPACT_LAYOUT in manager.available_layouts()

    compact = manager.apply(COMPACT_LAYOUT)
    assert compact.name == COMPACT_LAYOUT

    reset = manager.reset()
    assert reset.name == DEFAULT_LAYOUT


def test_workspace_manager_falls_back_to_default() -> None:
    manager = WorkspaceManager()

    layout = manager.apply("Missing")

    assert layout.name == DEFAULT_LAYOUT
