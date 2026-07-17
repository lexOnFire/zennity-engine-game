from __future__ import annotations

from typing import Any


def _has_image_sprite(obj: Any) -> bool:
    if obj is None:
        return False
    for component in getattr(obj, "components", []):
        if getattr(component, "type_name", type(component).__name__) == "Image":
            if str(getattr(component, "sprite_path", "") or "").strip():
                return True
    return False


def apply_sprite_selection_overlay_patch() -> bool:
    try:
        from editor.viewport.viewport_renderer import ViewportRenderer
    except Exception:
        return False

    if getattr(ViewportRenderer, "_zennity_sprite_selection_patch_applied", False):
        return True

    original = ViewportRenderer.render_qt_overlays

    def render_without_sprite_box(self, *args, **kwargs):
        selected = kwargs.get("selected")
        active_tool_name = str(kwargs.get("active_tool_name", "")).lower()
        if selected is None and len(args) >= 3:
            selected = args[2]
        if active_tool_name == "" and len(args) >= 4:
            active_tool_name = str(args[3]).lower()
        if _has_image_sprite(selected) and active_tool_name != "scale":
            kwargs["selection_visible"] = False
        return original(self, *args, **kwargs)

    ViewportRenderer.render_qt_overlays = render_without_sprite_box
    ViewportRenderer._zennity_sprite_selection_patch_applied = True
    return True
