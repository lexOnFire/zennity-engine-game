from __future__ import annotations

from typing import Any


def _current_scene_object(editor: Any) -> Any | None:
    viewport = getattr(editor, "viewport", None)
    scene = getattr(viewport, "active_scene", None)
    if scene is None:
        return None
    selected_index = int(getattr(scene, "selected_index", -1))
    objects = list(getattr(scene, "editable_objects", []))
    if 0 <= selected_index < len(objects):
        return objects[selected_index]
    return None


def _current_runtime_object(editor: Any) -> Any | None:
    context = getattr(editor, "editor_context", None)
    selection = getattr(context, "selection", None)
    return getattr(selection, "selected", None)


def _sync_object_selection(editor: Any) -> None:
    viewport = getattr(editor, "viewport", None)
    scene = getattr(viewport, "active_scene", None)
    if viewport is None or scene is None:
        return

    obj = _current_runtime_object(editor) or _current_scene_object(editor)
    if obj is None:
        objects = list(getattr(scene, "editable_objects", []))
        obj = objects[0] if objects else None
    if obj is None:
        return

    try:
        editor.select_object(obj)
    except Exception:
        try:
            viewport.select_object(obj)
        except Exception:
            pass

    objects = list(getattr(scene, "editable_objects", []))
    if obj in objects and hasattr(scene, "selected_index"):
        scene.selected_index = objects.index(obj)

    try:
        viewport.update()
    except Exception:
        pass


def apply_tool_selection_stability_patch() -> bool:
    try:
        from editor.phase1_editor import ZennityPhase1Editor
        from editor.runtime.tool_manager import EditorTool
    except Exception:
        return False

    if getattr(ZennityPhase1Editor, "_zennity_tool_selection_patch_applied", False):
        return True

    original = ZennityPhase1Editor._on_runtime_tool_changed

    def on_runtime_tool_changed(self, tool: EditorTool) -> None:
        original(self, tool)
        if tool in (EditorTool.MOVE, EditorTool.ROTATE, EditorTool.SCALE):
            _sync_object_selection(self)

    ZennityPhase1Editor._on_runtime_tool_changed = on_runtime_tool_changed
    ZennityPhase1Editor._zennity_tool_selection_patch_applied = True
    return True
