from __future__ import annotations

import math
from typing import Any


def _rotated_scale_handle_positions(viewport: Any, obj: Any) -> list[tuple[float, float]]:
    if obj is None or not hasattr(obj, "transform"):
        return []
    pos = getattr(obj.transform, "position", None)
    scale = getattr(obj.transform, "scale", None)
    if pos is None or scale is None:
        return []
    cx, cy = viewport.world_to_viewport(pos)
    zoom = float(getattr(getattr(viewport, "camera", None), "zoom", 1.0))
    w = abs(float(scale[0])) * zoom
    h = abs(float(scale[1])) * zoom
    rz = math.radians(float(getattr(obj.transform, "rz", 0.0)))
    cos_r = math.cos(rz)
    sin_r = math.sin(rz)
    local = [
        (-w / 2, -h / 2),
        (0, -h / 2),
        (w / 2, -h / 2),
        (w / 2, 0),
        (w / 2, h / 2),
        (0, h / 2),
        (-w / 2, h / 2),
        (-w / 2, 0),
    ]
    return [(cx + lx * cos_r - ly * sin_r, cy + lx * sin_r + ly * cos_r) for lx, ly in local]


def apply_rotated_scale_gizmo_patch() -> bool:
    try:
        from editor.widgets.phase1_viewport import Phase1ViewportWidget
        from editor.runtime.tool_manager import EditorTool
    except Exception:
        return False
    if getattr(Phase1ViewportWidget, "_zennity_rotated_scale_gizmo_patch", False):
        return True

    def scale_handle_positions(self, obj: Any) -> list[tuple[float, float]]:
        return _rotated_scale_handle_positions(self, obj)

    def scale_handle_at_viewport_point(self, x: float, y: float, selected: Any) -> int | None:
        if self._active_tool() != EditorTool.SCALE:
            return None
        if not self._should_draw_gizmo(selected):
            return None
        handles = _rotated_scale_handle_positions(self, selected)
        for index, (hx, hy) in enumerate(handles):
            if math.hypot(float(x) - hx, float(y) - hy) <= 10.0:
                return index
        return None

    Phase1ViewportWidget._scale_handle_positions = scale_handle_positions
    Phase1ViewportWidget._scale_handle_at_viewport_point = scale_handle_at_viewport_point
    Phase1ViewportWidget._zennity_rotated_scale_gizmo_patch = True
    return True
