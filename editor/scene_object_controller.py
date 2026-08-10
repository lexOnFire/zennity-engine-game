"""Mutable scene-object operations for the isolated editor."""
from __future__ import annotations

import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QInputDialog


class SceneObjectController:
    """Owns object creation, naming, duplication, deletion and rename state changes."""

    PRESETS = {
        "Empty": ("GameObject", 40.0, 40.0, (160, 164, 174), None),
        "Sprite": ("Sprite", 64.0, 64.0, (180, 180, 190), None),
        "Player": ("Player", 36.0, 48.0, (88, 117, 255), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
        "Platform": ("Platform", 160.0, 32.0, (91, 194, 100), {"is_kinematic": True, "use_gravity": False}),
        "Enemy": ("Enemy", 40.0, 40.0, (220, 88, 88), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
        "Trigger": ("Trigger", 80.0, 80.0, (222, 178, 72), {"is_kinematic": True, "use_gravity": False}),
        "Camera": ("Camera2D", 96.0, 54.0, (110, 190, 210), None),
    }

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()

    def new_scene(self) -> None:
        h = self.host
        h._scene_history.clear()
        h._scene_snapshot = []
        h._objects_by_name = {}
        h._runtime_objects_by_name.clear()
        h._runtime_animator_states.clear()
        h._scene_document = {
            "format_version": 2,
            "scene_name": "Untitled",
            "engine_version": "Zennity 1.0.1",
            "blackboard": {"variables": {}},
            "objects": [],
        }
        h._current_scene_path = None
        h._selected_name = None
        h._drag_history_snapshot = None
        h._clear_inspector_view()
        h.logic_workspace.clear_runtime_trace()
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot([])
        dock = getattr(h, "_dock_visual_scripting", None)
        if dock is not None and hasattr(dock, "sync_from_host"):
            dock.sync_from_host()
        h._autosave.schedule()
        h.statusBar().showMessage("Nova cena criada")
        h._log("INFO", "Nova cena limpa criada, sem objetos ou vínculos anteriores")

    def unique_name(self, base: str) -> str:
        if base not in self.host._objects_by_name:
            return base
        index = 2
        while f"{base}_{index}" in self.host._objects_by_name:
            index += 1
        return f"{base}_{index}"

    def create(self, kind: str) -> None:
        h = self.host
        if h._play_session.is_running or kind not in self.PRESETS:
            return
        width, height = h.native_viewport_size()
        self.create_at(kind, width / 2.0, height / 2.0)

    def create_at(self, kind: str, screen_x: float, screen_y: float) -> None:
        h = self.host
        h._record_history()
        h._commands.put({
            "type": "create_object_at", "kind": kind,
            "screen_x": screen_x, "screen_y": screen_y,
        })

    def create_sprite_at(self, texture_path: Path, screen_x: float, screen_y: float) -> None:
        h = self.host
        resolved = texture_path.resolve()
        try:
            relative = resolved.relative_to(self.project_root).as_posix()
        except ValueError:
            relative = str(resolved)
        pixmap = QPixmap(str(texture_path))
        width = float(pixmap.width()) if not pixmap.isNull() else 64.0
        height = float(pixmap.height()) if not pixmap.isNull() else 64.0
        h._record_history()
        h._commands.put({
            "type": "create_sprite_at", "texture": relative,
            "screen_x": screen_x, "screen_y": screen_y,
            "width": max(1.0, width), "height": max(1.0, height),
        })

    def reset_to_initial(self) -> None:
        h = self.host
        h._record_history()
        h._scene_snapshot = deepcopy(h._initial_scene_snapshot)
        h._objects_by_name = {item["name"]: item for item in h._scene_snapshot}
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        if h._selected_name in h._objects_by_name:
            h._update_inspector(h._selected_name)

    def rename(self, old_name: str) -> None:
        h = self.host
        if h._play_session.is_running or old_name not in h._objects_by_name:
            return
        new_name, accepted = QInputDialog.getText(
            h, "Renomear objeto", "Nome:", text=old_name
        )
        new_name = new_name.strip()
        if not accepted or not new_name or (
            new_name != old_name and new_name in h._objects_by_name
        ):
            return
        if new_name == old_name:
            return
        try:
            changed_graphs = h._logic_workspace_controller.rename_object_references(
                old_name, new_name
            )
        except (OSError, ValueError) as exc:
            h.statusBar().showMessage(f"Renomeação cancelada: {exc}")
            h._log("ERROR", f"Falha ao atualizar Logic Graphs: {exc}")
            return
        h._record_history()
        obj = h._objects_by_name.pop(old_name)
        obj["name"] = new_name
        h._objects_by_name[new_name] = obj
        if h._selected_name == old_name:
            h._selected_name = new_name
        self._publish_selected(new_name)
        h._log(
            "INFO",
            f"Objeto renomeado: {old_name} → {new_name}; "
            f"{len(changed_graphs)} Logic Graph(s) atualizado(s)",
        )

    def delete(self, name: str) -> None:
        h = self.host
        if h._play_session.is_running:
            h.statusBar().showMessage("Não é possível deletar durante o Play Mode.")
            return
        if name not in h._objects_by_name:
            h.statusBar().showMessage(f"Objeto '{name}' não encontrado para deletar.")
            return
        h._record_history()
        h._scene_snapshot = [obj for obj in h._scene_snapshot if obj["name"] != name]
        h._objects_by_name.pop(name, None)
        if h._selected_name == name:
            h._selected_name = None
            h._clear_inspector_view()
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def set_transform_locked(self, name: str, locked: bool) -> None:
        """Prevent accidental viewport transforms while keeping the object selectable."""
        h = self.host
        obj = h._objects_by_name.get(name)
        if h._play_session.is_running or obj is None:
            return
        next_value = bool(locked)
        if bool(obj.get("editor_locked", False)) == next_value:
            return
        h._record_history()
        obj["editor_locked"] = next_value
        h._refresh_hierarchy(force=True)
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        if h._selected_name == name:
            h._scene_controller.select(name)
            h._update_inspector(name)
        state = "travada" if next_value else "destravada"
        h.statusBar().showMessage(f"Transformação de {name} {state}")

    def duplicate_selected(self) -> None:
        h = self.host
        if h._play_session.is_running or h._selected_name not in h._objects_by_name:
            return
        h._record_history()

        target_name = h._selected_name
        parent_obj = h._objects_by_name[target_name]

        def get_all_descendants(root_name: str) -> list[dict[str, Any]]:
            descendants: list[dict[str, Any]] = []
            for obj in h._scene_snapshot:
                if isinstance(obj, dict) and obj.get("parent") == root_name:
                    descendants.append(obj)
                    descendants.extend(get_all_descendants(str(obj.get("name", ""))))
            return descendants

        name_map: dict[str, str] = {}
        new_objects: list[dict[str, Any]] = []

        new_parent = deepcopy(parent_obj)
        new_parent["id"] = str(uuid.uuid4())
        new_parent_name = self.unique_name(f"{target_name}_copy")
        new_parent["name"] = new_parent_name
        new_parent["x"] = float(new_parent.get("x", 0.0)) + 16.0
        new_parent["y"] = float(new_parent.get("y", 0.0)) + 16.0
        new_parent["children"] = []
        name_map[target_name] = new_parent_name
        new_objects.append(new_parent)

        for child_obj in get_all_descendants(target_name):
            child_copy = deepcopy(child_obj)
            child_copy["id"] = str(uuid.uuid4())
            old_child_name = str(child_copy.get("name", "Child"))
            new_child_name = self.unique_name(f"{old_child_name}_copy")
            child_copy["name"] = new_child_name
            child_copy["children"] = []
            name_map[old_child_name] = new_child_name
            new_objects.append(child_copy)

        for cloned in new_objects:
            old_parent = cloned.get("parent")
            if old_parent and old_parent in name_map:
                cloned["parent"] = name_map[old_parent]

        for cloned in new_objects:
            h._scene_snapshot.append(cloned)
            h._objects_by_name[cloned["name"]] = cloned

        h._selected_name = new_parent_name
        self._publish_selected(new_parent_name)

    def _publish_selected(self, name: str) -> None:
        h = self.host
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._scene_controller.select(name)
        h._update_inspector(name)
