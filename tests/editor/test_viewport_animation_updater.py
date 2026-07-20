from pathlib import Path


def test_isolated_viewport_delegates_animation_frames_and_events() -> None:
    viewport = (\n        Path("editor/isolated_viewport.py").read_text(encoding="utf-8")\n        + Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")\n    )
    updater = Path("editor/runtime/viewport_animation_updater.py").read_text(encoding="utf-8")

    assert "animation_updater.update(dt)" in viewport
    assert "def update_animations" not in viewport
    assert "class ViewportAnimationUpdater" in updater
    assert 'hook = getattr(module, "on_animation_event", None)' in updater
    assert 'self.state_hook(object_name, "on_animation_state_enter"' in updater
