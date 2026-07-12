"""Inicializa Interface Qt e Viewport Pygame em processos independentes.

Execute a partir da raiz do projeto:
    python -m editor.isolated_editor_main
"""
from __future__ import annotations

import multiprocessing as mp
import sys
import json
from copy import deepcopy
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QToolBar
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.isolated_viewport import run_viewport


class IsolatedEditorWindow(InterfaceSmokeTest):
    def __init__(self, viewport_process: mp.Process | None, commands, events) -> None:
        super().__init__()
        self._viewport_process = viewport_process
        self._commands = commands
        self._events = events
        self._initial_scene_snapshot = [
            {"name": "Chao", "x": 450.0, "y": 500.0, "w": 600.0, "h": 32.0, "color": (91, 194, 100)},
            {"name": "Player", "x": 450.0, "y": 250.0, "w": 36.0, "h": 48.0, "color": (88, 117, 255)},
        ]
        self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
        self._scene_document: dict | None = None
        self._current_scene_path: Path | None = None
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._selected_name: str | None = None
        self._updating_inspector = False
        self.setWindowTitle("Zennity — Interface isolada (PySide6)")
        self.statusBar().showMessage(
            "Viewport Pygame está em outra janela/processo. Arraste painéis aqui sem afetá-la."
        )
        self._connect_existing_toolbar_actions()
        self._build_viewport_link_toolbar()
        self._connect_hierarchy_to_viewport()
        self._refresh_hierarchy()
        self._connect_inspector_to_viewport()
        self.viewport_host.installEventFilter(self)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._event_timer = QTimer(self)
        self._event_timer.timeout.connect(self._read_viewport_events)
        self._event_timer.start(33)

    def attach_viewport_process(self, process: mp.Process) -> None:
        self._viewport_process = process

    def native_viewport_size(self) -> tuple[int, int]:
        """Return physical pixels expected by the native Pygame child window."""
        scale = max(1.0, float(self.viewport_host.devicePixelRatioF()))
        return (
            max(32, round(self.viewport_host.width() * scale)),
            max(32, round(self.viewport_host.height() * scale)),
        )

    def eventFilter(self, watched, event) -> bool:
        if watched is self.viewport_host and event.type() == QEvent.Resize:
            width, height = self.native_viewport_size()
            self._commands.put({"type": "viewport_size", "w": width, "h": height})
        return super().eventFilter(watched, event)

    def _build_viewport_link_toolbar(self) -> None:
        toolbar = QToolBar("Ligação com Viewport")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for label, payload in (
            ("Selecionar Player", {"type": "select_object", "name": "Player"}),
            ("Mover ←", {"type": "move_selected", "dx": -16}),
            ("Mover →", {"type": "move_selected", "dx": 16}),
            ("Reset", {"type": "reset_from_interface"}),
        ):
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, message=payload: self._send_toolbar_command(message))
            toolbar.addAction(action)

    def _connect_existing_toolbar_actions(self) -> None:
        commands = {
            "Abrir": {"type": "load_scene"},
            "Salvar": {"type": "save_scene"},
            "Play": {"type": "play"},
            "Stop": {"type": "stop"},
        }
        for action in self.findChildren(QAction):
            payload = commands.get(action.text())
            if payload is not None:
                action.triggered.connect(
                    lambda checked=False, message=payload: self._send_toolbar_command(message)
                )

    def _send_toolbar_command(self, message: dict) -> None:
        if message.get("type") == "save_scene":
            self._save_scene_snapshot()
            return
        if message.get("type") == "load_scene":
            self._load_scene_snapshot()
            return
        if message.get("type") == "reset_from_interface":
            self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
            self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
            self._refresh_hierarchy()
            self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
            if self._selected_name in self._objects_by_name:
                self._update_inspector(self._selected_name)
            return
        self._commands.put(message)

    def _save_scene_snapshot(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar cena", str(self._current_scene_path or "Untitled.zscene"),
            "Zennity Scene (*.zscene);;Cena JSON (*.json)"
        )
        if not filename:
            return
        path = Path(filename)
        payload = deepcopy(self._scene_document) if self._scene_document else {
            "format_version": 1, "scene_name": path.stem, "engine_version": "Zennity 0.1.0", "objects": []
        }
        existing = {str(item.get("name")): item for item in payload.get("objects", [])}
        scene_objects = []
        for snapshot in self._scene_snapshot:
            source = deepcopy(existing.get(snapshot["name"], {}))
            source.update({"name": snapshot["name"], "active": True, "enabled": True})
            source.setdefault("id", snapshot.get("id", snapshot["name"]))
            source["transform"] = {
                "position": [snapshot["x"], snapshot["y"], 0.0],
                "rotation": source.get("transform", {}).get("rotation", [0.0, 0.0, 0.0]),
                "rz": source.get("transform", {}).get("rz", 0.0),
                "scale": [snapshot["w"], snapshot["h"], 1.0],
            }
            source.setdefault("visual", {"mesh_type": snapshot.get("mesh_type"), "color": snapshot.get("color")})
            source.setdefault("components", {})
            scene_objects.append(source)
        payload["objects"] = scene_objects
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self._scene_document = payload
        self._current_scene_path = path
        self.statusBar().showMessage(f"Cena salva: {filename}")

    def _load_scene_snapshot(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir cena", "", "Zennity Scene (*.zscene);;Cena JSON (*.json)"
        )
        if not filename:
            return
        try:
            payload = json.loads(Path(filename).read_text(encoding="utf-8"))
            objects = payload.get("objects", [])
            if not isinstance(objects, list):
                raise ValueError("arquivo de cena inválido")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.statusBar().showMessage(f"Falha ao abrir cena: {exc}")
            return
        snapshots = []
        for item in objects:
            if not isinstance(item, dict) or "name" not in item:
                continue
            if "transform" in item:
                transform = item.get("transform", {})
                position = list(transform.get("position", [0.0, 0.0, 0.0]))
                scale = list(transform.get("scale", [32.0, 32.0, 1.0]))
                visual = item.get("visual", {}) or {}
                color = visual.get("color") or ((91, 194, 100) if item["name"].lower() in {"chao", "floor"} else (88, 117, 255))
                snapshots.append({"id": item.get("id", item["name"]), "name": item["name"], "x": float(position[0]), "y": float(position[1]), "w": abs(float(scale[0])), "h": abs(float(scale[1])), "color": color, "mesh_type": visual.get("mesh_type")})
            elif {"x", "y", "w", "h"}.issubset(item):
                snapshots.append(dict(item))
        if not snapshots and objects:
            self.statusBar().showMessage("Falha ao abrir cena: nenhum objeto compatível")
            return
        self._scene_snapshot = snapshots
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._scene_document = payload if any("transform" in item for item in objects if isinstance(item, dict)) else None
        self._current_scene_path = Path(filename)
        self._selected_name = None
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self.statusBar().showMessage(f"Cena aberta: {filename}")

    def _connect_hierarchy_to_viewport(self) -> None:
        self.hierarchy_tree.itemClicked.connect(self._select_hierarchy_item)

    def _refresh_hierarchy(self) -> None:
        self.hierarchy_tree.clear()
        scene_name = self._scene_document.get("scene_name", "MainScene") if self._scene_document else "MainScene"
        root = QTreeWidgetItem([str(scene_name)])
        root.setExpanded(True)
        for obj in self._scene_snapshot:
            root.addChild(QTreeWidgetItem([str(obj["name"])]))
        self.hierarchy_tree.addTopLevelItem(root)

    def _connect_inspector_to_viewport(self) -> None:
        for field in self.inspector_fields.values():
            field.valueChanged.connect(lambda _value: self._send_inspector_transform())

    def _send_inspector_transform(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        for key, field in self.inspector_fields.items():
            obj[key] = float(field.value())
        self._commands.put({"type": "set_transform", "name": self._selected_name, **{k: obj[k] for k in ("x", "y", "w", "h")}})

    def _select_hierarchy_item(self, item: QTreeWidgetItem) -> None:
        name = item.text(0)
        if name in self._objects_by_name:
            self._commands.put({"type": "select_object", "name": name})
            self._selected_name = name
            self._update_inspector(name)
            self.statusBar().showMessage(f"Interface: {name} selecionado")

    def _update_inspector(self, name: str) -> None:
        obj = self._objects_by_name.get(name)
        if obj is None:
            return
        self._updating_inspector = True
        try:
            self.inspector_name_label.setText(name)
            for key in ("x", "y", "w", "h"):
                self.inspector_fields[key].setValue(float(obj[key]))
        finally:
            self._updating_inspector = False

    def _read_viewport_events(self) -> None:
        while True:
            try:
                message = self._events.get_nowait()
            except Exception:
                return
            if message.get("type") == "selected":
                self._selected_name = message["name"]
                self._update_inspector(self._selected_name)
                self.statusBar().showMessage(f"Viewport: {self._selected_name} selecionado")
            elif message.get("type") == "transform":
                obj = self._objects_by_name.get(message["name"])
                if obj is not None:
                    obj["x"] = float(message["x"])
                    obj["y"] = float(message["y"])
                    if "w" in message:
                        obj["w"] = float(message["w"])
                    if "h" in message:
                        obj["h"] = float(message["h"])
                    if message["name"] == self._selected_name:
                        self._update_inspector(self._selected_name)
                self.statusBar().showMessage(
                    f"Viewport: {message['name']} em X={message['x']:.1f}, Y={message['y']:.1f}"
                )
            elif message.get("type") == "play_state":
                self.statusBar().showMessage(
                    "Viewport: PLAY" if message["state"] == "play" else "Viewport: EDIT — cena restaurada"
                )
            elif message.get("type") == "scene_snapshot":
                self._scene_snapshot = [dict(item) for item in message.get("objects", [])]
                self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
                self._refresh_hierarchy()
                if self._selected_name in self._objects_by_name:
                    self._update_inspector(self._selected_name)
            elif message.get("type") == "viewport_mode":
                state = "embutida" if message.get("embedded") else "em janela separada (fallback)"
                self.statusBar().showMessage(f"Viewport {state}")

    def closeEvent(self, event) -> None:
        try:
            self._commands.put_nowait({"type": "shutdown"})
        except Exception:
            pass
        if self._viewport_process is not None and self._viewport_process.is_alive():
            self._viewport_process.terminate()
            self._viewport_process.join(timeout=2)
        super().closeEvent(event)


def main() -> None:
    context = mp.get_context("spawn")
    commands = context.Queue()
    events = context.Queue()
    app = QApplication.instance() or QApplication(sys.argv)
    window = IsolatedEditorWindow(None, commands, events)
    window.show()
    app.processEvents()

    host_id = int(window.viewport_host.winId())
    host_size = window.native_viewport_size()
    viewport_process = context.Process(
        target=run_viewport,
        args=(commands, events, host_id, host_size),
        name="ZennityViewport",
    )
    window.attach_viewport_process(viewport_process)
    viewport_process.start()
    exit_code = app.exec()

    if viewport_process.is_alive():
        viewport_process.terminate()
        viewport_process.join(timeout=2)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
