from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPen, QPixmap


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_EDITOR_BOX = QColor(80, 160, 255, 90)


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    cwd = Path.cwd()
    roots.append(cwd)
    roots.extend(cwd.parents)
    here = Path(__file__).resolve()
    roots.append(here.parents[2])
    return list(dict.fromkeys(roots))


def _resolve_sprite_path(path_value: str) -> Path | None:
    if not path_value:
        return None
    raw = Path(str(path_value).strip().replace("\\", "/"))
    if raw.is_absolute():
        return raw if raw.exists() else None
    for root in _candidate_roots():
        candidate = root / raw
        if candidate.exists() and candidate.is_file():
            return candidate
    name = raw.name.lower()
    for root in _candidate_roots():
        for base in (root / "Assets", root / "examples"):
            if not base.exists():
                continue
            for candidate in base.rglob("*"):
                if candidate.is_file() and candidate.name.lower() == name and candidate.suffix.lower() in _IMAGE_EXTENSIONS:
                    return candidate
    return None


def _image_component(obj: Any) -> Any | None:
    for component in getattr(obj, "components", []):
        if getattr(component, "type_name", type(component).__name__) == "Image":
            if str(getattr(component, "sprite_path", "") or "").strip():
                return component
    return None


def _patch_sprite_selection_overlay() -> None:
    try:
        from editor.viewport.viewport_renderer import ViewportRenderer
    except Exception:
        return
    if getattr(ViewportRenderer, "_zennity_sprite_selection_patch_applied", False):
        return
    original = ViewportRenderer.render_qt_overlays

    def render_qt_overlays(self, *args, **kwargs):
        selected = kwargs.get("selected")
        active_tool_name = str(kwargs.get("active_tool_name", "")).lower()
        if selected is None and len(args) >= 3:
            selected = args[2]
        if active_tool_name == "" and len(args) >= 4:
            active_tool_name = str(args[3]).lower()
        if _image_component(selected) is not None and active_tool_name != "scale":
            kwargs["selection_visible"] = False
        return original(self, *args, **kwargs)

    ViewportRenderer.render_qt_overlays = render_qt_overlays
    ViewportRenderer._zennity_sprite_selection_patch_applied = True


def apply_phase1_sprite_overlay_patch() -> bool:
    try:
        from editor.widgets.phase1_viewport import Phase1ViewportWidget
    except Exception:
        return False

    _patch_sprite_selection_overlay()

    if getattr(Phase1ViewportWidget, "_zennity_sprite_overlay_patch_applied", False):
        return True

    original_paint_gl = Phase1ViewportWidget.paintGL

    def patched_paint_gl(self) -> None:
        original_paint_gl(self)
        scene = getattr(self, "active_scene", None)
        if scene is None:
            return
        objects = getattr(scene, "editable_objects", getattr(scene, "game_objects", []))
        if not objects:
            return

        from PySide6.QtGui import QPainter

        painter = QPainter(self)
        try:
            is_editor_view = not bool(getattr(self, "is_game_view", lambda: False)()) and not bool(getattr(self, "_is_playing", lambda: False)())
            for obj in objects:
                image = _image_component(obj)
                if image is None or not bool(getattr(image, "visible", True)):
                    continue
                path = _resolve_sprite_path(str(getattr(image, "sprite_path", "") or ""))
                if path is None:
                    continue
                pixmap = QPixmap(str(path))
                if pixmap.isNull():
                    continue
                transform = getattr(obj, "transform", None)
                if transform is None:
                    continue
                pos = getattr(transform, "position", [0, 0, 0])
                scale = getattr(transform, "scale", [64, 64, 1])
                x, y = self.world_to_viewport(pos)
                zoom = float(getattr(getattr(self, "camera", None), "zoom", 1.0))
                w = max(1.0, abs(float(scale[0])) * zoom)
                h = max(1.0, abs(float(scale[1])) * zoom)
                alpha = max(0.0, min(1.0, float(getattr(image, "alpha", 255)) / 255.0))
                rz = float(getattr(transform, "rz", 0.0))
                local_rect = QRectF(-w / 2.0, -h / 2.0, w, h)

                painter.save()
                painter.translate(float(x), float(y))
                painter.rotate(rz)
                painter.setOpacity(alpha)
                painter.drawPixmap(local_rect, pixmap, pixmap.rect())
                painter.setOpacity(1.0)
                if is_editor_view:
                    painter.setPen(QPen(_EDITOR_BOX, 1, Qt.DotLine))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRect(local_rect)
                painter.restore()
        finally:
            painter.end()

    Phase1ViewportWidget.paintGL = patched_paint_gl
    Phase1ViewportWidget._zennity_sprite_overlay_patch_applied = True
    return True
