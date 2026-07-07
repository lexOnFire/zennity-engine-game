from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication


# ---------------------------------------------------------------------------
# Helpers de refresh da UI
# ---------------------------------------------------------------------------

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


def _refresh_viewport(viewport: Any) -> None:
    if viewport is None:
        return
    for method in ("_apply_qt_shims", "_sync_model_from_scene", "_sync_selection_to_model"):
        try:
            getattr(viewport, method)()
        except Exception:
            pass
    try:
        viewport.update()
    except Exception:
        pass


def _refresh_editor(editor: Any, label: str = "") -> None:
    """Sincroniza viewport, hierarquia e inspector apos undo/redo."""
    selected = _current_selected(editor)

    for attr in ("viewport", "game_viewport"):
        _refresh_viewport(getattr(editor, attr, None))

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
            editor.inspector.load_object(selected)
        except Exception:
            pass

    try:
        editor._update_undo_redo_states()
    except Exception:
        pass

    if label and hasattr(editor, "status_msg"):
        try:
            editor.status_msg.setText(label)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Inscricao nos callbacks do CommandManager
# ---------------------------------------------------------------------------

def _subscribe_refresh_callbacks(editor: Any) -> None:
    """Inscreve refresh de UI nos callbacks do CommandManager.

    Usa on_after_undo e on_after_redo em vez de QTimer dispersos,
    garantindo que o refresh aconteca exatamente uma vez e de forma sincrona.
    """
    commands = getattr(getattr(editor, "editor_context", None), "commands", None)
    if commands is None:
        return

    # Evita duplicar inscricoes
    if getattr(editor, "_zennity_undo_redo_callbacks_subscribed", False):
        return
    editor._zennity_undo_redo_callbacks_subscribed = True

    def after_undo(cmd: Any) -> None:
        _refresh_editor(editor, f"Desfeito: {cmd.description}")

    def after_redo(cmd: Any) -> None:
        _refresh_editor(editor, f"Refeito: {cmd.description}")

    if hasattr(commands, "on_after_undo"):
        commands.on_after_undo.append(after_undo)
    if hasattr(commands, "on_after_redo"):
        commands.on_after_redo.append(after_redo)


# ---------------------------------------------------------------------------
# Instalacao de atalhos e metodos no editor
# ---------------------------------------------------------------------------

def _safe_disconnect(action: Any) -> None:
    try:
        action.triggered.disconnect()
    except Exception:
        pass


def _install_instance_shortcuts(editor: Any) -> bool:
    _subscribe_refresh_callbacks(editor)

    if getattr(editor, "_zennity_undo_redo_instance_patched", False):
        # Garante que botoes apontem para os metodos certos mesmo se reinstalado
        try:
            if getattr(editor, "act_undo", None) is not None:
                _safe_disconnect(editor.act_undo)
                editor.act_undo.triggered.connect(
                    lambda checked=False, e=editor: _do_undo(e)
                )
            if getattr(editor, "act_redo", None) is not None:
                _safe_disconnect(editor.act_redo)
                editor.act_redo.triggered.connect(
                    lambda checked=False, e=editor: _do_redo(e)
                )
        except Exception:
            pass
        return True

    editor._zennity_undo_redo_instance_patched = True

    def _do_undo(e: Any) -> None:
        commands = getattr(getattr(e, "editor_context", None), "commands", None)
        if commands is None or not commands.can_undo:
            if hasattr(e, "status_msg"):
                e.status_msg.setText("Nada para desfazer")
            return
        commands.undo()  # callbacks disparam _refresh_editor automaticamente

    def _do_redo(e: Any) -> None:
        commands = getattr(getattr(e, "editor_context", None), "commands", None)
        if commands is None or not commands.can_redo:
            if hasattr(e, "status_msg"):
                e.status_msg.setText("Nada para refazer")
            return
        commands.redo()  # callbacks disparam _refresh_editor automaticamente

    editor.undo = lambda: _do_undo(editor)
    editor.redo = lambda: _do_redo(editor)

    act_undo = getattr(editor, "act_undo", None)
    if act_undo is not None:
        _safe_disconnect(act_undo)
        act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        act_undo.setShortcutContext(Qt.ApplicationShortcut)
        act_undo.triggered.connect(lambda checked=False, e=editor: _do_undo(e))

    act_redo = getattr(editor, "act_redo", None)
    if act_redo is not None:
        _safe_disconnect(act_redo)
        act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        act_redo.setShortcutContext(Qt.ApplicationShortcut)
        act_redo.triggered.connect(lambda checked=False, e=editor: _do_redo(e))

    shortcut_undo = QShortcut(QKeySequence("Ctrl+Z"), editor)
    shortcut_undo.setContext(Qt.ApplicationShortcut)
    shortcut_undo.activated.connect(lambda: _do_undo(editor))

    shortcut_redo = QShortcut(QKeySequence("Ctrl+Y"), editor)
    shortcut_redo.setContext(Qt.ApplicationShortcut)
    shortcut_redo.activated.connect(lambda: _do_redo(editor))

    shortcut_redo_alt = QShortcut(QKeySequence("Ctrl+Shift+Z"), editor)
    shortcut_redo_alt.setContext(Qt.ApplicationShortcut)
    shortcut_redo_alt.activated.connect(lambda: _do_redo(editor))

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
    from PySide6.QtCore import QTimer

    try:
        from editor.phase1_editor import ZennityPhase1Editor
    except Exception:
        app = QApplication.instance()
        if app is not None:
            for delay in (0, 200, 600, 1200):
                QTimer.singleShot(delay, _scan_and_install_instances)
        return False

    if not getattr(ZennityPhase1Editor, "_zennity_undo_redo_feedback_patch_applied", False):
        original_connect = ZennityPhase1Editor._connect

        def patched_connect(self) -> None:
            original_connect(self)
            _install_instance_shortcuts(self)

        ZennityPhase1Editor.undo = lambda self: _scan_and_install_instances() or self.editor_context.commands.undo()
        ZennityPhase1Editor.redo = lambda self: _scan_and_install_instances() or self.editor_context.commands.redo()
        ZennityPhase1Editor._connect = patched_connect
        ZennityPhase1Editor._zennity_undo_redo_feedback_patch_applied = True

    app = QApplication.instance()
    if app is not None:
        for delay in (0, 200, 600, 1200, 2400):
            QTimer.singleShot(delay, _scan_and_install_instances)
    return True
