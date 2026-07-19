from __future__ import annotations

from typing import Any


def _scene_selected_object(editor: Any) -> Any | None:
    viewport = getattr(editor, "viewport", None)
    scene = getattr(viewport, "active_scene", None)
    if scene is None:
        return None
    objects = list(getattr(scene, "editable_objects", []))
    selected_index = int(getattr(scene, "selected_index", -1))
    return objects[selected_index] if 0 <= selected_index < len(objects) else None


def sync_tool_selection(editor: Any) -> None:
    """Keep transform tools attached to the canonical editor selection."""
    viewport = getattr(editor, "viewport", None)
    scene = getattr(viewport, "active_scene", None)
    if viewport is None or scene is None:
        return

    selection = getattr(getattr(editor, "editor_context", None), "selection", None)
    selected = getattr(selection, "selected", None)
    obj = selected or _scene_selected_object(editor)
    if obj is None:
        objects = list(getattr(scene, "editable_objects", []))
        obj = objects[0] if objects else None
    if obj is None:
        return

    editor.select_object(obj)
    objects = list(getattr(scene, "editable_objects", []))
    if obj in objects and hasattr(scene, "selected_index"):
        scene.selected_index = objects.index(obj)
    viewport.update()
