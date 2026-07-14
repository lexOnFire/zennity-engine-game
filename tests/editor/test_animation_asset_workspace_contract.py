from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_animation_workspace_exposes_library_timeline_and_asset_actions() -> None:
    source = (ROOT / "editor" / "interface_smoke_test.py").read_text(encoding="utf-8")

    for widget_name in (
        "animation_library_tree",
        "animation_timeline",
        "animation_new_button",
        "animation_open_button",
        "animation_save_button",
        "animation_save_as_button",
        "animation_duplicate_button",
        "animation_delete_button",
    ):
        assert f"self.{widget_name}" in source


def test_editor_integrates_zanim_without_removing_embedded_clips() -> None:
    source = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")

    assert "load_animation_asset" in source
    assert "save_animation_asset" in source
    assert 'obj.setdefault("animator"' in source
    assert '"asset_path"' in (ROOT / "engine" / "animation" / "clip_asset.py").read_text(encoding="utf-8")


def test_preview_index_exists_before_animation_workspace_is_configured() -> None:
    source = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")
    init_start = source.index("def __init__")
    preview_index = source.index("self._animator_preview_index = 0", init_start)
    configure_workspace = source.index("self._configure_animation_workspace()", init_start)

    assert preview_index < configure_workspace
