from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QMimeData, QObject, QTimer, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QApplication, QAbstractItemView, QTreeWidgetItem, QWidget


_ASSET_MIME = "application/x-zennity-asset-path"
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_SCRIPT_EXTENSIONS = {".py"}


def _event_pos(event: Any):
    return event.position().toPoint() if hasattr(event, "position") else event.pos()


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


def _get_or_add_image_component(obj: Any):
    from engine.ui.runtime_components import ImageComponent
    image = obj.get_component(ImageComponent) if hasattr(obj, "get_component") else None
    if image is None and hasattr(obj, "add_component"):
        image = obj.add_component(ImageComponent())
    return image


def _get_or_add_script_component(obj: Any):
    try:
        from engine.core.component_registry import component_registry
        script_cls = component_registry.resolve("Script") or component_registry.resolve("ScriptComponent")
    except Exception:
        script_cls = None
    if script_cls is None:
        return None
    script = obj.get_component(script_cls) if hasattr(obj, "get_component") else None
    if script is None and hasattr(obj, "add_component"):
        script = obj.add_component(script_cls())
    return script


def _apply_asset_to_object(editor: Any, obj: Any, asset_path: str) -> bool:
    if obj is None or not asset_path:
        return False
    if _is_image(asset_path):
        image = _get_or_add_image_component(obj)
        if image is None:
            return False
        image.sprite_path = asset_path
        image.visible = True
        if hasattr(editor, "select_object"):
            editor.select_object(obj)
        if hasattr(editor, "inspector"):
            editor.inspector.load_object(obj)
        for attr in ("viewport", "game_viewport"):
            viewport = getattr(editor, attr, None)
            if viewport is not None:
                try:
                    viewport.update()
                    viewport.repaint()
                except Exception:
                    pass
        if hasattr(editor, "status_msg"):
            editor.status_msg.setText(f"Asset aplicado: {asset_path}")
        return True
    if _is_script(asset_path):
        script = _get_or_add_script_component(obj)
        if script is None:
            return False
        for attr in ("script_path", "path", "file_path"):
            if hasattr(script, attr):
                setattr(script, attr, asset_path)
                break
        if hasattr(editor, "select_object"):
            editor.select_object(obj)
        if hasattr(editor, "inspector"):
            editor.inspector.load_object(obj)
        if hasattr(editor, "status_msg"):
            editor.status_msg.setText(f"Script aplicado: {asset_path}")
        return True
    return False


class _AssetDragFilter(QObject):
    def __init__(self, panel: Any) -> None:
        super().__init__(panel)
        self.panel = panel
        self.start_pos = None

    def eventFilter(self, obj, event) -> bool:
        tree = getattr(self.panel, "tree", None)
        if tree is None:
            return False
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.start_pos = _event_pos(event)
            return False
        if event.type() == QEvent.MouseButtonRelease:
            self.start_pos = None
            return False
        if event.type() == QEvent.MouseMove and self.start_pos is not None and event.buttons() & Qt.LeftButton:
            current_pos = _event_pos(event)
            if (current_pos - self.start_pos).manhattanLength() < 6:
                return False
            item = tree.itemAt(self.start_pos)
            path = _asset_path_from_item(item)
            asset = item.data(0, Qt.UserRole) if item is not None else None
            if not path or asset is None:
                return False
            mime = QMimeData()
            mime.setData(_ASSET_MIME, path.encode("utf-8"))
            mime.setText(path)
            drag = QDrag(tree)
            drag.setMimeData(mime)
            drag.exec(Qt.CopyAction)
            self.start_pos = None
            return True
        return False


class _AssetDropFilter(QObject):
    def __init__(self, editor: Any, target: str) -> None:
        super().__init__(editor)
        self.editor = editor
        self.target = target

    def _asset_path(self, event) -> str:
        mime = event.mimeData()
        if mime.hasFormat(_ASSET_MIME):
            return bytes(mime.data(_ASSET_MIME)).decode("utf-8")
        return mime.text().strip() if mime.hasText() else ""

    def _target_object(self, event) -> Any:
        if self.target == "viewport":
            viewport = getattr(self.editor, "viewport", None)
            if viewport is not None:
                try:
                    pos = _event_pos(event)
                    obj = viewport._object_at_viewport_point(float(pos.x()), float(pos.y()))
                    if obj is not None:
                        return obj
                except Exception:
                    pass
        context = getattr(self.editor, "editor_context", None)
        selection = getattr(context, "selection", None)
        selected = getattr(selection, "selected", None)
        if selected is not None:
            return selected
        viewport = getattr(self.editor, "viewport", None)
        scene = getattr(viewport, "active_scene", None)
        objects = list(getattr(scene, "editable_objects", [])) if scene is not None else []
        idx = int(getattr(scene, "selected_index", -1)) if scene is not None else -1
        if 0 <= idx < len(objects):
            return objects[idx]
        return None

    def eventFilter(self, obj, event) -> bool:
        if event.type() in (QEvent.DragEnter, QEvent.DragMove):
            path = self._asset_path(event)
            if _is_image(path) or _is_script(path):
                event.acceptProposedAction()
                return True
        if event.type() == QEvent.Drop:
            path = self._asset_path(event)
            target = self._target_object(event)
            if _apply_asset_to_object(self.editor, target, path):
                event.acceptProposedAction()
                return True
        return False


def _enable_asset_rename(panel: Any) -> None:
    tree = getattr(panel, "tree", None)
    if tree is None or getattr(panel, "_zennity_asset_rename_enabled", False):
        return
    panel._zennity_asset_rename_enabled = True
    tree.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)

    def mark_editable(item: QTreeWidgetItem | None) -> None:
        if item is None:
            return
        item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled)
        for i in range(item.childCount()):
            mark_editable(item.child(i))

    def refresh_flags() -> None:
        mark_editable(tree.topLevelItem(0))

    original_refresh = panel.refresh_assets

    def refresh_assets() -> None:
        original_refresh()
        refresh_flags()

    def begin_rename(item: QTreeWidgetItem, column: int) -> None:
        if item is None or item.parent() is None:
            return
        tree.editItem(item, 0)

    def finish_rename(item: QTreeWidgetItem, column: int) -> None:
        if column != 0 or item is None or item.parent() is None:
            return
        old_path = str(item.data(0, Qt.UserRole + 1) or "")
        asset = item.data(0, Qt.UserRole)
        if not old_path:
            old_path = str(getattr(asset, "path", "") or "")
        new_name = item.text(0).strip()
        if not old_path or not new_name or new_name == Path(old_path).name:
            return
        try:
            panel.rename_path(old_path, new_name)
        except Exception:
            refresh_assets()

    panel.refresh_assets = refresh_assets
    tree.itemDoubleClicked.connect(begin_rename)
    tree.itemChanged.connect(finish_rename)
    refresh_flags()


def _install_filter_on_widget(widget: QWidget, drop_filter: QObject) -> None:
    widget.setAcceptDrops(True)
    widget.installEventFilter(drop_filter)
    viewport = getattr(widget, "viewport", None)
    if callable(viewport):
        child = viewport()
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
    if resources is None or viewport is None or inspector is None:
        return False
    if getattr(editor, "_zennity_asset_drag_drop_patch_applied", False):
        return True
    editor._zennity_asset_drag_drop_patch_applied = True

    tree = getattr(resources, "tree", None)
    if tree is not None:
        tree.setDragEnabled(True)
        tree.setAcceptDrops(False)
        tree.setDragDropMode(QAbstractItemView.DragOnly)
        tree.setDefaultDropAction(Qt.CopyAction)
        drag_filter = _AssetDragFilter(resources)
        tree.installEventFilter(drag_filter)
        tree.viewport().installEventFilter(drag_filter)
        resources._zennity_asset_drag_filter = drag_filter
    _enable_asset_rename(resources)

    for widget, name in ((viewport, "viewport"), (inspector, "inspector")):
        drop_filter = _AssetDropFilter(editor, name)
        _install_filter_on_widget(widget, drop_filter)
        setattr(editor, f"_zennity_asset_drop_filter_{name}", drop_filter)
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
    if getattr(ZennityPhase1Editor, "_zennity_asset_drag_drop_class_patched", False):
        return True
    original_connect = ZennityPhase1Editor._connect

    def connect(self) -> None:
        original_connect(self)
        apply_asset_drag_drop_patch(self)

    ZennityPhase1Editor._connect = connect
    ZennityPhase1Editor._zennity_asset_drag_drop_class_patched = True
    return True
