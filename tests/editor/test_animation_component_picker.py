from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_animation_picker_discovers_searches_and_previews_zanim_assets() -> None:
    source = _source("editor/widgets/animation_picker.py")

    assert "class AnimationPickerDialog(QDialog)" in source
    assert 'self.setObjectName("AnimationPickerDialog")' in source
    assert 'directory.rglob("*.zanim")' in source
    assert "load_animation_asset(path)" in source
    assert 'self.search.setPlaceholderText("Pesquisar animação...")' in source
    assert 'self.preview.setObjectName("AnimationPickerPreview")' in source
    assert "Frames:" in source
    assert "Sprite Sheet:" in source
    assert "frame_pixmap = pixmap.copy" in source
    assert 'return "Sprite Sheet não definido"' in source
    assert '"  — incompleta" if error else ""' in source
    assert "QFileDialog" not in source


def test_animator_component_opens_picker_before_mutating_object() -> None:
    source = _source("editor/isolated_editor_main.py")
    add_start = source.index("def _add_component")
    choose_start = source.index("def _choose_animation_component", add_start)
    add_method = source[add_start:choose_start]
    choose_method = source[choose_start:source.index("def _send_inspector_physics", choose_start)]

    assert 'if component == "animator":' in add_method
    assert "self._choose_animation_component()" in add_method
    assert "AnimationPickerDialog(Path.cwd(), self)" in choose_method
    assert "picker.exec()" in choose_method
    assert "_apply_animation_asset_path_to_object(picker.selected_path, object_name)" in choose_method


def test_animation_picker_preserves_create_and_empty_compatibility_paths() -> None:
    picker = _source("editor/widgets/animation_picker.py")
    editor = _source("editor/isolated_editor_main.py")

    assert 'self.create_button = QPushButton("Criar nova")' in picker
    assert 'self.empty_button = QPushButton("Adicionar vazio")' in picker
    assert 'self._finish("create")' in picker
    assert 'self._finish("empty")' in picker
    assert 'picker.requested_action == "create"' in editor
    assert "self.viewport_tabs.setCurrentIndex(2)" in editor
    assert 'picker.requested_action == "empty"' in editor
    assert "já possui um Animator 2D" in editor
    assert '"active_clip": "Idle"' in editor


def test_animation_picker_uses_global_theme() -> None:
    source = _source("editor/widgets/animation_picker.py")
    theme = _source("editor/ui/theme.py")

    assert "setStyleSheet" not in source
    assert "QDialog#AnimationPickerDialog" in theme
    assert "QListWidget#AnimationPickerList" in theme
    assert "QWidget#AnimationPickerDetailsPanel" in theme
