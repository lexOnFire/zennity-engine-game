from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class EditorExtension(Protocol):
    name: str

    def load(self, editor: Any) -> None:
        """Called when the extension is first loaded into memory."""
        pass

    def enable(self, editor: Any) -> None:
        """Called to activate the extension features."""
        pass

    def disable(self, editor: Any) -> None:
        """Called to deactivate the extension features (e.g. before unload or hot-reload)."""
        pass

    def unload(self, editor: Any) -> None:
        """Called when the extension is completely removed."""
        pass


ExtensionErrorHandler = Callable[[str, str, Exception], None]


@dataclass(frozen=True)
class InstalledExtension:
    name: str
    extension: EditorExtension


class EditorExtensionManager:
    """Manages full lifecycle of editor extensions with rollback on failure."""

    def __init__(self, editor: Any, on_error: ExtensionErrorHandler | None = None) -> None:
        self.editor = editor
        self.on_error = on_error
        self._installed: list[InstalledExtension] = []
        self._installed_names: set[str] = set()

    @property
    def installed_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self._installed)

    def _report_error(self, name: str, phase: str, exc: Exception) -> None:
        if self.on_error:
            self.on_error(name, phase, exc)
        else:
            print(f"Extension '{name}' failed during '{phase}': {exc}")

    def install(self, extension: EditorExtension) -> bool:
        name = str(extension.name).strip()
        if not name:
            raise ValueError("editor extension name cannot be empty")
        if name in self._installed_names:
            return False

        # Phase 1: Load
        try:
            if hasattr(extension, "load"):
                extension.load(self.editor)
        except Exception as exc:
            self._report_error(name, "load", exc)
            return False

        # Phase 2: Enable
        try:
            if hasattr(extension, "enable"):
                extension.enable(self.editor)
        except Exception as exc:
            self._report_error(name, "enable", exc)
            # Rollback enable by calling disable (if it was partially enabled) and then unload
            try:
                if hasattr(extension, "disable"):
                    extension.disable(self.editor)
            except Exception as d_exc:
                self._report_error(name, "disable (rollback)", d_exc)
            try:
                if hasattr(extension, "unload"):
                    extension.unload(self.editor)
            except Exception as u_exc:
                self._report_error(name, "unload (rollback)", u_exc)
            return False

        self._installed.append(InstalledExtension(name, extension))
        self._installed_names.add(name)
        return True

    def uninstall_all(self) -> None:
        for installed in reversed(self._installed):
            ext = installed.extension
            # Phase 1: Disable
            try:
                if hasattr(ext, "disable"):
                    ext.disable(self.editor)
            except Exception as exc:
                self._report_error(installed.name, "disable", exc)
            
            # Phase 2: Unload
            try:
                if hasattr(ext, "unload"):
                    ext.unload(self.editor)
            except Exception as exc:
                self._report_error(installed.name, "unload", exc)
                
        self._installed.clear()
        self._installed_names.clear()


class AssetDragDropExtension:
    name = "asset_drag_drop"

    def load(self, editor: Any) -> None:
        pass
        
    def enable(self, editor: Any) -> None:
        from editor.runtime.asset_drag_drop import install_asset_drag_drop
        install_asset_drag_drop(editor)

    def disable(self, editor: Any) -> None:
        # Qt owns the event filters through their widget parents. They are
        # destroyed with the editor; no global class state needs restoration.
        pass
        
    def unload(self, editor: Any) -> None:
        pass


def default_editor_extensions() -> tuple[EditorExtension, ...]:
    return (AssetDragDropExtension(),)

