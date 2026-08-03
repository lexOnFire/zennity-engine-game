from pathlib import Path
from types import SimpleNamespace

from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock


class _Editor:
    def __init__(self) -> None:
        self.opened = []

    def load_document(self, path: Path) -> bool:
        self.opened.append(path)
        return True


def test_scene_workspace_preloads_every_visual_tab() -> None:
    root = Path.cwd()
    workspace = {
        "logic": "Assets/Demos/PortalStation/PortalTerminal.zlogic",
        "behavior_tree": "Assets/Demos/PortalStation/StationDrone.zbehavior",
        "dialogue": "Assets/Demos/PortalStation/StationGuide.zdialogue",
        "material": "Assets/Demos/PortalStation/PortalGlow.zmat",
        "animator": "Assets/Demos/PortalStation/PortalAnimator.zanimator",
        "ui": "Assets/Demos/PortalStation/PortalHUD.zui",
    }
    editors = [_Editor() for _index in range(6)]
    messages = []
    dock = SimpleNamespace(
        _host=SimpleNamespace(_scene_document={"visual_logic_workspace": workspace}),
        _scene_workspace_signature=(),
        graph_editor=editors[0],
        behavior_tree_editor=editors[1],
        dialogue_graph_editor=editors[2],
        material_graph_editor=editors[3],
        animator_graph_editor=editors[4],
        ui_builder=editors[5],
        runtime_logs_text=SimpleNamespace(append=messages.append),
    )

    VisualScriptingEditorDock._sync_scene_workspace(dock)
    VisualScriptingEditorDock._sync_scene_workspace(dock)

    assert all(len(editor.opened) == 1 for editor in editors)
    assert all(editor.opened[0].is_relative_to(root) for editor in editors)
    assert messages == ["[Workspace] 6 documento(s) da cena carregado(s)."]


def test_scene_workspace_accepts_owned_behavior_tree_entry() -> None:
    editor = _Editor()
    dock = SimpleNamespace(
        _host=SimpleNamespace(
            _scene_document={"visual_logic_workspace": {
                "behavior_tree": {
                    "path": "Assets/Demos/PortalStation/StationDrone.zbehavior",
                    "object": "StationDrone",
                }
            }},
            _objects_by_name={},
        ),
        _scene_workspace_signature=(),
        graph_editor=_Editor(), behavior_tree_editor=editor,
        dialogue_graph_editor=_Editor(), material_graph_editor=_Editor(),
        animator_graph_editor=_Editor(), ui_builder=_Editor(),
        runtime_logs_text=SimpleNamespace(append=lambda _message: None),
    )

    VisualScriptingEditorDock._sync_scene_workspace(dock)

    assert editor.opened[0].name == "StationDrone.zbehavior"
