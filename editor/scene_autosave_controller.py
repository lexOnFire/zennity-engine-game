"""Debounced scene autosave for viewport editing."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer

from editor.autosave_manager import AutosaveManager


class SceneAutosaveController:
    """Save named scenes in place and keep recovery for untitled scenes."""

    def __init__(self, host: Any, project_root: Path, delay_ms: int = 1200) -> None:
        self.host = host
        self._manager = AutosaveManager(
            project_root,
            snapshot_fn=self.snapshot,
            interval_seconds=300,
        )
        self._timer = QTimer(host)
        self._timer.setSingleShot(True)
        self._timer.setInterval(max(250, int(delay_ms)))
        self._timer.timeout.connect(self.flush)

    def start(self) -> None:
        self._manager.start()

    def schedule(self) -> None:
        if not self.host._play_session.is_running:
            self._timer.start()

    def flush(self) -> bool:
        self._timer.stop()
        h = self.host
        recovery_saved = self._manager.flush()
        path = h._current_scene_path
        if path is None:
            if recovery_saved:
                h.statusBar().showMessage("Autosave de recuperação atualizado")
            return recovery_saved
        try:
            h._scene_document = h._scene_persistence.save(
                Path(path), h._scene_snapshot, h._scene_document
            )
        except (OSError, ValueError, TypeError) as exc:
            h._log("WARN", f"Autosave falhou: {exc}")
            h.statusBar().showMessage(f"Autosave falhou: {exc}")
            return False
        h.statusBar().showMessage(f"Autosave: {Path(path).name}")
        return True

    def snapshot(self) -> dict[str, Any]:
        h = self.host
        return {
            "scene_path": str(h._current_scene_path) if h._current_scene_path else None,
            "scene_document": deepcopy(h._scene_document),
            "objects": deepcopy(h._scene_snapshot),
            "selected": h._selected_name,
        }

    def stop(self) -> None:
        self._timer.stop()
        self._manager.stop()
