"""Document lifecycle operations for the Animator controller editor."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from engine.animation.controller_asset import (
    default_animator_controller,
    load_animator_controller,
    save_animator_controller,
)


class AnimatorDocumentMixin:
    @property
    def current_path(self) -> Path | None:
        return self.path

    def new_document(self) -> None:
        self.path = None
        self.saved_path = None
        self.data = default_animator_controller()
        self.name_field.setText(str(self.data["name"]))
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._reset_preview()
        self._refresh_all()

    def load_document(self, path: str | Path) -> bool:
        try:
            self.path = Path(path).resolve()
            self.saved_path = self.path
            self.data = load_animator_controller(self.path)
            self.name_field.setText(str(self.data["name"]))
            self._undo_stack.clear()
            self._redo_stack.clear()
            self._reset_preview()
            self._refresh_all()
            return True
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Animator Controller", str(exc))
            return False

    def open_dialog(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir Animator Controller",
            str(self.project_root / "Assets" / "Animations"),
            "Zennity Animator (*.zanimator);;Todos os arquivos (*.*)",
        )
        if filename:
            self.load_document(filename)

    def save(self) -> None:
        self._save()

    def _cancel_or_reload(self) -> None:
        if not self.embedded:
            self.reject()
            return
        if self.path and self.path.is_file():
            self.load_document(self.path)
        else:
            self.new_document()

    def _save(self) -> None:
        name = self.name_field.text().strip()
        if not name:
            QMessageBox.warning(self, "Nome obrigatório", "Informe um nome para o controller.")
            return
        self.data["name"] = name
        self.data["initial_state"] = self.initial_combo.currentText()
        if self.path is None:
            safe_name = "".join(
                character if character.isalnum() or character in "-_" else "_"
                for character in name
            )
            self.path = self.project_root / "Assets" / "Animations" / f"{safe_name}.zanimator"
        save_animator_controller(self.path, self.data)
        self.saved_path = self.path
        if not self.embedded:
            self.accept()
