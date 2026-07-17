from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QDrag
from PySide6.QtCore import QMimeData
from PySide6.QtWidgets import QApplication, QAbstractItemView

_ASSET_MIME = "application/x-zennity-asset-path"
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_SCRIPT_EXTENSIONS = {".py"}


def _event_pos(event: Any):
    return event.position().toPoint() if hasattr(event, "position") else event.pos()


def _asset_path(event: Any) -> str:
    mime = event.mimeData()
    if mime.hasFormat(_ASSET_MIME):
        return bytes(mime.data(_ASSET_MIME)).decode("utf-8")
    return mime.text().strip() if mime.hasText() else ""


def _supported(path: str) -> bool:
    return Path(path).suffix.lower() in (_IMAGE_EXTENSIONS | _SCRIPT_EXTENSIONS)


def _selected(editor: Any) -> Any | None:
    try:
        selected = editor.editor_context.selection.selected
        if selected is not None:
            return selected
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


def _object_at(editor: Any, event: Any) -> Any | None:
    try:
        pos = _event_pos(event)
        return editor.viewport._object_at_viewport_point(float(pos.x()), float(pos.y()))
    except Exception:
        return None


def _apply(editor: Any, obj: Any, path: str) -> bool:
    if obj is None or not _supported(path):
        return False
    suffix = Path(path).suffix.lower()
    if suffix in _IMAGE_EXTENSIONS:
        from engine.ui.runtime_components import ImageComponent
        image = obj.get_component(ImageComponent) if hasattr(obj, "get_component") else None
        if image is None and hasattr(obj, "add_component"):
            image = obj.add_component(ImageComponent())
        if image is None:
            return False
        image.sprite_path = path
        image.visible = True
    elif suffix in _SCRIPT_EXTENSIONS:
        try:
            from engine.core.component_registry import component_registry
            cls = component_registry.resolve("Script") or component_registry.resolve("ScriptComponent")
        except Exception:
            cls = None
        if cls is None:
            return False
        comp = obj.get_component(cls) if hasattr(obj, "get_component") else None
        if comp is None and hasattr(obj, "add_component"):
            comp = obj.add_component(cls())
        if comp is None:
            return False
        for attr in ("script_path", "path", "file_path"):
            if hasattr(comp, attr):
                setattr(comp, attr, path)
                break
    else:
        return False

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
                vp.repaint()
            except Exception:
                pass
    if hasattr(editor, "status_msg"):
        editor.status_msg.setText(f"Asset aplicado: {path}")
    return True


def _patch_asset_tree(editor: Any) -> None:
    resources = getattr(editor, "resources", None)
    tree = getattr(resources, "tree", None)
    if tree is None or getattr(tree, "_zennity_direct_drag", False):
        return
    tree._zennity_direct_drag = True
    tree.setDragEnabled(True)
    tree.setAcceptDrops(False)
    tree.setDragDropMode(QAbstractItemView.DragOnly)
    tree.setDefaultDropAction(Qt.CopyAction)
    tree._zennity_drag_start = None
    old_press = tree.mousePressEvent
    old_move = tree.mouseMoveEvent

    def mouse_press(event):
        if event.button() == Qt.LeftButton:
            tree._zennity_drag_start = _event_pos(event)
        old_press(event)

    def mouse_move(event):
        start = getattr(tree, "_zennity_drag_start", None)
        if start is not None and event.buttons() & Qt.LeftButton:
            pos = _event_pos(event)
            if (pos - start).manhattanLength() >= 6:
                item = tree.itemAt(start)
                asset = item.data(0, Qt.UserRole) if item is not None else None
                path = str(getattr(asset, "path", "") or "") if asset is not None else ""
                if path:
                    mime = QMimeData()
                    mime.setData(_ASSET_MIME, path.encode("utf-8"))
                    mime.setText(path)
                    drag = QDrag(tree)
                    drag.setMimeData(mime)
                    tree._zennity_drag_start = None
                    drag.exec(Qt.CopyAction)
                    return
        old_move(event)

    tree.mousePressEvent = mouse_press
    tree.mouseMoveEvent = mouse_move


def _patch_target(editor: Any, widget: Any, use_mouse_object: bool) -> None:
    if widget is None or getattr(widget, "_zennity_direct_asset_drop", False):
        return
    widget._zennity_direct_asset_drop = True
    widget.setAcceptDrops(True)
    old_enter = getattr(widget, "dragEnterEvent", None)
    old_move = getattr(widget, "dragMoveEvent", None)
    old_drop = getattr(widget, "dropEvent", None)

    def drag_enter(event):
        if _supported(_asset_path(event)):
            event.acceptProposedAction()
            return
        if old_enter is not None:
            old_enter(event)

    def drag_move(event):
        if _supported(_asset_path(event)):
            event.acceptProposedAction()
            return
        if old_move is not None:
            old_move(event)

    def drop(event):
        path = _asset_path(event)
        obj = (_object_at(editor, event) if use_mouse_object else None) or _selected(editor)
        if _apply(editor, obj, path):
            event.acceptProposedAction()
            return
        if old_drop is not None:
            old_drop(event)

    widget.dragEnterEvent = drag_enter
    widget.dragMoveEvent = drag_move
    widget.dropEvent = drop


def apply_asset_direct_drop_patch(editor: Any) -> bool:
    if not all(hasattr(editor, a) for a in ("resources", "viewport", "inspector")):
        return False
    _patch_asset_tree(editor)
    _patch_target(editor, getattr(editor, "viewport", None), True)
    _patch_target(editor, getattr(editor, "inspector", None), False)
    if hasattr(editor, "status_msg"):
        editor.status_msg.setText("Drag/drop direto de Assets ativado")
    return True


def _scan() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    ok = False
    for widget in app.topLevelWidgets():
        if all(hasattr(widget, a) for a in ("resources", "viewport", "inspector")):
            ok = apply_asset_direct_drop_patch(widget) or ok
    return ok


def patch_asset_direct_drop_runtime() -> bool:
    try:
        from editor.phase1_editor import ZennityPhase1Editor
    except Exception:
        ZennityPhase1Editor = None
    if ZennityPhase1Editor is not None and not getattr(ZennityPhase1Editor, "_zennity_direct_asset_drop_class_patched", False):
        original_connect = ZennityPhase1Editor._connect

        def connect(self):
            original_connect(self)
            apply_asset_direct_drop_patch(self)

        ZennityPhase1Editor._connect = connect
        ZennityPhase1Editor._zennity_direct_asset_drop_class_patched = True
    app = QApplication.instance()
    if app is not None:
        for delay in (0, 200, 600, 1200, 2400):
            QTimer.singleShot(delay, _scan)
    return True
