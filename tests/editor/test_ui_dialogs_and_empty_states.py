from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_empty_state_is_reusable_and_used_by_bottom_panels() -> None:
    component = _source("editor/ui/empty_state.py")
    interface = _source("editor/interface_smoke_test.py")
    theme = _source("editor/ui/theme.py")

    assert "class EmptyStateWidget(QWidget)" in component
    assert 'setObjectName("EmptyState")' in component
    assert 'EmptyStateWidget("Nenhuma saída disponível"' in interface
    assert 'EmptyStateWidget("Depurador inativo"' in interface
    assert "QWidget#EmptyState" in theme
    assert "QLabel#EmptyStateDescription" in theme


def test_asset_preview_is_responsive_and_has_explicit_visual_state() -> None:
    interface = _source("editor/interface_smoke_test.py")
    runtime = _source("editor/isolated_editor_main.py")
    theme = _source("editor/ui/theme.py")
    preview_section = interface[interface.index("# Asset Preview aprimorado"):interface.index("console_row = QSplitter")]

    assert 'preview.setObjectName("AssetPreviewPanel")' in preview_section
    assert 'self.preview_label.setObjectName("AssetPreviewThumbnail")' in preview_section
    assert 'self.preview_details_label.setObjectName("AssetPreviewDetails")' in preview_section
    assert ".setFixedSize(" not in preview_section
    assert "setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)" in preview_section
    assert 'self._set_asset_preview_state("content")' in runtime
    assert 'QLabel#AssetPreviewThumbnail[uiState="empty"]' in theme


def test_component_picker_has_search_empty_state_and_no_local_palette() -> None:
    source = _source("editor/widgets/component_picker.py")

    assert 'self.setObjectName("ComponentPickerDialog")' in source
    assert 'self.tree.setObjectName("ComponentPickerTree")' in source
    assert 'QTreeWidgetItem(["Nenhum componente encontrado"])' in source
    assert 'setProperty("uiRole", "primary")' in source
    assert "setStyleSheet" not in source


def test_validation_and_preferences_dialogs_use_global_theme_contract() -> None:
    validation = _source("editor/widgets/project_validation_dialog.py")
    preferences = _source("editor/windows/preferences_dialog.py")
    theme = _source("editor/ui/theme.py")

    assert 'self.setObjectName("ProjectValidationDialog")' in validation
    assert 'status.setProperty("uiState", "success" if self.report.valid else "error")' in validation
    assert "summary.setStyleSheet" not in validation
    assert "status.setStyleSheet" not in validation
    assert "DEFAULT_TOKENS.danger" in validation
    assert 'self.setObjectName("PreferencesDialog")' in preferences
    assert "QDialog#ComponentPickerDialog" in theme
    assert "QDialog#ProjectValidationDialog" in theme
    assert "QDialog#PreferencesDialog" in theme
