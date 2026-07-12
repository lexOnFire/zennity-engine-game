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
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QToolBar
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.isolated_viewport import run_viewport


class IsolatedEditorWindow(InterfaceSmokeTest):
    def __init__(self, viewport_process: mp.Process, commands, events) -> None:
        super().__init__()
        self._viewport_process = viewport_process
        self._commands = commands
        self._events = events
        self._initial_scene_snapshot = [
            {"name": "Chao", "x": 450.0, "y": 500.0, "w": 600.0, "h": 32.0, "color": (91, 194, 100)},
            {"name": "Player", "x": 450.0, "y": 250.0, "w": 36.0, "h": 48.0, "color": (88, 117, 255)},
        ]
        self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._selected_name: str | None = None
        self.setWindowTitle("Zennity — Interface isolada (PySide6)")
        self.statusBar().showMessage(
            "Viewport Pygame está em outra janela/processo. Arraste painéis aqui sem afetá-la."
        )
        self._build_viewport_link_toolbar()
        self._connect_hierarchy_to_viewport()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._event_timer = QTimer(self)
        self._event_timer.timeout.connect(self._read_viewport_events)
        self._event_timer.start(33)

    def _build_viewport_link_toolbar(self) -> None:
        toolbar = QToolBar("Ligação com Viewport")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        for label, payload in (
            ("Selecionar Player", {"type": "select_object", "name": "Player"}),
            ("Mover ←", {"type": "move_selected", "dx": -16}),
            ("Mover →", {"type": "move_selected", "dx": 16}),
            ("Play", {"type": "play"}),
            ("Stop", {"type": "stop"}),
            ("Reset", {"type": "reset_from_interface"}),
            ("Salvar Cena", {"type": "save_scene"}),
            ("Abrir Cena", {"type": "load_scene"}),
        ):
            action = QAction(label, self)
            action.triggered.connect(lambda checked=False, message=payload: self._send_toolbar_command(message))
            toolbar.addAction(action)

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
            self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
            if self._selected_name in self._objects_by_name:
                self._update_inspector(self._selected_name)
            return
        self._commands.put(message)

    def _save_scene_snapshot(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar cena isolada", "isolated_scene.json", "Cena JSON (*.json)"
        )
        if not filename:
            return
        payload = {"version": 1, "objects": self._scene_snapshot}
        Path(filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.statusBar().showMessage(f"Cena salva: {filename}")

    def _load_scene_snapshot(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Abrir cena isolada", "", "Cena JSON (*.json)"
        )
        if not filename:
            return
        try:
            payload = json.loads(Path(filename).read_text(encoding="utf-8"))
            objects = payload.get("objects", [])
            required = {"name", "x", "y", "w", "h"}
            if not isinstance(objects, list) or any(not required.issubset(item) for item in objects):
                raise ValueError("arquivo de cena inválido")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.statusBar().showMessage(f"Falha ao abrir cena: {exc}")
            return
        self._scene_snapshot = [dict(item) for item in objects]
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._selected_name = None
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self.statusBar().showMessage(f"Cena aberta: {filename}")

    def _connect_hierarchy_to_viewport(self) -> None:
        for tree in self.findChildren(QTreeWidget):
            tree.itemClicked.connect(self._select_hierarchy_item)

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
        self.inspector_labels["name"].setText(name)
        for key in ("x", "y", "w", "h"):
            self.inspector_labels[key].setText(f"{float(obj[key]):.2f}")

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
                if self._selected_name in self._objects_by_name:
                    self._update_inspector(self._selected_name)

    def closeEvent(self, event) -> None:
        try:
            self._commands.put_nowait({"type": "shutdown"})
        except Exception:
            pass
        if self._viewport_process.is_alive():
            self._viewport_process.terminate()
            self._viewport_process.join(timeout=2)
        super().closeEvent(event)


def main() -> None:
    context = mp.get_context("spawn")
    commands = context.Queue()
    events = context.Queue()
    viewport_process = context.Process(target=run_viewport, args=(commands, events), name="ZennityViewport")
    viewport_process.start()

    app = QApplication.instance() or QApplication(sys.argv)
    window = IsolatedEditorWindow(viewport_process, commands, events)
    window.show()
    exit_code = app.exec()

    if viewport_process.is_alive():
        viewport_process.terminate()
        viewport_process.join(timeout=2)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
