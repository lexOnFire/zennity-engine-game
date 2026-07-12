"""Inicializa Interface Qt e Viewport Pygame em processos independentes.

Execute a partir da raiz do projeto:
    python -m editor.isolated_editor_main
"""
from __future__ import annotations

import multiprocessing as mp
import sys
import json
import uuid
from copy import deepcopy
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMenu, QToolBar
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
            {"id": "floor", "name": "Chao", "x": 450.0, "y": 500.0, "w": 600.0, "h": 32.0, "color": (91, 194, 100), "rigidbody": {"is_kinematic": True, "use_gravity": False}, "collider": {"type": "box"}},
            {"id": "player", "name": "Player", "x": 450.0, "y": 250.0, "w": 36.0, "h": 48.0, "color": (88, 117, 255), "rigidbody": {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}, "collider": {"type": "box"}},
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
        self._configure_create_menu()
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
            "Novo": {"type": "new_scene"},
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
        if message.get("type") == "new_scene":
            self._new_scene()
            return
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

    def _configure_create_menu(self) -> None:
        for menu_action in self.menuBar().actions():
            menu = menu_action.menu()
            if menu is None or menu.title() != "Criar":
                continue
            menu.clear()
            for label, kind in (("Empty Object", "Empty"), ("Player 2D", "Player"), ("Platform 2D", "Platform")):
                action = menu.addAction(label)
                action.triggered.connect(lambda checked=False, object_kind=kind: self._create_object(object_kind))
            break

    def _new_scene(self) -> None:
        self._scene_snapshot = []
        self._objects_by_name = {}
        self._scene_document = {"format_version": 1, "scene_name": "Untitled", "engine_version": "Zennity 0.1.0", "objects": []}
        self._current_scene_path = None
        self._selected_name = None
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": []})
        self.statusBar().showMessage("Nova cena criada")

    def _unique_name(self, base: str) -> str:
        if base not in self._objects_by_name:
            return base
        index = 2
        while f"{base}_{index}" in self._objects_by_name:
            index += 1
        return f"{base}_{index}"

    def _create_object(self, kind: str) -> None:
        presets = {
            "Empty": ("GameObject", 40.0, 40.0, (160, 164, 174), None),
            "Player": ("Player", 36.0, 48.0, (88, 117, 255), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Platform": ("Platform", 160.0, 32.0, (91, 194, 100), {"is_kinematic": True, "use_gravity": False}),
        }
        base, width, height, color, rigidbody = presets[kind]
        name = self._unique_name(base)
        obj = {"id": str(uuid.uuid4()), "name": name, "x": 450.0, "y": 250.0, "w": width, "h": height, "color": color, "mesh_type": kind}
        if rigidbody is not None:
            obj["rigidbody"] = rigidbody
            obj["collider"] = {"type": "box"}
        self._scene_snapshot.append(obj)
        self._objects_by_name[name] = obj
        self._selected_name = name
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": name})
        self._update_inspector(name)

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
        existing_by_id = {str(item.get("id")): item for item in payload.get("objects", []) if item.get("id") is not None}
        existing_by_name = {str(item.get("name")): item for item in payload.get("objects", [])}
        scene_objects = []
        for snapshot in self._scene_snapshot:
            source = deepcopy(existing_by_id.get(str(snapshot.get("id"))) or existing_by_name.get(snapshot["name"], {}))
            source.update({"name": snapshot["name"], "active": True, "enabled": True})
            source.setdefault("id", snapshot.get("id", snapshot["name"]))
            source["transform"] = {
                "position": [snapshot["x"], snapshot["y"], 0.0],
                "rotation": source.get("transform", {}).get("rotation", [0.0, 0.0, 0.0]),
                "rz": source.get("transform", {}).get("rz", 0.0),
                "scale": [snapshot["w"], snapshot["h"], 1.0],
            }
            source.setdefault("visual", {"mesh_type": snapshot.get("mesh_type"), "color": snapshot.get("color")})
            components = source.setdefault("components", {})
            if snapshot.get("rigidbody") is not None:
                components["rigidbody"] = deepcopy(snapshot["rigidbody"])
            if snapshot.get("collider") is not None:
                collider = deepcopy(snapshot["collider"])
                collider.setdefault("width", snapshot["w"])
                collider.setdefault("height", snapshot["h"])
                components["collider"] = collider
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
                components = item.get("components", {}) or {}
                color = visual.get("color") or ((91, 194, 100) if item["name"].lower() in {"chao", "floor"} else (88, 117, 255))
                snapshot = {"id": item.get("id", item["name"]), "name": item["name"], "x": float(position[0]), "y": float(position[1]), "w": abs(float(scale[0])), "h": abs(float(scale[1])), "color": color, "mesh_type": visual.get("mesh_type")}
                if isinstance(components.get("rigidbody"), dict):
                    snapshot["rigidbody"] = deepcopy(components["rigidbody"])
                if isinstance(components.get("collider"), dict):
                    snapshot["collider"] = deepcopy(components["collider"])
                snapshots.append(snapshot)
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
        self.hierarchy_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hierarchy_tree.customContextMenuRequested.connect(self._open_hierarchy_menu)

    def _open_hierarchy_menu(self, position) -> None:
        item = self.hierarchy_tree.itemAt(position)
        if item is None or item.text(0) not in self._objects_by_name:
            return
        menu = QMenu(self)
        rename_action = menu.addAction("Renomear")
        delete_action = menu.addAction("Excluir")
        rename_action.triggered.connect(lambda _checked=False: self._rename_object(item.text(0)))
        delete_action.triggered.connect(lambda _checked=False: self._delete_object(item.text(0)))
        menu.exec(self.hierarchy_tree.viewport().mapToGlobal(position))

    def _rename_object(self, old_name: str) -> None:
        new_name, accepted = QInputDialog.getText(self, "Renomear objeto", "Nome:", text=old_name)
        new_name = new_name.strip()
        if not accepted or not new_name or (new_name != old_name and new_name in self._objects_by_name):
            return
        obj = self._objects_by_name.pop(old_name)
        obj["name"] = new_name
        self._objects_by_name[new_name] = obj
        if self._selected_name == old_name:
            self._selected_name = new_name
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": new_name})
        self._update_inspector(new_name)

    def _delete_object(self, name: str) -> None:
        self._scene_snapshot = [obj for obj in self._scene_snapshot if obj["name"] != name]
        self._objects_by_name.pop(name, None)
        if self._selected_name == name:
            self._selected_name = None
            self.inspector_name_label.setText("—")
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})

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
        for field in self.physics_fields.values():
            field.toggled.connect(lambda _checked: self._send_inspector_physics())

    def _send_inspector_physics(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        rigidbody = obj.get("rigidbody")
        if rigidbody is None:
            return
        rigidbody["use_gravity"] = self.physics_fields["use_gravity"].isChecked()
        rigidbody["is_kinematic"] = self.physics_fields["is_kinematic"].isChecked()
        self._commands.put({"type": "set_physics", "name": self._selected_name, "rigidbody": rigidbody})

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
            rigidbody = obj.get("rigidbody")
            for key, field in self.physics_fields.items():
                field.setEnabled(rigidbody is not None)
                field.setChecked(bool((rigidbody or {}).get(key, False)))
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
