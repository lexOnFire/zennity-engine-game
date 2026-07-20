from pathlib import Path

from editor.runtime.viewport_sprite_renderer import ViewportSpriteRenderer


def test_sprite_renderer_has_stable_layer_order_and_camera_filter() -> None:
    assert ViewportSpriteRenderer.LAYER_ORDER == {"Background": 0, "Default": 1, "Foreground": 2, "UI": 3}
    assert ViewportSpriteRenderer._is_camera({"camera": {}})
    assert not ViewportSpriteRenderer._is_camera({"mesh_type": "Sprite"})


def test_isolated_viewport_delegates_sprite_and_physics_work() -> None:
    source = (\n        Path("editor/isolated_viewport.py").read_text(encoding="utf-8")\n        + Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")\n    )
    assert "sprite_renderer.draw(" in source
    assert "physics_stepper.step(" in source
    assert "texture_cache[str(texture_path)]" not in source
