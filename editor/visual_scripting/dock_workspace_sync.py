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


def _collect_behavior_tree_paths(host: Any) -> list[Path]:
    """Return unique .zbehavior paths linked to any object in the active scene."""
    objects = getattr(host, "_objects_by_name", {})
    seen: set[str] = set()
    result: list[Path] = []
    cwd = Path(getattr(getattr(host, "_scene_persistence", None), "project_root", Path.cwd()))
    for obj in objects.values():
        behavior = obj.get("behavior") if isinstance(obj.get("behavior"), dict) else None
        if not behavior:
            continue
        raw = str(behavior.get("controller_path", "")).strip()
        if not raw or raw in seen:
            continue
        seen.add(raw)
        path = Path(raw)
        path = path if path.is_absolute() else cwd / path
        if path.is_file():
            result.append(path)
    return result


def sync_scene_workspace(dock: VisualScriptingEditorDock) -> None:
    """Preload all visual documents declared by the active scene."""
    document = getattr(dock._host, "_scene_document", None)
    workspace = (
        document.get("visual_logic_workspace", {})
        if isinstance(document, dict) else {}
    )
    if not isinstance(workspace, dict):
        workspace = {}

    # ── build a signature that also tracks linked behavior trees ──────────────
    bt_paths = _collect_behavior_tree_paths(dock._host)
    bt_sig = tuple(str(p) for p in sorted(bt_paths))
    workspace_sig = tuple(
        sorted((str(key), str(value)) for key, value in workspace.items())
    )
    signature = workspace_sig + bt_sig
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

    # 1. Open files declared in visual_logic_workspace (scene-level)
    for key, editor in editors.items():
        asset_value = workspace.get(key)
        if not asset_value:
            continue
        raw_path = asset_value.get("path", "") if isinstance(asset_value, dict) else asset_value
        path = Path(str(raw_path))
        root = Path(getattr(getattr(dock._host, "_scene_persistence", None), "project_root", Path.cwd()))
        path = path if path.is_absolute() else root / path
        callback = (
            getattr(editor, "open_asset", None)
            or getattr(editor, "load_document", None)
        )
        if callback is not None and path.is_file() and callback(path):
            opened += 1

    # 2. Auto-load the first behavior tree linked to any scene object
    #    (opens in the Behavior Tree tab so the editor is hydrated)
    if bt_paths:
        bt_editor = dock.behavior_tree_editor
        callback = (
            getattr(bt_editor, "open_asset", None)
            or getattr(bt_editor, "load_document", None)
        )
        # Only open if the workspace didn't already handle a behavior_tree key
        if callback is not None and "behavior_tree" not in workspace:
            if callback(bt_paths[0]):
                opened += 1

    if opened:
        dock.runtime_logs_text.append(
            f"[Workspace] {opened} documento(s) da cena carregado(s)."
        )
