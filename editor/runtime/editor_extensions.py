from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class EditorExtension(Protocol):
    name: str

    def install(self, editor: Any) -> None: ...

    def uninstall(self, editor: Any) -> None: ...


ExtensionErrorHandler = Callable[[str, Exception], None]


@dataclass(frozen=True)
class InstalledExtension:
    name: str
    extension: EditorExtension


class EditorExtensionManager:
    """Installs editor extensions explicitly and tears them down in reverse order."""

    def __init__(self, editor: Any, on_error: ExtensionErrorHandler | None = None) -> None:
        self.editor = editor
        self.on_error = on_error
        self._installed: list[InstalledExtension] = []
        self._installed_names: set[str] = set()

    @property
    def installed_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self._installed)

    def install(self, extension: EditorExtension) -> bool:
        name = str(extension.name).strip()
        if not name:
            raise ValueError("editor extension name cannot be empty")
        if name in self._installed_names:
            return False
        try:
            extension.install(self.editor)
        except Exception as exc:
            if self.on_error is None:
                raise
            self.on_error(name, exc)
            return False
        self._installed.append(InstalledExtension(name, extension))
        self._installed_names.add(name)
        return True

    def uninstall_all(self) -> None:
        for installed in reversed(self._installed):
            try:
                installed.extension.uninstall(self.editor)
            except Exception as exc:
                if self.on_error is not None:
                    self.on_error(installed.name, exc)
        self._installed.clear()
        self._installed_names.clear()


class AssetDragDropExtension:
    name = "asset_drag_drop"

    def install(self, editor: Any) -> None:
        from editor.runtime.asset_drag_drop_patch import apply_asset_drag_drop_patch

        apply_asset_drag_drop_patch(editor)

    def uninstall(self, editor: Any) -> None:
        # Qt owns the event filters through their widget parents. They are
        # destroyed with the editor; no global class state needs restoration.
        return None


def default_editor_extensions() -> tuple[EditorExtension, ...]:
    return (AssetDragDropExtension(),)
