"""Extensões explícitas do editor e camada isolada de compatibilidade."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


Installer = Callable[[Any], Any]


@dataclass(frozen=True, slots=True)
class EditorExtension:
    name: str
    install: Installer
    compatibility_only: bool = False


class EditorExtensionRegistry:
    def __init__(self) -> None:
        self._extensions: list[EditorExtension] = []
        self._installed: set[tuple[int, str]] = set()

    def register(self, extension: EditorExtension) -> None:
        if any(item.name == extension.name for item in self._extensions):
            raise ValueError(f"Extensão duplicada: {extension.name}")
        self._extensions.append(extension)

    def install_all(self, editor: Any, *, include_compatibility: bool = False) -> list[str]:
        installed: list[str] = []
        for extension in self._extensions:
            if extension.compatibility_only and not include_compatibility:
                continue
            key = (id(editor), extension.name)
            if key in self._installed:
                continue
            extension.install(editor)
            self._installed.add(key)
            installed.append(extension.name)
        return installed


def phase1_compatibility_extensions() -> EditorExtensionRegistry:
    """Centraliza patches do shell embutido até sua remoção na versão 2.0."""
    registry = EditorExtensionRegistry()

    def undo_redo(editor: Any) -> Any:
        from editor.runtime.undo_redo_feedback_patch import _install_instance_shortcuts
        return _install_instance_shortcuts(editor)

    def asset_drag_drop(editor: Any) -> Any:
        from editor.runtime.asset_drag_drop_patch import apply_asset_drag_drop_patch
        return apply_asset_drag_drop_patch(editor)

    registry.register(EditorExtension("legacy-undo-redo-feedback", undo_redo, compatibility_only=True))
    registry.register(EditorExtension("legacy-asset-drag-drop", asset_drag_drop, compatibility_only=True))
    return registry
