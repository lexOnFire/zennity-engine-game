from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_animation_workspace_exposes_library_timeline_and_asset_actions() -> None:
    source = (ROOT / "editor" / "ui" / "workspace_builder.py").read_text(encoding="utf-8")

    for widget_name in (
        "animation_library_tree",
        "animation_timeline",
        "animation_new_button",
        "animation_open_button",
        "animation_save_button",
        "animation_save_as_button",
        "animation_duplicate_button",
        "animation_delete_button",
        "animation_apply_button",
        "animation_demo_button",
    ):
        assert f"window.{widget_name}" in source


def test_editor_integrates_zanim_without_removing_embedded_clips() -> None:
    source = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")
    operations = (ROOT / "editor" / "animation_workspace_operations.py").read_text(encoding="utf-8") + (ROOT / "editor" / "animation_asset_operations.py").read_text(encoding="utf-8") + (ROOT / "editor" / "animation_preview_operations.py").read_text(encoding="utf-8")

    assert "AnimationWorkspaceOperations" in source
    assert "load_animation_asset" in operations
    assert "save_animation_asset" in operations
    assert 'obj.setdefault("animator"' in operations
    assert '"asset_path"' in (ROOT / "engine" / "animation" / "clip_asset.py").read_text(encoding="utf-8")


def test_preview_index_exists_before_animation_workspace_is_configured() -> None:
    source = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")
    bootstrap = (ROOT / "editor" / "editor_bootstrap_controller.py").read_text(encoding="utf-8")
    preview_index = source.index("self._animator_preview_index = 0")
    compose = source.index("self._bootstrap.compose(")

    assert preview_index < compose
    assert "h._configure_animation_workspace()" in bootstrap


def test_zanim_can_be_applied_explicitly_or_dropped_on_an_object() -> None:
    source = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")
    controller = (ROOT / "editor" / "animation_workspace_controller.py").read_text(encoding="utf-8")
    operations = (ROOT / "editor" / "animation_workspace_operations.py").read_text(encoding="utf-8") + (ROOT / "editor" / "animation_asset_operations.py").read_text(encoding="utf-8") + (ROOT / "editor" / "animation_preview_operations.py").read_text(encoding="utf-8")

    assert "h.animation_apply_button.clicked.connect" in controller
    assert "h.animation_demo_button.clicked.connect" in controller
    assert 'path.suffix.lower() != ".zanim"' in operations
    assert "_apply_animation_asset_path_to_object" in operations


def test_animation_workspace_is_resizable_and_properties_scroll() -> None:
    source = (ROOT / "editor" / "ui" / "workspace_builder.py").read_text(encoding="utf-8")

    assert "window.animation_content_splitter = QSplitter(Qt.Horizontal)" in source
    assert "window.animation_content_splitter.setSizes([230, 700, 310])" in source
    assert "window.animation_properties_scroll.setWidgetResizable(True)" in source
    assert "window.animator_preview.setMinimumHeight(160)" in source
    assert "window.animator_preview.setMinimumSize(320, 260)" not in source


def test_animation_workspace_separates_asset_object_timeline_and_clip_properties() -> None:
    source = (ROOT / "editor" / "ui" / "workspace_builder.py").read_text(encoding="utf-8")
    runtime = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")
    controller = (ROOT / "editor" / "animation_workspace_controller.py").read_text(encoding="utf-8")
    operations = (ROOT / "editor" / "animation_workspace_operations.py").read_text(encoding="utf-8") + (ROOT / "editor" / "animation_asset_operations.py").read_text(encoding="utf-8") + (ROOT / "editor" / "animation_preview_operations.py").read_text(encoding="utf-8")

    for label in ("ASSET", "OBJETO", "TIMELINE", "OBJETO SELECIONADO", "PROPRIEDADES DO CLIP"):
        assert f'QLabel("{label}")' in source
    assert 'window.animation_new_button = QToolButton()' in source
    assert 'window.animation_delete_button.setProperty("uiRole", "danger")' in source
    assert 'suffix = "  •  ainda não salvo"' in controller
    assert 'self._set_animation_preview_state("error")' in operations
