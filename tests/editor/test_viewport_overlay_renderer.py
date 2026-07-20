from pathlib import Path

from editor.runtime.viewport_overlay_renderer import ViewportOverlayRenderer


def test_overlay_renderer_recognizes_all_runtime_camera_shapes() -> None:
    assert ViewportOverlayRenderer._is_camera({"component_names": ["Camera2D"]})
    assert ViewportOverlayRenderer._is_camera({"camera": {"active": True}})
    assert ViewportOverlayRenderer._is_camera({"mesh_type": "Camera"})
    assert not ViewportOverlayRenderer._is_camera({"mesh_type": "Sprite"})


def test_isolated_viewport_delegates_overlays_and_gizmos() -> None:
    source = (\n        Path("editor/isolated_viewport.py").read_text(encoding="utf-8")\n        + Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")\n    )
    sprite_renderer = Path("editor/runtime/viewport_sprite_renderer.py").read_text(encoding="utf-8")
    renderer = Path("editor/runtime/viewport_overlay_renderer.py").read_text(encoding="utf-8")

    assert "overlay_renderer.draw_scene(" in source
    assert "overlay_renderer.draw_selection(" in sprite_renderer
    assert "overlay_renderer.draw_hud(" in source
    assert "def draw_scene(" in renderer
    assert "def draw_selection(" in renderer
    assert "def draw_hud(" in renderer
