from editor.workspace.workspace_manager import (
    WorkspaceManager as QtWorkspaceManager,
    WorkspacePreset,
    WindowRegistry,
    PanelRegistry,
)
from editor.workspace.layout_model import (
    ANIMATION_LAYOUT,
    COMPACT_LAYOUT,
    DEFAULT_LAYOUT,
    WorkspaceLayout,
    WorkspaceLayoutManager,
    animation_workspace_layout,
    compact_workspace_layout,
    default_workspace_layout,
)

# API histórica sem Qt. O manager visual permanece disponível explicitamente.
WorkspaceManager = WorkspaceLayoutManager

__all__ = [
    "WorkspaceManager",
    "QtWorkspaceManager",
    "WorkspacePreset",
    "WindowRegistry",
    "PanelRegistry",
    "ANIMATION_LAYOUT",
    "COMPACT_LAYOUT",
    "DEFAULT_LAYOUT",
    "WorkspaceLayout",
    "animation_workspace_layout",
    "compact_workspace_layout",
    "default_workspace_layout",
]
