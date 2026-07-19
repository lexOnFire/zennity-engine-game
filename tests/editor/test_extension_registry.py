import pytest

from editor.extensions import EditorExtension, EditorExtensionRegistry


def test_extensions_are_explicit_idempotent_and_compatibility_gated():
    calls = []
    registry = EditorExtensionRegistry()
    registry.register(EditorExtension("modern", lambda editor: calls.append(("modern", editor))))
    registry.register(EditorExtension("legacy", lambda editor: calls.append(("legacy", editor)), compatibility_only=True))
    editor = object()
    assert registry.install_all(editor) == ["modern"]
    assert registry.install_all(editor) == []
    assert registry.install_all(editor, include_compatibility=True) == ["legacy"]
    assert [name for name, _ in calls] == ["modern", "legacy"]


def test_extension_names_are_unique():
    registry = EditorExtensionRegistry()
    registry.register(EditorExtension("one", lambda editor: None))
    with pytest.raises(ValueError):
        registry.register(EditorExtension("one", lambda editor: None))
