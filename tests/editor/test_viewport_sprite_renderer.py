from pathlib import Path

from editor.runtime.viewport_sprite_renderer import ViewportSpriteRenderer, _safe_color


def test_sprite_renderer_has_stable_layer_order_and_camera_filter() -> None:
    assert ViewportSpriteRenderer.LAYER_ORDER == {"Background": 0, "Default": 1, "Foreground": 2, "UI": 3}
    assert ViewportSpriteRenderer._is_camera({"camera": {}})
    assert not ViewportSpriteRenderer._is_camera({"mesh_type": "Sprite"})


def test_sprite_renderer_accepts_hex_and_sanitizes_invalid_colors() -> None:
    assert _safe_color("#ff8040", (1, 2, 3)) == (255, 128, 64)
    assert _safe_color([300, -5, 12.8], (1, 2, 3)) == (255, 0, 12)
    assert _safe_color("not-a-color", (1, 2, 3)) == (1, 2, 3)


def test_isolated_viewport_delegates_sprite_and_physics_work() -> None:
    source = (
        Path("editor/isolated_viewport.py").read_text(encoding="utf-8")
        + Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")
        + Path("editor/runtime/viewport_session_lifecycle.py").read_text(encoding="utf-8")
    )
    assert "sprite_renderer.draw(" in source
    assert "physics_stepper.step(" in source
    assert "texture_cache[str(texture_path)]" not in source
