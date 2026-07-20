from pathlib import Path

from editor.ui.icons import TOOLBAR_GLYPHS, component_title
from editor.ui.theme import EDITOR_QSS, build_editor_stylesheet
from editor.ui.tokens import DEFAULT_TOKENS, EditorThemeTokens


def test_stylesheet_is_generated_from_tokens_without_placeholders() -> None:
    stylesheet = build_editor_stylesheet()

    assert "$" not in stylesheet
    assert DEFAULT_TOKENS.bg in stylesheet
    assert DEFAULT_TOKENS.accent in stylesheet
    assert "QToolBar#CommandBar" in stylesheet
    assert "QTreeWidget#HierarchyTree" in stylesheet
    assert "QWidget#InspectorComponentHeader" in stylesheet
    assert stylesheet == EDITOR_QSS


def test_theme_can_be_recolored_without_editing_widget_code() -> None:
    custom = EditorThemeTokens(accent="#ff00aa", bg="#010203")
    stylesheet = build_editor_stylesheet(custom)

    assert "#ff00aa" in stylesheet
    assert "#010203" in stylesheet
    assert DEFAULT_TOKENS.accent not in stylesheet


def test_toolbar_and_component_glyphs_are_centralized_and_monochrome() -> None:
    assert set(TOOLBAR_GLYPHS) == {
        "Novo", "Abrir", "Salvar", "Desfazer", "Refazer", "Select",
        "Move", "Rotate", "Scale", "Snap: OFF", "Play", "Pause", "Stop",
    }
    assert TOOLBAR_GLYPHS["Play"] == "▶"
    assert component_title("sprite", "Sprite Renderer") == "▧  Sprite Renderer"


def test_editor_applies_foundation_and_exposes_semantic_widget_names() -> None:
    interface = (\n        Path("editor/interface_smoke_test.py").read_text(encoding="utf-8")\n        + Path("editor/ui/docks_builder.py").read_text(encoding="utf-8")\n    )
    main = Path("editor/isolated_editor_main.py").read_text(encoding="utf-8")
    compatibility = Path("editor/premium_theme.py").read_text(encoding="utf-8")

    assert "apply_editor_theme(app)" in interface
    assert "apply_editor_theme(app)" in main
    assert 'setObjectName("HierarchyTree")' in interface
    assert 'setObjectName("AssetsTree")' in interface
    assert 'setObjectName("InspectorToolbar")' in interface
    assert 'setObjectName("InspectorPanel")' in interface
    assert "PREMIUM_QSS = EDITOR_QSS" in compatibility


def test_ui_foundation_documents_no_inline_style_rule() -> None:
    documentation = Path("docs/editor_ui_foundation.md").read_text(encoding="utf-8")

    assert "setStyleSheet()" in documentation
    assert "conteúdo realmente dinâmico" in documentation
    assert "uiRole" in documentation
    assert "objectName" in documentation
