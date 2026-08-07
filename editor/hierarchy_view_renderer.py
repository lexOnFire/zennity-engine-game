"""Incremental hierarchy rendering for the official editor."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidgetItem


class HierarchyViewRenderer:
    """Rebuild the hierarchy only when its visible structure changes."""

    def __init__(self, editor: Any) -> None:
        self.editor = editor
        self._last_signature: tuple[Any, ...] | None = None
        self.rebuild_count = 0
        self.skipped_count = 0

    def refresh(self, *, force: bool = False) -> bool:
        signature = self._signature()
        if not force and signature == self._last_signature:
            self.skipped_count += 1
            return False
        self._last_signature = signature
        self.rebuild_count += 1
        self._rebuild()
        return True

    def invalidate(self) -> None:
        self._last_signature = None

    def _signature(self) -> tuple[Any, ...]:
        editor = self.editor
        scene_name = editor._scene_document.get("scene_name", "MainScene") if editor._scene_document else "MainScene"
        permanent = tuple(
            (str(obj.get("id", "")), str(obj.get("name", "")), bool(obj.get("editor_locked", False)))
            for obj in editor._scene_snapshot
        )
        spawned = tuple(sorted(
            (str(obj.get("id", name)), str(obj.get("name", name)))
            for name, obj in editor._runtime_objects_by_name.items()
            if obj.get("spawned_by_logic", False) and name not in editor._objects_by_name
        )) if editor._runtime_playing else ()
        return str(scene_name), permanent, spawned, str(editor._selected_name or "")

    def _rebuild(self) -> None:
        editor = self.editor
        tree = editor.hierarchy_tree
        tree.setUpdatesEnabled(False)
        try:
            tree.clear()
            scene_name = editor._scene_document.get("scene_name", "MainScene") if editor._scene_document else "MainScene"
            root = QTreeWidgetItem(["🟢 " + str(scene_name)])
            root.setExpanded(True)
            selected_items = []
            selected_names = set(getattr(editor, "_selected_names", [editor._selected_name] if editor._selected_name else []))

            def _add_object_nodes(parent_item: QTreeWidgetItem, objects: list[dict[str, Any]]) -> None:
                for obj in objects:
                    name = str(obj["name"])
                    lock_icon = "🔒 " if obj.get("editor_locked", False) else ""
                    is_group = bool(obj.get("is_group", False))
                    prefix = "📂 " if is_group else self._icon(name)
                    item = QTreeWidgetItem([lock_icon + prefix + name])
                    item.setData(0, Qt.UserRole, name)
                    if obj.get("editor_locked", False):
                        item.setToolTip(0, "Transformação bloqueada")
                    parent_item.addChild(item)
                    if name in selected_names:
                        selected_items.append(item)
                    children = obj.get("children", [])
                    if children:
                        _add_object_nodes(item, children)
                        item.setExpanded(True)

            root_objects = [obj for obj in editor._scene_snapshot if not obj.get("parent")]
            _add_object_nodes(root, root_objects if root_objects else editor._scene_snapshot)
            spawned = [
                obj for name, obj in editor._runtime_objects_by_name.items()
                if obj.get("spawned_by_logic", False) and name not in editor._objects_by_name
            ]
            if editor._runtime_playing and spawned:
                runtime_root = QTreeWidgetItem([f"▶ Runtime ({len(spawned)})"])
                runtime_root.setData(0, Qt.UserRole + 1, "runtime-group")
                runtime_root.setExpanded(True)
                for obj in sorted(spawned, key=lambda value: str(value.get("name", ""))):
                    name = str(obj.get("name", "RuntimeObject"))
                    item = QTreeWidgetItem(["⚡ " + name])
                    item.setData(0, Qt.UserRole, name)
                    item.setData(0, Qt.UserRole + 1, "runtime-object")
                    item.setToolTip(0, "Instância temporária criada durante o Play Mode")
                    runtime_root.addChild(item)
                    if name == editor._selected_name:
                        selected_item = item
                root.addChild(runtime_root)
            tree.addTopLevelItem(root)
            if selected_items:
                tree.blockSignals(True)
                try:
                    for item in selected_items:
                        item.setSelected(True)
                    if selected_items:
                        tree.setCurrentItem(selected_items[-1])
                finally:
                    tree.blockSignals(False)
        finally:
            tree.setUpdatesEnabled(True)

    @staticmethod
    def item_name(item: QTreeWidgetItem | None) -> str:
        if item is None:
            return ""
        stored_name = item.data(0, Qt.UserRole)
        if stored_name:
            return str(stored_name)
        return item.text(0).lstrip("🟢🔴🟡🔵🟣⚫⚪📁🏔️☀️☁️📷🔶💡👤📦 ").strip()

    @staticmethod
    def _icon(name: str) -> str:
        lowered = name.lower()
        if "player" in lowered:
            return "👤 "
        if "chao" in lowered or "floor" in lowered:
            return "🏔️ "
        return "📦 "
