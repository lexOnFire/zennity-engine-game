from __future__ import annotations

"""Drag-and-drop de assets da aba Resources para Viewport e Inspector.

Melhorias em relacao a versao anterior:
 - Toda aplicacao de asset passa pelo CommandManager (suporte a undo/redo).
 - Feedback visual de hover no widget alvo durante o arrasto.
 - Unifica a logica duplicada de asset_drag_drop_patch e asset_direct_drop_patch.
"""

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QMimeData, QObject, QTimer, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QApplication, QAbstractItemView, QTreeWidgetItem, QWidget

_ASSET_MIME = "application/x-zennity-asset-path"
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_SCRIPT_EXTENSIONS = {".py"}

_HOVER_STYLE_VALID = "border: 2px solid #4f98a3;"
_HOVER_STYLE_RESET = ""


# ---------------------------------------------------------------------------
# Helpers de tipo e path
# ---------------------------------------------------------------------------

def _event_pos(event: Any):
    return event.position().toPoint() if hasattr(event, "position") else event.pos()


def _asset_path_from_mime(event: Any) -> str:
    mime = event.mimeData()
    if mime.hasFormat(_ASSET_MIME):
        return bytes(mime.data(_ASSET_MIME)).decode("utf-8")
    return mime.text().strip() if mime.hasText() else ""


def _asset_path_from_item(item: QTreeWidgetItem | None) -> str:
    if item is None:
        return ""
    asset = item.data(0, Qt.UserRole)
    if asset is not None:
        return str(getattr(asset, "path", "") or "")
    return str(item.data(0, Qt.UserRole + 1) or "")


def _is_image(path: str) -> bool:
    return Path(path).suffix.lower() in _IMAGE_EXTENSIONS


def _is_script(path: str) -> bool:
    return Path(path).suffix.lower() in _SCRIPT_EXTENSIONS


def _is_supported(path: str) -> bool:
    return _is_image(path) or _is_script(path)


# ---------------------------------------------------------------------------
# Resolucao de componentes
# ---------------------------------------------------------------------------

def _get_or_create_image_component(obj: Any) -> Any | None:
    try:
        from engine.ui.runtime_components import ImageComponent
    except ImportError:
        return None
    comp = obj.get_component(ImageComponent) if hasattr(obj, "get_component") else None
    if comp is None and hasattr(obj, "add_component"):
        comp = obj.add_component(ImageComponent())
    return comp


def _get_or_create_script_component(obj: Any) -> Any | None:
    try:
        from engine.core.component_registry import component_registry
        cls = component_registry.resolve("Script") or component_registry.resolve("ScriptComponent")
    except Exception:
        cls = None
    if cls is None:
        return None
    comp = obj.get_component(cls) if hasattr(obj, "get_component") else None
    if comp is None and hasattr(obj, "add_component"):
        comp = obj.add_component(cls())
    return comp


# ---------------------------------------------------------------------------
# Aplicacao de asset com suporte a undo/redo
# ---------------------------------------------------------------------------

def _apply_asset_with_undo(editor: Any, obj: Any, asset_path: str) -> bool:
    """Aplica um asset ao objeto passando pelo CommandManager.

    O undo restaura o valor anterior do campo (sprite_path ou script_path).
    """
    if obj is None or not _is_supported(asset_path):
        return False

    commands = getattr(getattr(editor, "editor_context", None), "commands", None)

    def _refresh_after() -> None:
        try:
            editor.select_object(obj)
        except Exception:
            pass
        try:
            editor.inspector.load_object(obj)
        except Exception:
            pass
        for name in ("viewport", "game_viewport"):
            vp = getattr(editor, name, None)
            if vp is not None:
                try:
                    vp.update()
                except Exception:
                    pass

    if _is_image(asset_path):
        comp = _get_or_create_image_component(obj)
        if comp is None:
            return False
        old_path = getattr(comp, "sprite_path", "")
        old_visible = getattr(comp, "visible", True)

        def do() -> None:
            comp.sprite_path = asset_path
            comp.visible = True
            _refresh_after()

        def undo_fn() -> None:
            comp.sprite_path = old_path
            comp.visible = old_visible
            _refresh_after()

        desc = f"Sprite: {Path(asset_path).name} -> {getattr(obj, 'name', str(obj))}"

    elif _is_script(asset_path):
        comp = _get_or_create_script_component(obj)
        if comp is None:
            return False
        script_attr = next((a for a in ("script_path", "path", "file_path") if hasattr(comp, a)), None)
        old_val = getattr(comp, script_attr, "") if script_attr else ""

        def do() -> None:
            if script_attr:
                setattr(comp, script_attr, asset_path)
            _refresh_after()

        def undo_fn() -> None:
            if script_attr:
                setattr(comp, script_attr, old_val)
            _refresh_after()

        desc = f"Script: {Path(asset_path).name} -> {getattr(obj, 'name', str(obj))}"

    else:
        return False

    if commands is not None:
        from editor.runtime.command_manager import FunctionCommand
        cmd = FunctionCommand(description=desc, do=do, undo_action=undo_fn)
        commands.execute(cmd)
    else:
        # Fallback sem undo se CommandManager nao estiver disponivel
        do()

    if hasattr(editor, "status_msg"):
        editor.status_msg.setText(f"Asset aplicado: {Path(asset_path).name}")
    return True


# ---------------------------------------------------------------------------
# Resolucao do objeto alvo do drop
# ---------------------------------------------------------------------------

def _target_from_viewport_pos(editor: Any, event: Any) -> Any | None:
    try:
        pos = _event_pos(event)
        return editor.viewport._object_at_viewport_point(float(pos.x()), float(pos.y()))
    except Exception:
        return None


def _target_selected(editor: Any) -> Any | None:
    try:
        return editor.editor_context.selection.selected
    except Exception:
        pass
    try:
        scene = editor.viewport.active_scene
        objects = list(getattr(scene, "editable_objects", []))
        idx = int(getattr(scene, "selected_index", -1))
        if 0 <= idx < len(objects):
            return objects[idx]
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Event filters
# ---------------------------------------------------------------------------

class _AssetDragFilter(QObject):
    """Inicia um QDrag quando o usuario arrasta um item da arvore de assets."""

    def __init__(self, panel: Any) -> None:
        super().__init__(panel)
        self.panel = panel
        self._start_pos = None

    def eventFilter(self, obj: Any, event: Any) -> bool:
        tree = getattr(self.panel, "tree", None)
        if tree is None:
            return False

        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self._start_pos = _event_pos(event)
            return False

        if event.type() == QEvent.MouseButtonRelease:
            self._start_pos = None
            return False

        if (
            event.type() == QEvent.MouseMove
            and self._start_pos is not None
            and event.buttons() & Qt.LeftButton
        ):
            pos = _event_pos(event)
            if (pos - self._start_pos).manhattanLength() < 8:
                return False
            item = tree.itemAt(self._start_pos)
            path = _asset_path_from_item(item)
            if not path or item is None:
                return False
            mime = QMimeData()
            mime.setData(_ASSET_MIME, path.encode("utf-8"))
            mime.setText(path)
            drag = QDrag(tree)
            drag.setMimeData(mime)
            self._start_pos = None
            drag.exec(Qt.CopyAction)
            return True
        return False


class _AssetDropFilter(QObject):
    """Aceita drops de assets e aplica ao objeto alvo com suporte a undo."""

    def __init__(self, editor: Any, use_cursor_object: bool = False) -> None:
        super().__init__(editor)
        self.editor = editor
        self.use_cursor_object = use_cursor_object
        self._hovered_widget: QWidget | None = None

    def _get_target(self, event: Any) -> Any | None:
        if self.use_cursor_object:
            obj = _target_from_viewport_pos(self.editor, event)
            if obj is not None:
                return obj
        return _target_selected(self.editor)

    def _set_hover(self, widget: QWidget | None, active: bool) -> None:
        if widget is None:
            return
        try:
            widget.setStyleSheet(_HOVER_STYLE_VALID if active else _HOVER_STYLE_RESET)
        except Exception:
            pass

    def eventFilter(self, obj: Any, event: Any) -> bool:
        if event.type() in (QEvent.DragEnter, QEvent.DragMove):
            path = _asset_path_from_mime(event)
            if _is_supported(path):
                event.acceptProposedAction()
                if isinstance(obj, QWidget):
                    self._hovered_widget = obj
                    self._set_hover(obj, True)
                return True
            return False

        if event.type() == QEvent.DragLeave:
            self._set_hover(self._hovered_widget, False)
            self._hovered_widget = None
            return False

        if event.type() == QEvent.Drop:
            self._set_hover(self._hovered_widget, False)
            self._hovered_widget = None
            path = _asset_path_from_mime(event)
            target = self._get_target(event)
            if _apply_asset_with_undo(self.editor, target, path):
                event.acceptProposedAction()
                return True
        return False


# ---------------------------------------------------------------------------
# Instalacao
# ---------------------------------------------------------------------------

def _install_drop_on(widget: QWidget, drop_filter: _AssetDropFilter) -> None:
    widget.setAcceptDrops(True)
    widget.installEventFilter(drop_filter)
    # Tambem instala no viewport interno (OpenGL/scroll area)
    vp_fn = getattr(widget, "viewport", None)
    if callable(vp_fn):
        child = vp_fn()
        if child is not None:
            child.setAcceptDrops(True)
            child.installEventFilter(drop_filter)
    for child in widget.findChildren(QWidget):
        child.setAcceptDrops(True)
        child.installEventFilter(drop_filter)


def apply_asset_drag_drop_patch(editor: Any) -> bool:
    resources = getattr(editor, "resources", None)
    viewport = getattr(editor, "viewport", None)
    inspector = getattr(editor, "inspector", None)
    if not all((resources, viewport, inspector)):
        return False
    if getattr(editor, "_zennity_asset_drag_drop_v2_applied", False):
        return True
    editor._zennity_asset_drag_drop_v2_applied = True

    # --- Drag na arvore de assets ---
    tree = getattr(resources, "tree", None)
    if tree is not None:
        tree.setDragEnabled(True)
        tree.setAcceptDrops(False)
        tree.setDragDropMode(QAbstractItemView.DragOnly)
        tree.setDefaultDropAction(Qt.CopyAction)
        drag_filter = _AssetDragFilter(resources)
        tree.installEventFilter(drag_filter)
        vp = getattr(tree, "viewport", None)
        if callable(vp) and vp() is not None:
            vp().installEventFilter(drag_filter)
        editor._zennity_asset_drag_filter = drag_filter

    # --- Drop na viewport (usa objeto sob o cursor) ---
    vp_drop = _AssetDropFilter(editor, use_cursor_object=True)
    _install_drop_on(viewport, vp_drop)
    editor._zennity_asset_drop_viewport = vp_drop

    # --- Drop no inspector (usa objeto selecionado) ---
    insp_drop = _AssetDropFilter(editor, use_cursor_object=False)
    _install_drop_on(inspector, insp_drop)
    editor._zennity_asset_drop_inspector = insp_drop

    if hasattr(editor, "status_msg"):
        editor.status_msg.setText("Drag/drop de Assets ativado")
    return True


def _scan_and_apply() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    applied = False
    for widget in app.topLevelWidgets():
        if all(hasattr(widget, attr) for attr in ("resources", "viewport", "inspector")):
            applied = apply_asset_drag_drop_patch(widget) or applied
    return applied


def install_asset_drag_drop_runtime_watch() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    for delay in (0, 200, 600, 1200):
        QTimer.singleShot(delay, _scan_and_apply)
    return True


def patch_phase1_editor_asset_drag_drop() -> bool:
    install_asset_drag_drop_runtime_watch()
    try:
        from editor.phase1_editor import ZennityPhase1Editor
    except Exception:
        return False
    if getattr(ZennityPhase1Editor, "_zennity_asset_drag_drop_v2_class_patched", False):
        return True
    original_connect = ZennityPhase1Editor._connect

    def connect(self) -> None:
        original_connect(self)
        apply_asset_drag_drop_patch(self)

    ZennityPhase1Editor._connect = connect
    ZennityPhase1Editor._zennity_asset_drag_drop_v2_class_patched = True
    return True
