"""Mixin de manipulação de mídia e UI para IsolatedInspectorController."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QFileDialog

from editor.runtime.native_ui import normalize_ui
from editor.runtime.sprite_rendering import assign_sprite_texture


class InspectorControllerUIMediaMixin:
    """Isola lógica de dialogs de cor, arquivo de imagem/som e UI no Inspector."""

    def choose_sprite_texture(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        h = self.host
        filename, _ = QFileDialog.getOpenFileName(
            h,
            "Selecionar textura",
            str(Path.cwd() / "Assets"),
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not filename:
            return
        path = Path(filename)
        try:
            texture = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            textures_dir = Path.cwd() / "Assets" / "Textures"
            textures_dir.mkdir(parents=True, exist_ok=True)
            destination = textures_dir / path.name
            index = 1
            while destination.exists() and destination.read_bytes() != path.read_bytes():
                destination = textures_dir / f"{path.stem}_{index}{path.suffix}"
                index += 1
            if not destination.exists():
                shutil.copy2(path, destination)
            texture = destination.relative_to(Path.cwd()).as_posix()
            h._refresh_assets()
        h._record_history()
        assign_sprite_texture(obj, texture)
        h.sprite_texture_field.setText(texture)
        h.sprite_color_button.setStyleSheet("background: rgb(255, 255, 255);")
        self.send_renderer(record_history=False)
        h._log("INFO", f"Textura aplicada sem tint: {Path(texture).name}")

    def choose_sprite_color(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        h = self.host
        current = obj.get("color", (255, 255, 255))
        color = QColorDialog.getColor(QColor(*current[:3]), h, "Cor do Sprite")
        if not color.isValid():
            return
        h._record_history()
        obj["color"] = (color.red(), color.green(), color.blue())
        h.sprite_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        self.send_renderer(record_history=False)

    def choose_camera_color(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        camera = obj.get("camera")
        if not isinstance(camera, dict):
            return
        h = self.host
        current = camera.get("background_color", [22, 24, 31])
        color = QColorDialog.getColor(QColor(*current[:3]), h, "Cor de fundo da câmera")
        if not color.isValid():
            return
        h._record_history()
        camera["background_color"] = [color.red(), color.green(), color.blue()]
        h.camera_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def toggle_ui_visibility(self, checked: bool) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        ui = obj.get("ui")
        if not isinstance(ui, dict):
            return
        h = self.host
        h._record_history()
        ui["visible"] = bool(checked)
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def delete_ui(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        if "ui" not in obj:
            return
        h = self.host
        h._record_history()
        obj.pop("ui", None)
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._update_inspector(name)

    def choose_ui_color(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        ui = normalize_ui(obj.get("ui"))
        if ui is None:
            return
        h = self.host
        color = QColorDialog.getColor(QColor(*tuple(ui.get("color", (255, 255, 255)))[:3]), h, "Cor da UI")
        if not color.isValid():
            return
        h._record_history()
        obj["ui"]["color"] = [color.red(), color.green(), color.blue()]
        h.ui_color_button.setStyleSheet(f"background: rgb({color.red()}, {color.green()}, {color.blue()});")
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def choose_ui_image(self) -> None:
        if self._selected() is None:
            return
        h = self.host
        filename, _ = QFileDialog.getOpenFileName(
            h,
            "Selecionar imagem da UI",
            str(Path.cwd() / "Assets"),
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not filename:
            return
        path = Path(filename)
        try:
            value = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            value = str(path.resolve())
        h.ui_image_path_field.setText(value)
        self.send_ui()

    def send_ui(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        ui = normalize_ui(obj.get("ui"))
        if ui is None:
            return
        h = self.host
        h._record_history()
        ui.update({key: float(field.value()) for key, field in h.ui_position_fields.items()})
        ui.update({
            "visible": h.show_ui_chk.isChecked(),
            "text": h.ui_text_field.text(),
            "path": h.ui_image_path_field.text(),
            "interactable": h.ui_interactable_field.isChecked(),
            "event": h.ui_event_field.text().strip() or "click",
            "target": "" if h.ui_target_combo.currentText() == "Este objeto" else h.ui_target_combo.currentText(),
        })
        obj["ui"] = ui
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def ensure_canvas(self) -> None:
        h = self.host
        if any((normalize_ui(obj.get("ui")) or {}).get("type") == "canvas" for obj in h._scene_snapshot):
            return
        name = h._unique_name("Canvas")
        canvas = {
            "id": str(uuid.uuid4()),
            "name": name,
            "x": 0.0,
            "y": 0.0,
            "w": 1.0,
            "h": 1.0,
            "rotation": 0.0,
            "color": (255, 255, 255),
            "mesh_type": "UI",
            "renderer_enabled": False,
            "ui": normalize_ui({"type": "canvas"}),
        }
        h._scene_snapshot.append(canvas)
        h._objects_by_name[name] = canvas
        h._log("INFO", "Canvas criado automaticamente para a interface do jogo")
