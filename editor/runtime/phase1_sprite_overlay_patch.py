from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPen, QPixmap


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_EDITOR_BOX = QColor(80, 160, 255, 90)
_PATH_CACHE: dict[str, Path | None] = {}
_PIXMAP_CACHE: dict[str, QPixmap] = {}
_ROOTS_CACHE: list[Path] | None = None


def _candidate_roots() -> list[Path]:
    global _ROOTS_CACHE
    if _ROOTS_CACHE is not None:
        return _ROOTS_CACHE
    roots: list[Path] = []
    cwd = Path.cwd()
    roots.append(cwd)
    roots.extend(cwd.parents)
    here = Path(__file__).resolve()
    roots.append(here.parents[2])
    _ROOTS_CACHE = list(dict.fromkeys(roots))
    return _ROOTS_CACHE


def _resolve_sprite_path(path_value: str) -> Path | None:
    key = str(path_value or "").strip().replace("\\", "/")
    if not key:
        return None
    if key in _PATH_CACHE:
        return _PATH_CACHE[key]
    raw = Path(key)
    if raw.is_absolute():
        result = raw if raw.exists() else None
        _PATH_CACHE[key] = result
        return result
    for root in _candidate_roots():
        candidate = root / raw
        if candidate.exists() and candidate.is_file():
            _PATH_CACHE[key] = candidate
            return candidate
    name = raw.name.lower()
    for root in _candidate_roots():
        for base in (root / "Assets", root / "examples"):
            if not base.exists():
                continue
            for candidate in base.rglob("*"):
                if candidate.is_file() and candidate.name.lower() == name and candidate.suffix.lower() in _IMAGE_EXTENSIONS:
                    _PATH_CACHE[key] = candidate
                    return candidate
    _PATH_CACHE[key] = None
    return None


def _cached_pixmap(path: Path) -> QPixmap | None:
    key = str(path.resolve())
    pixmap = _PIXMAP_CACHE.get(key)
    if pixmap is None:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return None
        _PIXMAP_CACHE[key] = pixmap
    return pixmap


def _image_component(obj: Any) -> Any | None:
    if obj is None:
        return None
    for component in getattr(obj, "components", []):
        if getattr(component, "type_name", type(component).__name__) == "Image":
            if str(getattr(component, "sprite_path", "") or "").strip():
                return component
    return None


def _call_or_value(obj: Any, name: str, default: bool = False) -> Any:
    value = getattr(obj, name, default)
    return value() if callable(value) else value


def _selected_object(viewport: Any) -> Any | None:
    getter = getattr(viewport, "selected_object", None)
    if callable(getter):
        try:
            return getter()
        except Exception:
            return None
    return getattr(viewport, "selected", None)


def _is_rect_visible(x: float, y: float, w: float, h: float, viewport_w: int, viewport_h: int) -> bool:
    # Use a generous margin because rotated sprites can extend past their unrotated bounds.
    margin = max(w, h, 32.0) * 0.5
    return not (
        x + margin < 0
        or x - margin > viewport_w
        or y + margin < 0
        or y - margin > viewport_h
    )


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


def _patch_legacy_sprite_draw() -> None:
    """Avoid drawing an Image twice while the Scene View uses the Qt overlay.

    ``Editor2DScene._draw_object`` is the legacy Pygame path.  The Phase 1
    overlay is intentionally rendered after its framebuffer has been copied to
    Qt so it can use sub-pixel coordinates.  Without this guard both paths draw
    the same ImageComponent during a Scene View frame.

    The flag is scoped to a single paint call by ``patched_paint_gl`` below; it
    is never enabled in Game View or while playing, where Pygame remains the
    sole renderer.
    """
    try:
        from editor_legacy.editor_2d import Editor2DScene
    except Exception:
        return

    if getattr(Editor2DScene, "_zennity_qt_sprite_skip_patch_applied", False):
        return

    original_draw_object = Editor2DScene._draw_object

    def draw_object_without_qt_overlay_duplicates(self, screen, obj, idx=None, zoom=1.0, lay=None):
        overlay_ids = getattr(self, "_zennity_qt_overlay_sprite_ids", ())
        if id(obj) in overlay_ids:
            return
        return original_draw_object(self, screen, obj, idx, zoom, lay)

    Editor2DScene._draw_object = draw_object_without_qt_overlay_duplicates
    Editor2DScene._zennity_qt_sprite_skip_patch_applied = True


def _qt_overlay_sprite_ids(objects: list[Any]) -> set[int]:
    """Return only sprites the Qt pass can actually draw this frame."""
    result: set[int] = set()
    for obj in objects:
        image = _image_component(obj)
        if image is None or not bool(getattr(image, "visible", True)):
            continue
        path = _resolve_sprite_path(str(getattr(image, "sprite_path", "") or ""))
        if path is not None and _cached_pixmap(path) is not None:
            result.add(id(obj))
    return result


def apply_phase1_sprite_overlay_patch() -> bool:
    _patch_sprite_selection_overlay()
    # The Pygame framebuffer is the only source that draws sprites.  A second
    # Qt pixmap pass looked smoother but used a different camera transform,
    # which detached the visible sprite from its collider/selection box.
    return True
