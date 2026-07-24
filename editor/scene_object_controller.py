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
        h._record_history()
        h._scene_snapshot = []
        h._objects_by_name = {}
        h._scene_document = {
            "format_version": 1,
            "scene_name": "Untitled",
            "engine_version": "Zennity 0.1.0",
            "objects": [],
        }
        h._current_scene_path = None
        h._selected_name = None
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot([])
        h.statusBar().showMessage("Nova cena criada")
        h._log("INFO", "Nova cena criada")

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
        h._record_history()
        base, width, height, color, rigidbody = self.PRESETS[kind]
        name = self.unique_name(base)
        obj = {
            "id": str(uuid.uuid4()), "name": name, "x": 450.0, "y": 250.0,
            "w": width, "h": height, "rotation": 0.0, "color": color,
            "mesh_type": kind,
        }
        if rigidbody is not None:
            obj["rigidbody"] = deepcopy(rigidbody)
            obj["collider"] = {"type": "box"}
        if kind == "Trigger":
            obj["collider"]["is_trigger"] = True
        if kind == "Camera":
            obj["component_names"] = ["Camera2D"]
            obj["camera"] = {"active": True, "zoom": 1.0}
        h._scene_snapshot.append(obj)
        h._objects_by_name[name] = obj
        h._selected_name = name
        self._publish_selected(name)
        h._log("INFO", f"Objeto criado: {name}")

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
        h._record_history()
        obj = h._objects_by_name.pop(old_name)
        obj["name"] = new_name
        h._objects_by_name[new_name] = obj
        if h._selected_name == old_name:
            h._selected_name = new_name
        self._publish_selected(new_name)

    def delete(self, name: str) -> None:
        h = self.host
        if h._play_session.is_running or name not in h._objects_by_name:
            return
        h._record_history()
        h._scene_snapshot = [obj for obj in h._scene_snapshot if obj["name"] != name]
        h._objects_by_name.pop(name, None)
        if h._selected_name == name:
            h._selected_name = None
            for header, body in h.script_containers:
                h.inspector_layout.removeWidget(header)
                h.inspector_layout.removeWidget(body)
                header.deleteLater()
                body.deleteLater()
            h.script_containers.clear()
            h._clear_inspector_view()
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def duplicate_selected(self) -> None:
        h = self.host
        if h._play_session.is_running or h._selected_name not in h._objects_by_name:
            return
        h._record_history()
        duplicate = deepcopy(h._objects_by_name[h._selected_name])
        duplicate["id"] = str(uuid.uuid4())
        duplicate["name"] = self.unique_name(f"{h._selected_name}_copy")
        duplicate["x"] = float(duplicate.get("x", 0.0)) + 16.0
        duplicate["y"] = float(duplicate.get("y", 0.0)) + 16.0
        h._scene_snapshot.append(duplicate)
        h._objects_by_name[duplicate["name"]] = duplicate
        h._selected_name = duplicate["name"]
        self._publish_selected(duplicate["name"])

    def _publish_selected(self, name: str) -> None:
        h = self.host
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._scene_controller.select(name)
        h._update_inspector(name)
