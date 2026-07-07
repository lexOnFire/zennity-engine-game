from __future__ import annotations

"""Drag-and-drop de assets da aba Resources para Viewport e Inspector.

Regra central: toda aplicacao de asset passa pelo CommandManager
(suporte a undo/redo). O patch e instalado UMA unica vez por instancia
do editor chamando apply_asset_drag_drop_patch(editor).
"""

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEvent, QMimeData, QObject, Qt
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import QAbstractItemView, QTreeWidgetItem, QWidget

_ASSET_MIME = "application/x-zennity-asset-path"
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
_SCRIPT_EXTENSIONS = {".py"}
_HOVER_STYLE_VALID = "border: 2px solid #4f98a3;"
_HOVER_STYLE_RESET = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _event_pos(event: Any):
    return event.position().toPoint() if hasattr(event, "position") else event.pos()


def _asset_path_from_mime(event: Any) -> str:
    mime = event.mimeData()
    if mime.hasFormat(_ASSET_MIME):
        return bytes(mime.data(_ASSET_MIME)).decode("utf-8")
    return mime.text().strip() if mime.hasText() else ""


def _asset_path_from_item(item) -> str:
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
# Aplicacao de asset com undo
# ---------------------------------------------------------------------------

def _apply_asset_with_undo(editor: Any, asset_path: str, target_obj: Any) -> bool:
    """Aplica asset ao target_obj registrando no CommandManager para undo."""
    if target_obj is None or not asset_path:
        return False

    commands = getattr(getattr(editor, "editor_context", None), "commands", None)
    if commands is None:
        return False

    path = asset_path.strip()

    if _is_image(path):
        # Tenta SpriteRenderer, depois Image
        comp = None
        comp_attr = None
        for comp_type_name, attr in (
            ("SpriteRenderer", "sprite_path"),
            ("Image", "source"),
        ):
            try:
                from engine import components as _comps
                comp_type = getattr(_comps, comp_type_name, None)
                if comp_type is None:
                    continue
                found = target_obj.get_component(comp_type)
                if found is not None:
                    comp = found
                    comp_attr = attr
                    break
            except Exception:
                continue

        if comp is None or comp_attr is None:
            return False

        old_val = getattr(comp, comp_attr, None)
        new_val = path

        def do_apply():
            setattr(comp, comp_attr, new_val)
            _post_apply(editor, target_obj)

        def do_undo():
            setattr(comp, comp_attr, old_val)
            _post_apply(editor, target_obj)

        from editor.runtime.command_manager import FunctionCommand
        commands.execute(FunctionCommand(
            f"Aplicar sprite '{Path(path).name}' em {target_obj.name}",
            do_apply,
            do_undo,
        ))
        return True

    if _is_script(path):
        comp = None
        comp_attr = None
        try:
            from engine import components as _comps
            script_type = getattr(_comps, "ScriptComponent", None) or getattr(_comps, "Script", None)
            if script_type is not None:
                found = target_obj.get_component(script_type)
                if found is not None:
                    comp = found
                    comp_attr = "script_path"
        except Exception:
            pass

        if comp is None:
            # fallback: tenta atributo generico no objeto
            if hasattr(target_obj, "script_path"):
                old_val = target_obj.script_path

                def do_apply_obj():
                    target_obj.script_path = path
                    _post_apply(editor, target_obj)

                def do_undo_obj():
                    target_obj.script_path = old_val
                    _post_apply(editor, target_obj)

                from editor.runtime.command_manager import FunctionCommand
                commands.execute(FunctionCommand(
                    f"Aplicar script '{Path(path).name}' em {target_obj.name}",
                    do_apply_obj,
                    do_undo_obj,
                ))
                return True
            return False

        old_val = getattr(comp, comp_attr, None)

        def do_apply_comp():
            setattr(comp, comp_attr, path)
            _post_apply(editor, target_obj)

        def do_undo_comp():
            setattr(comp, comp_attr, old_val)
            _post_apply(editor, target_obj)

        from editor.runtime.command_manager import FunctionCommand
        commands.execute(FunctionCommand(
            f"Aplicar script '{Path(path).name}' em {target_obj.name}",
            do_apply_comp,
            do_undo_comp,
        ))
        return True

    return False


def _post_apply(editor: Any, obj: Any) -> None:
    """Refresh de Inspector e Viewport apos aplicar um asset."""
    try:
        editor.inspector.load_object(obj)
    except Exception:
        pass
    try:
        viewport = getattr(editor, "viewport", None)
        if viewport is not None:
            viewport.update()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Filtro de drag (origem: ResourcesPanel / PrefabsPanel)
# ---------------------------------------------------------------------------

class _AssetDragFilter(QObject):
    """Instala drag no widget de assets (QTreeWidget da aba Resources)."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._drag_start_item = None

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                if hasattr(watched, "itemAt"):
                    self._drag_start_item = watched.itemAt(_event_pos(event))
        elif event.type() == QEvent.MouseMove:
            if event.buttons() & Qt.LeftButton and self._drag_start_item is not None:
                path = _asset_path_from_item(self._drag_start_item)
                if path and _is_supported(path):
                    self._start_drag(path)
                    self._drag_start_item = None
                    return True
        elif event.type() == QEvent.MouseButtonRelease:
            self._drag_start_item = None
        return False

    def _start_drag(self, asset_path: str) -> None:
        mime = QMimeData()
        mime.setData(_ASSET_MIME, asset_path.encode("utf-8"))
        mime.setText(asset_path)
        drag = QDrag(self.parent())
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


# ---------------------------------------------------------------------------
# Filtro de drop (destino: Viewport)
# ---------------------------------------------------------------------------

class _ViewportDropFilter(QObject):
    """Aceita drop de assets na Viewport, aplicando no objeto sob o cursor."""

    def __init__(self, editor: Any, viewport: QWidget) -> None:
        super().__init__(viewport)
        self._editor = editor
        self._viewport = viewport
        viewport.setAcceptDrops(True)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.DragEnter:
            if event.mimeData().hasFormat(_ASSET_MIME) or event.mimeData().hasText():
                event.acceptProposedAction()
                watched.setStyleSheet(_HOVER_STYLE_VALID)
                return True
        elif event.type() == QEvent.DragLeave:
            watched.setStyleSheet(_HOVER_STYLE_RESET)
        elif event.type() == QEvent.Drop:
            watched.setStyleSheet(_HOVER_STYLE_RESET)
            path = _asset_path_from_mime(event)
            if path and _is_supported(path):
                obj = self._object_at(event)
                if obj is not None:
                    _apply_asset_with_undo(self._editor, path, obj)
                    event.acceptProposedAction()
                    return True
        return False

    def _object_at(self, event: Any) -> Any:
        """Retorna o GameObject sob o cursor na viewport."""
        pos = _event_pos(event)
        scene = getattr(self._viewport, "active_scene", None)
        if scene is None:
            return None
        # Usa hit-test da viewport se disponivel
        if hasattr(self._viewport, "_object_at_screen"):
            return self._viewport._object_at_screen(pos.x(), pos.y())
        # Fallback: objeto selecionado no editor
        try:
            return self._editor.editor_context.selection.selected
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Filtro de drop (destino: Inspector)
# ---------------------------------------------------------------------------

class _InspectorDropFilter(QObject):
    """Aceita drop de assets no Inspector, aplicando no objeto selecionado."""

    def __init__(self, editor: Any, inspector: QWidget) -> None:
        super().__init__(inspector)
        self._editor = editor
        self._inspector = inspector
        inspector.setAcceptDrops(True)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.DragEnter:
            if event.mimeData().hasFormat(_ASSET_MIME) or event.mimeData().hasText():
                event.acceptProposedAction()
                watched.setStyleSheet(_HOVER_STYLE_VALID)
                return True
        elif event.type() == QEvent.DragLeave:
            watched.setStyleSheet(_HOVER_STYLE_RESET)
        elif event.type() == QEvent.Drop:
            watched.setStyleSheet(_HOVER_STYLE_RESET)
            path = _asset_path_from_mime(event)
            if path and _is_supported(path):
                try:
                    obj = self._editor.editor_context.selection.selected
                except Exception:
                    obj = None
                if obj is not None:
                    _apply_asset_with_undo(self._editor, path, obj)
                    event.acceptProposedAction()
                    return True
        return False


# ---------------------------------------------------------------------------
# Ponto de entrada publico
# ---------------------------------------------------------------------------

def apply_asset_drag_drop_patch(editor: Any) -> None:
    """Instala drag-and-drop de assets no editor.

    Deve ser chamado UMA vez apos a UI estar completamente montada,
    tipicamente no final de ZennityPhase1Editor._connect().
    """
    if getattr(editor, "_zennity_asset_drag_drop_applied", False):
        return
    editor._zennity_asset_drag_drop_applied = True

    # --- Filtros de drag nos paineis de assets ---
    resources = getattr(editor, "resources", None)
    if resources is not None:
        tree = getattr(resources, "tree", None) or getattr(resources, "file_tree", None)
        if tree is None:
            # Tenta encontrar o primeiro QTreeWidget filho
            from PySide6.QtWidgets import QTreeWidget
            tree = resources.findChild(QTreeWidget)
        if tree is not None:
            drag_filter = _AssetDragFilter(tree)
            tree.installEventFilter(drag_filter)
            if hasattr(tree, "setDragEnabled"):
                tree.setDragEnabled(True)
            editor._asset_drag_filter_resources = drag_filter

    prefabs = getattr(editor, "prefabs", None)
    if prefabs is not None:
        tree = getattr(prefabs, "tree", None) or getattr(prefabs, "file_tree", None)
        if tree is None:
            from PySide6.QtWidgets import QTreeWidget
            tree = prefabs.findChild(QTreeWidget)
        if tree is not None:
            drag_filter_p = _AssetDragFilter(tree)
            tree.installEventFilter(drag_filter_p)
            if hasattr(tree, "setDragEnabled"):
                tree.setDragEnabled(True)
            editor._asset_drag_filter_prefabs = drag_filter_p

    # --- Filtro de drop na Viewport ---
    viewport = getattr(editor, "viewport", None)
    if viewport is not None:
        vp_filter = _ViewportDropFilter(editor, viewport)
        viewport.installEventFilter(vp_filter)
        editor._asset_drop_filter_viewport = vp_filter

    # --- Filtro de drop no Inspector ---
    inspector = getattr(editor, "inspector", None)
    if inspector is not None:
        insp_filter = _InspectorDropFilter(editor, inspector)
        inspector.installEventFilter(insp_filter)
        editor._asset_drop_filter_inspector = insp_filter
