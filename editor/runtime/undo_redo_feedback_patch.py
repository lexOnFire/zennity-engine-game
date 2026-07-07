from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QApplication


def _refresh_editor_after_history(editor: Any, action_name: str) -> None:
    try:
        editor.refresh_hierarchy_from_viewport()
    except Exception:
        pass

    selected = None
    try:
        selected = editor.editor_context.selection.selected
    except Exception:
        selected = None

    if selected is not None:
        try:
            editor.on_viewport_selection_changed(selected)
        except Exception:
            pass
        try:
            editor.inspector.load_object(selected)
        except Exception:
            pass

    for attr in ("viewport", "game_viewport"):
        viewport = getattr(editor, attr, None)
        if viewport is None:
            continue
        try:
            viewport.update()
            viewport.repaint()
        except Exception:
            pass

    try:
        editor._update_undo_redo_states()
    except Exception:
        pass

    if hasattr(editor, "status_msg"):
        try:
            editor.status_msg.setText(action_name)
        except Exception:
            pass

    app = QApplication.instance()
    if app is not None:
        app.processEvents()


def apply_undo_redo_feedback_patch() -> bool:
    try:
        from editor.phase1_editor import ZennityPhase1Editor
    except Exception:
        return False

    if getattr(ZennityPhase1Editor, "_zennity_undo_redo_feedback_patch_applied", False):
        return True

    def undo(self) -> None:
        commands = self.editor_context.commands
        if not commands.can_undo:
            if hasattr(self, "status_msg"):
                self.status_msg.setText("Nada para desfazer")
            return
        commands.undo()
        _refresh_editor_after_history(self, "Desfeito")

    def redo(self) -> None:
        commands = self.editor_context.commands
        if not commands.can_redo:
            if hasattr(self, "status_msg"):
                self.status_msg.setText("Nada para refazer")
            return
        commands.redo()
        _refresh_editor_after_history(self, "Refeito")

    ZennityPhase1Editor.undo = undo
    ZennityPhase1Editor.redo = redo
    ZennityPhase1Editor._zennity_undo_redo_feedback_patch_applied = True
    return True
