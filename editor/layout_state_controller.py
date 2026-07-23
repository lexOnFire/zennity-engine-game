"""Versioned and recoverable persistence for the editor window layout."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSettings


class LayoutStateController:
    """Persist Qt window state without trapping users in a corrupt layout."""

    SCHEMA_VERSION = 1

    def __init__(self, host: Any, settings: Any | None = None) -> None:
        self.host = host
        self.settings = settings or QSettings("Zennity", "EditorLayout")
        self._default_geometry = host.saveGeometry()
        self._default_state = host.saveState(self.SCHEMA_VERSION)

    def save(self) -> None:
        self.settings.setValue("schemaVersion", self.SCHEMA_VERSION)
        self.settings.setValue("geometry", self.host.saveGeometry())
        self.settings.setValue("windowState", self.host.saveState(self.SCHEMA_VERSION))
        sync = getattr(self.settings, "sync", None)
        if callable(sync):
            sync()

    def restore(self) -> bool:
        try:
            version = int(self.settings.value("schemaVersion", 0))
        except (TypeError, ValueError):
            version = 0
        geometry = self.settings.value("geometry")
        state = self.settings.value("windowState")
        if version != self.SCHEMA_VERSION or geometry is None or state is None:
            return False
        try:
            geometry_ok = bool(self.host.restoreGeometry(geometry))
            state_ok = bool(self.host.restoreState(state, self.SCHEMA_VERSION))
        except (TypeError, ValueError, RuntimeError):
            geometry_ok = state_ok = False
        if geometry_ok and state_ok:
            return True
        self.reset()
        return False

    def reset(self) -> None:
        self.settings.remove("geometry")
        self.settings.remove("windowState")
        self.settings.remove("schemaVersion")
        self.host.restoreGeometry(self._default_geometry)
        self.host.restoreState(self._default_state, self.SCHEMA_VERSION)

