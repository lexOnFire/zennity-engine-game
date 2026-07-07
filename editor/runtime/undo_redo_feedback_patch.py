from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QShortcut


def _current_selected(editor: Any) -> Any | None:
    try:
        selected = editor.editor_context.selection.selected
        if selected is not None:
            return selected
    except Exception:
        pass
    try:
        return editor.viewport._selected_transform_object()
    except Exception:
        return None


def _refresh_editor_after_history(editor: Any, action_name: str) -> None:
    selected = _current_selected(editor)

    try:
        if hasattr(editor.viewport, "_sync_model_from_scene"):
            editor.viewport._sync_model_from_scene()
    except Exception:
        pass

    try:
        editor.refresh_hierarchy_from_viewport()
    except Exception:
        pass

    if selected is not None:
        try:
            editor.select_object(selected)
        except Exception:
            pass
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
            viewport._sync_selection_to_model()
        except Exception:
            pass
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


def _undo_now(editor: Any) -> None:
    commands = editor.editor_context.commands
    if not commands.can_undo:
        if hasattr(editor, "status_msg"):
            editor.status_msg.setText("Nada para desfazer")
        return
    commands.undo()
    _refresh_editor_after_history(editor, "Desfeito")


def _redo_now(editor: Any) -> None:
    commands = editor.editor_context.commands
    if not commands.can_redo:
        if hasattr(editor, "status_msg"):
            editor.status_msg.setText("Nada para refazer")
        return
    commands.redo()
    _refresh_editor_after_history(editor, "Refeito")


def _safe_disconnect(action: Any) -> None:
    try:
        action.triggered.disconnect()
    except Exception:
        pass


def _install_instance_shortcuts(editor: Any) -> bool:
    if getattr(editor, "_zennity_undo_redo_instance_patched", False):
        return True
    editor._zennity_undo_redo_instance_patched = True

    def undo_bound() -> None:
        _undo_now(editor)

    def redo_bound() -> None:
        _redo_now(editor)

    editor.undo = undo_bound
    editor.redo = redo_bound

    act_undo = getattr(editor, "act_undo", None)
    if act_undo is not None:
        _safe_disconnect(act_undo)
        act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        act_undo.setShortcutContext(Qt.ApplicationShortcut)
        act_undo.triggered.connect(undo_bound)
    act_redo = getattr(editor, "act_redo", None)
    if act_redo is not None:
        _safe_disconnect(act_redo)
        act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        act_redo.setShortcutContext(Qt.ApplicationShortcut)
        act_redo.triggered.connect(redo_bound)

    shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), editor)
    shortcut_undo.setContext(Qt.ApplicationShortcut)
    shortcut_undo.activated.connect(undo_bound)
    shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), editor)
    shortcut_redo.setContext(Qt.ApplicationShortcut)
    shortcut_redo.activated.connect(redo_bound)
    shortcut_redo_alt = QShortcut(QKeySequence("Ctrl+Shift+Z"), editor)
    shortcut_redo_alt.setContext(Qt.ApplicationShortcut)
    shortcut_redo_alt.activated.connect(redo_bound)
    editor._zennity_undo_shortcuts = (shortcut_undo, shortcut_redo, shortcut_redo_alt)

    try:
        editor._update_undo_redo_states()
    except Exception:
        pass
    return True


def _scan_and_install_instances() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    installed = False
    for widget in app.topLevelWidgets():
        if all(hasattr(widget, attr) for attr in ("editor_context", "viewport", "inspector")):
            installed = _install_instance_shortcuts(widget) or installed
    return installed


def apply_undo_redo_feedback_patch() -> bool:
    try:
        from editor.phase1_editor import ZennityPhase1Editor
    except Exception:
        # Se o editor ainda esta carregando, instala por varredura quando a janela existir.
        app = QApplication.instance()
        if app is not None:
            for delay in (0, 200, 600, 1200):
                QTimer.singleShot(delay, _scan_and_install_instances)
        return False

    if not getattr(ZennityPhase1Editor, "_zennity_undo_redo_feedback_patch_applied", False):
        def undo(self) -> None:
            _undo_now(self)

        def redo(self) -> None:
            _redo_now(self)

        original_connect = ZennityPhase1Editor._connect

        def connect(self) -> None:
            original_connect(self)
            _install_instance_shortcuts(self)

        ZennityPhase1Editor.undo = undo
        ZennityPhase1Editor.redo = redo
        ZennityPhase1Editor._connect = connect
        ZennityPhase1Editor._zennity_undo_redo_feedback_patch_applied = True

    app = QApplication.instance()
    if app is not None:
        for delay in (0, 200, 600, 1200):
            QTimer.singleShot(delay, _scan_and_install_instances)
    return True
