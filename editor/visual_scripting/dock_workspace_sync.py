"""Workspace sync helpers for VisualScriptingEditorDock."""
from __future__ import annotations
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock


class GraphToolAdapter:
    """Expose one hub tab through the bridge/tool contracts."""

    def __init__(self, hub: VisualScriptingEditorDock, tool_id: str, graph_editor: Any) -> None:
        self.hub = hub
        self.tool_id = tool_id
        self.graph_editor = graph_editor

    def show(self) -> None:
        self.hub.open_graph_tool(self.tool_id)

    def raise_(self) -> None:
        self.hub.raise_()

    def activateWindow(self) -> None:
        self.hub.activateWindow()


def sync_scene_workspace(dock: VisualScriptingEditorDock) -> None:
    """Preload all visual documents declared by the active scene."""
    document = getattr(dock._host, "_scene_document", None)
    workspace = (
        document.get("visual_logic_workspace", {})
        if isinstance(document, dict) else {}
    )
    if not isinstance(workspace, dict):
        return
    signature = tuple(
        sorted((str(key), str(value)) for key, value in workspace.items())
    )
    if not signature or signature == dock._scene_workspace_signature:
        return
    # Set before opening: LogicGraphEditor emits asset_changed synchronously.
    dock._scene_workspace_signature = signature
    editors = {
        "logic": dock.graph_editor,
        "behavior_tree": dock.behavior_tree_editor,
        "dialogue": dock.dialogue_graph_editor,
        "material": dock.material_graph_editor,
        "animator": dock.animator_graph_editor,
        "ui": dock.ui_builder,
    }
    opened = 0
    for key, editor in editors.items():
        asset_value = workspace.get(key)
        if not asset_value:
            continue
        path = Path(str(asset_value))
        path = path if path.is_absolute() else Path.cwd() / path
        callback = (
            getattr(editor, "open_asset", None)
            or getattr(editor, "load_document", None)
        )
        if callback is not None and path.is_file() and callback(path):
            opened += 1
    if opened:
        dock.runtime_logs_text.append(
            f"[Workspace] {opened} documento(s) da cena carregado(s)."
        )
