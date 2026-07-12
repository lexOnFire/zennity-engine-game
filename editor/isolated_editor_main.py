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
from PySide6.QtCore import QEvent, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices, QPixmap
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMenu, QToolBar, QHBoxLayout, QFormLayout, QCheckBox, QLabel
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QWidget

from editor.interface_smoke_test import InterfaceSmokeTest
from editor.isolated_viewport import run_viewport
from editor.script_templates import build_isolated_script_template, inspect_script_contract


class IsolatedEditorWindow(InterfaceSmokeTest):
    def __init__(self, viewport_process: mp.Process | None, commands, events) -> None:
        super().__init__()
        self._viewport_process = viewport_process
        self._commands = commands
        self._events = events
        self._initial_scene_snapshot = [
            {"id": "floor", "name": "Chao", "x": 0.0, "y": 150.0, "w": 600.0, "h": 32.0, "rotation": 0.0, "color": (91, 194, 100), "rigidbody": {"is_kinematic": True, "use_gravity": False}, "collider": {"type": "box"}},
            {"id": "player", "name": "Player", "x": 0.0, "y": 0.0, "w": 36.0, "h": 48.0, "rotation": 0.0, "color": (88, 117, 255), "rigidbody": {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}, "collider": {"type": "box"}, "scripts": ["Assets/Scripts/player_controller_2d.py"]},
        ]
        self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
        self._scene_document: dict | None = None
        self._current_scene_path: Path | None = None
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._selected_name: str | None = None
        self._updating_inspector = False
        self._undo_stack: list[list[dict]] = []
        self._redo_stack: list[list[dict]] = []
        self._drag_history_snapshot: list[dict] | None = None
        self._snap_enabled = False
        self.setWindowTitle("Zennity Engine Editor — Phase 1")
        self.statusBar().showMessage(
            "Zennity Phase 1 pronto — Viewport em processo dedicado."
        )
        self._connect_existing_toolbar_actions()
        self._configure_main_menus()
        self._configure_tool_actions()
        self._configure_create_menu()
        self._connect_create_panel()
        self._configure_edit_menu()
        self._refresh_assets()
        self.assets_tree.itemClicked.connect(self._preview_asset)
        self._connect_hierarchy_to_viewport()
        self._refresh_hierarchy()
        self._connect_inspector_to_viewport()
        self.script_containers = []
        self.add_component_button.clicked.connect(self._open_add_component_menu)
        self.viewport_tabs.currentChanged.connect(self._change_view_mode)

        # Habilita Drag & Drop na árvore de assets e viewport_host
        self.assets_tree.setDragEnabled(True)
        self.viewport_host.setAcceptDrops(True)
        self.viewport_host.installEventFilter(self)
        self._hierarchy_drop_targets = {self.hierarchy_tree, self.hierarchy_tree.viewport()}
        self._inspector_drop_targets = {self.inspector_panel, *self.inspector_panel.findChildren(QWidget)}
        self._scene_drop_targets = {self.scene_script_drop_zone, self.viewport_tabs, self.viewport_tabs.tabBar(), self.viewport_host}
        self._script_drop_targets = self._hierarchy_drop_targets | self._inspector_drop_targets | self._scene_drop_targets
        for target in self._script_drop_targets:
            target.setAcceptDrops(True)
            target.installEventFilter(self)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._event_timer = QTimer(self)
        self._event_timer.timeout.connect(self._read_viewport_events)
        self._event_timer.start(33)
        self._log("INFO", "Zennity Phase 1 iniciado com Viewport em processo separado")

    def _log(self, level: str, message: str) -> None:
        self.console_output.appendPlainText(f"[{level}] {message}")

    def _connect_create_panel(self) -> None:
        for kind, button in self.create_buttons.items():
            button.clicked.connect(lambda checked=False, object_kind=kind: self._create_object(object_kind))

    def _preview_asset(self, item: QTreeWidgetItem) -> None:
        path_value = item.toolTip(0)
        if not path_value:
            return
        path = Path(path_value)
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.preview_label.setPixmap(pixmap.scaled(260, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        self.preview_label.clear()
        self.preview_label.setText(f"{path.name}\n{path}")

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
        if watched in self._script_drop_targets:
            if event.type() == QEvent.DragEnter:
                if event.source() is not self.assets_tree:
                    return super().eventFilter(watched, event)
                path = self._dragged_asset_path()
                if path is not None and path.suffix.lower() in {".py", ".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.DragMove:
                if event.source() is not self.assets_tree:
                    return super().eventFilter(watched, event)
                event.acceptProposedAction()
                return True
            elif event.type() == QEvent.Drop:
                if event.source() is not self.assets_tree:
                    return super().eventFilter(watched, event)
                path = self._dragged_asset_path()
                if path is not None and path.suffix.lower() == ".py":
                    if watched is self.viewport_host:
                        pos = event.position()
                        scale = max(1.0, float(self.viewport_host.devicePixelRatioF()))
                        self._commands.put({"type": "script_drop_at", "path": str(path.resolve()), "screen_x": float(pos.x()) * scale, "screen_y": float(pos.y()) * scale})
                        event.acceptProposedAction()
                        return True
                    target_name = self._selected_name
                    if watched in self._hierarchy_drop_targets:
                        local_position = self.hierarchy_tree.viewport().mapFromGlobal(event.globalPosition().toPoint())
                        item = self.hierarchy_tree.itemAt(local_position)
                        item_name = self._hierarchy_item_name(item)
                        if item_name in self._objects_by_name:
                            target_name = item_name
                    if target_name in self._objects_by_name:
                        self._attach_script(target_name, path)
                        event.acceptProposedAction()
                        return True
                elif path is not None and watched is self.viewport_host and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                    pos = event.position()
                    self._create_object_at("Sprite", float(pos.x()), float(pos.y()))
                    event.acceptProposedAction()
                    return True
        return super().eventFilter(watched, event)

    def _dragged_asset_path(self) -> Path | None:
        selected_items = self.assets_tree.selectedItems()
        if not selected_items:
            return None
        path_value = selected_items[0].toolTip(0)
        return Path(path_value) if path_value else None

    def _attach_script(self, object_name: str, path: Path) -> None:
        if object_name not in self._objects_by_name or path.suffix.lower() != ".py":
            return
        try:
            script_path = str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
        except ValueError:
            script_path = str(path.resolve())
        obj = self._objects_by_name[object_name]
        if script_path in obj.get("scripts", []):
            self.statusBar().showMessage(f"Script já anexado: {path.name}")
            return
        compatible, reason = inspect_script_contract(path)
        if not compatible:
            self._log("WARNING", f"Script anexado, mas incompatível com Play isolado: {path.name}: {reason}")
        self._record_history()
        scripts = obj.setdefault("scripts", [])
        scripts.append(script_path)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": object_name})
        self._selected_name = object_name
        self._update_inspector(object_name)
        self._log("INFO", f"Script anexado em {object_name}: {script_path}")

    def _get_available_scripts(self) -> list[Path]:
        scripts_dir = Path.cwd() / "Assets" / "Scripts"
        if scripts_dir.exists():
            return sorted([p for p in scripts_dir.glob("*.py") if p.name != "__init__.py"])
        return []

    def _change_attached_script(self, old_path: str, new_path: str) -> None:
        if self._selected_name not in self._objects_by_name or not new_path:
            return
        if old_path == new_path:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        scripts = obj.get("scripts", [])
        if old_path in scripts:
            idx = scripts.index(old_path)
            scripts[idx] = new_path
        else:
            scripts.append(new_path)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Script alterado de {Path(old_path).name} para {Path(new_path).name}")

    def _remove_single_script(self, script_path: str) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        scripts = obj.get("scripts", [])
        if script_path in scripts:
            scripts.remove(script_path)
        if not scripts:
            obj.pop("scripts", None)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Script removido: {Path(script_path).name}")

    def _update_script_config_val(self, script_path: str, key: str, value: float | bool) -> None:
        try:
            full_p = Path.cwd() / script_path
            if not full_p.exists():
                return
            content = full_p.read_text(encoding="utf-8")
            import ast
            tree = ast.parse(content)
            
            # Localiza a atribuição do CONFIG
            config_node = None
            for node in tree.body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, ast.Name) and target.id == "CONFIG" and isinstance(node.value, ast.Dict):
                        config_node = node
                        break
            
            if config_node:
                # Modifica o valor no AST/Texto
                for k_node, v_node in zip(config_node.value.keys, config_node.value.values):
                    if isinstance(k_node, ast.Constant) and k_node.value == key:
                        start_idx = v_node.col_offset
                        end_idx = v_node.end_col_offset
                        # Simples substituição textual baseada em linha
                        lines = content.splitlines()
                        target_line = config_node.lineno - 1
                        line_str = lines[target_line]
                        new_val_str = str(value)
                        lines[target_line] = line_str[:start_idx] + new_val_str + line_str[end_idx:]
                        full_p.write_text("\n".join(lines), encoding="utf-8")
                        self._log("INFO", f"Atualizado CONFIG['{key}'] = {value} em {Path(script_path).name}")
                        break
        except Exception as e:
            self._log("WARNING", f"Falha ao atualizar propriedade do script: {e}")

    def _remove_all_scripts(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        obj.pop("scripts", None)
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Todos os scripts removidos de {self._selected_name}")

    def _create_script_asset(self) -> None:
        if self._selected_name not in self._objects_by_name:
            self.statusBar().showMessage("Selecione um objeto antes de criar o script")
            return
        default_path = Path.cwd() / "Assets" / "Scripts" / "new_script.py"
        filename, _ = QFileDialog.getSaveFileName(self, "Criar Script", str(default_path), "Python Script (*.py)")
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".py":
            path = path.with_suffix(".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(build_isolated_script_template(path.stem), encoding="utf-8")
        self._refresh_assets()
        self._attach_script(self._selected_name, path)
        self._edit_script_path(path)

    def _edit_selected_script(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        scripts = obj.get("scripts", [])
        if not scripts:
            self.statusBar().showMessage("Nenhum script anexado para editar")
            return
        self._edit_script_path(Path(scripts[0]))

    def _edit_script_path(self, path: Path) -> None:
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            self.statusBar().showMessage(f"Script não encontrado: {path}")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve()))):
            self.statusBar().showMessage(f"Não foi possível abrir o editor para {path.name}")

    def _change_view_mode(self, index: int) -> None:
        mode = "scene" if index == 0 else "game"
        self._commands.put({"type": "set_view_mode", "mode": mode})
        self._log("INFO", f"Aba alterada para: {mode.upper()}")

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

    def _configure_main_menus(self) -> None:
        for label in ("Novo", "Abrir", "Salvar"):
            self.editor_menus["Arquivo"].addAction(self.toolbar_actions[label])
        for label in ("Select", "Move", "Rotate", "Scale", "Snap: OFF"):
            self.editor_menus["Ferramentas"].addAction(self.toolbar_actions[label])
        for label in ("Play", "Pause", "Stop"):
            self.editor_menus["Executar"].addAction(self.toolbar_actions[label])
        self.toolbar_actions["Pause"].setEnabled(False)
        self.toolbar_actions["Stop"].setEnabled(False)
        snap_action = self.toolbar_actions["Snap: OFF"]
        snap_action.setCheckable(True)
        snap_action.toggled.connect(self._toggle_snap)

    def _toggle_snap(self, enabled: bool) -> None:
        self._snap_enabled = bool(enabled)
        action = self.toolbar_actions["Snap: OFF"]
        action.setText("Snap: ON" if enabled else "Snap: OFF")
        self._commands.put({"type": "set_snap", "enabled": bool(enabled), "size": 16.0, "angle": 15.0})
        self.statusBar().showMessage("Snap ativado" if enabled else "Snap desativado")

    def _refresh_assets(self) -> None:
        self.assets_tree.clear()
        root_path = Path.cwd() / "Assets"
        if not root_path.exists():
            root_path = Path.cwd() / "assets"
        root_item = QTreeWidgetItem(["📁 " + (root_path.name if root_path.exists() else "Assets")])
        self.assets_tree.addTopLevelItem(root_item)

        def add_directory(parent_item: QTreeWidgetItem, directory: Path) -> None:
            for child in sorted(directory.iterdir(), key=lambda path: (path.is_file(), path.name.lower())):
                if child.name.startswith(".") or child.suffix == ".meta":
                    continue
                if child.is_dir():
                    icon = "📁 "
                elif child.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    icon = "🖼️ "
                elif child.suffix.lower() in (".ogg", ".wav", ".mp3"):
                    icon = "🔊 "
                else:
                    icon = "📄 "
                item = QTreeWidgetItem([icon + child.name])
                item.setToolTip(0, str(child))
                parent_item.addChild(item)
                if child.is_dir():
                    add_directory(item, child)

        if root_path.exists():
            add_directory(root_item, root_path)
        root_item.setExpanded(True)

    def _connect_existing_toolbar_actions(self) -> None:
        commands = {
            "Novo": {"type": "new_scene"},
            "Abrir": {"type": "load_scene"},
            "Salvar": {"type": "save_scene"},
            "Play": {"type": "play"},
            "Pause": {"type": "pause"},
            "Stop": {"type": "stop"},
        }
        for action in self.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            payload = commands.get(label)
            if payload is not None:
                action.triggered.connect(
                    lambda checked=False, message=payload: self._send_toolbar_command(message)
                )

    def _configure_tool_actions(self) -> None:
        group = QActionGroup(self)
        group.setExclusive(True)
        shortcuts = {"select": "Q", "move": "W", "rotate": "E", "scale": "R"}
        for action in self.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            tool = label.lower()
            if tool not in {"select", "move", "rotate", "scale"}:
                continue
            action.setCheckable(True)
            action.setShortcut(shortcuts[tool])
            action.setChecked(tool == "select")
            group.addAction(action)
            action.triggered.connect(lambda checked=False, name=tool: checked and self._commands.put({"type": "set_tool", "tool": name}))
        self._tool_action_group = group

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
            self._record_history()
            self._scene_snapshot = deepcopy(self._initial_scene_snapshot)
            self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
            self._refresh_hierarchy()
            self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
            if self._selected_name in self._objects_by_name:
                self._update_inspector(self._selected_name)
            return
        if message.get("type") == "play":
            self.viewport_tabs.setCurrentIndex(1)
        elif message.get("type") == "stop":
            self.viewport_tabs.setCurrentIndex(0)
        if message.get("type") == "move_selected" and self._selected_name is not None:
            self._record_history()
        self._commands.put(message)

    def _configure_create_menu(self) -> None:
        for menu_action in self.menuBar().actions():
            menu = menu_action.menu()
            if menu is None or menu.title() != "Criar":
                continue
            menu.clear()
            for label, kind in (
                ("Empty Object", "Empty"), ("Sprite 2D", "Sprite"),
                ("Player 2D", "Player"), ("Platform 2D", "Platform"),
                ("Enemy 2D", "Enemy"), ("Trigger 2D", "Trigger"),
                ("Camera 2D", "Camera"),
            ):
                action = menu.addAction(label)
                action.triggered.connect(lambda checked=False, object_kind=kind: self._create_object(object_kind))
            break

    def _configure_edit_menu(self) -> None:
        for menu_action in self.menuBar().actions():
            menu = menu_action.menu()
            if menu is None or menu.title() != "Editar":
                continue
            menu.clear()
            undo_action = self.toolbar_actions["Desfazer"]
            undo_action.setShortcut("Ctrl+Z")
            undo_action.triggered.connect(self._undo)
            menu.addAction(undo_action)
            redo_action = self.toolbar_actions["Refazer"]
            redo_action.setShortcut("Ctrl+Y")
            redo_action.triggered.connect(self._redo)
            menu.addAction(redo_action)
            menu.addSeparator()
            duplicate_action = menu.addAction("Duplicar")
            duplicate_action.setShortcut("Ctrl+D")
            duplicate_action.triggered.connect(self._duplicate_selected)
            delete_action = menu.addAction("Excluir")
            delete_action.setShortcut("Delete")
            delete_action.triggered.connect(
                lambda _checked=False: self._selected_name is not None and self._delete_object(self._selected_name)
            )
            break

    def _record_history(self, snapshot: list[dict] | None = None) -> None:
        state = deepcopy(snapshot if snapshot is not None else self._scene_snapshot)
        if not self._undo_stack or self._undo_stack[-1] != state:
            self._undo_stack.append(state)
            self._undo_stack = self._undo_stack[-100:]
        self._redo_stack.clear()

    def _restore_history(self, snapshot: list[dict]) -> None:
        self._scene_snapshot = deepcopy(snapshot)
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        if self._selected_name not in self._objects_by_name:
            self._selected_name = None
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        if self._selected_name is not None:
            self._commands.put({"type": "select_object", "name": self._selected_name})
            self._update_inspector(self._selected_name)

    def _undo(self) -> None:
        if self._undo_stack:
            self._redo_stack.append(deepcopy(self._scene_snapshot))
            self._restore_history(self._undo_stack.pop())

    def _redo(self) -> None:
        if self._redo_stack:
            self._undo_stack.append(deepcopy(self._scene_snapshot))
            self._restore_history(self._redo_stack.pop())

    def _new_scene(self) -> None:
        self._record_history()
        self._scene_snapshot = []
        self._objects_by_name = {}
        self._scene_document = {"format_version": 1, "scene_name": "Untitled", "engine_version": "Zennity 0.1.0", "objects": []}
        self._current_scene_path = None
        self._selected_name = None
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": []})
        self.statusBar().showMessage("Nova cena criada")
        self._log("INFO", "Nova cena criada")

    def _unique_name(self, base: str) -> str:
        if base not in self._objects_by_name:
            return base
        index = 2
        while f"{base}_{index}" in self._objects_by_name:
            index += 1
        return f"{base}_{index}"

    def _create_object(self, kind: str) -> None:
        self._record_history()
        presets = {
            "Empty": ("GameObject", 40.0, 40.0, (160, 164, 174), None),
            "Sprite": ("Sprite", 64.0, 64.0, (180, 180, 190), None),
            "Player": ("Player", 36.0, 48.0, (88, 117, 255), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Platform": ("Platform", 160.0, 32.0, (91, 194, 100), {"is_kinematic": True, "use_gravity": False}),
            "Enemy": ("Enemy", 40.0, 40.0, (220, 88, 88), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Trigger": ("Trigger", 80.0, 80.0, (222, 178, 72), {"is_kinematic": True, "use_gravity": False}),
            "Camera": ("Camera2D", 96.0, 54.0, (110, 190, 210), None),
        }
        base, width, height, color, rigidbody = presets[kind]
        name = self._unique_name(base)
        obj = {"id": str(uuid.uuid4()), "name": name, "x": 450.0, "y": 250.0, "w": width, "h": height, "rotation": 0.0, "color": color, "mesh_type": kind}
        if rigidbody is not None:
            obj["rigidbody"] = rigidbody
            obj["collider"] = {"type": "box"}
        if kind == "Trigger":
            obj["collider"]["is_trigger"] = True
        if kind == "Player":
            obj["scripts"] = ["Assets/Scripts/player_controller_2d.py"]
        if kind == "Camera":
            obj["component_names"] = ["Camera2D"]
            obj["camera"] = {"active": True, "zoom": 1.0}
        self._scene_snapshot.append(obj)
        self._objects_by_name[name] = obj
        self._selected_name = name
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": name})
        self._update_inspector(name)
        self._log("INFO", f"Objeto criado: {name}")

    def _create_object_at(self, kind: str, screen_x: float, screen_y: float) -> None:
        self._record_history()
        # Envia comando de criação em coordenadas de tela para a viewport.
        # A viewport traduzirá as coordenadas usando a câmera/zoom atuais e devolverá a cena atualizada.
        self._commands.put({
            "type": "create_object_at",
            "kind": kind,
            "screen_x": screen_x,
            "screen_y": screen_y
        })

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
                "rotation": [0.0, 0.0, float(snapshot.get("rotation", 0.0))],
                "rz": float(snapshot.get("rotation", 0.0)),
                "scale": [snapshot["w"], snapshot["h"], 1.0],
            }
            source.setdefault("visual", {"mesh_type": snapshot.get("mesh_type"), "color": snapshot.get("color")})
            components = source.setdefault("components", {})
            components.pop("controller", None)
            if snapshot.get("rigidbody") is not None:
                components["rigidbody"] = deepcopy(snapshot["rigidbody"])
            if snapshot.get("collider") is not None:
                collider = deepcopy(snapshot["collider"])
                collider.setdefault("width", snapshot["w"])
                collider.setdefault("height", snapshot["h"])
                components["collider"] = collider
            if snapshot.get("camera") is not None or "Camera2D" in snapshot.get("component_names", []):
                components["camera"] = deepcopy(snapshot.get("camera") or {"active": True, "zoom": 1.0})
            if snapshot.get("scripts"):
                components["scripts"] = list(dict.fromkeys(str(path) for path in snapshot["scripts"]))
            scene_objects.append(source)
        payload["objects"] = scene_objects
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self._scene_document = payload
        self._current_scene_path = path
        self.statusBar().showMessage(f"Cena salva: {filename}")
        self._log("INFO", f"Cena salva: {filename}")

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
                rotation = transform.get("rz", (transform.get("rotation") or [0.0, 0.0, 0.0])[2])
                snapshot = {"id": item.get("id", item["name"]), "name": item["name"], "x": float(position[0]), "y": float(position[1]), "w": abs(float(scale[0])), "h": abs(float(scale[1])), "rotation": float(rotation), "color": color, "mesh_type": visual.get("mesh_type")}
                if isinstance(components.get("rigidbody"), dict):
                    snapshot["rigidbody"] = deepcopy(components["rigidbody"])
                if isinstance(components.get("collider"), dict):
                    snapshot["collider"] = deepcopy(components["collider"])
                if isinstance(components.get("camera"), dict):
                    snapshot["camera"] = deepcopy(components["camera"])
                component_names = ["Camera2D"] if isinstance(components.get("camera"), dict) else []
                for component in components.get("items", []):
                    if isinstance(component, dict):
                        component_names.append(str(component.get("type") or component.get("component_type") or "Component"))
                if components.get("scripts"):
                    snapshot["scripts"] = [str(script) for script in components["scripts"]]
                    component_names.extend(f"Script: {script}" for script in components["scripts"])
                if component_names:
                    snapshot["component_names"] = component_names
                snapshots.append(snapshot)
            elif {"x", "y", "w", "h"}.issubset(item):
                snapshots.append(dict(item))
        if not snapshots and objects:
            self.statusBar().showMessage("Falha ao abrir cena: nenhum objeto compatível")
            return
        self._record_history()
        self._scene_snapshot = snapshots
        self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
        self._scene_document = payload if any("transform" in item for item in objects if isinstance(item, dict)) else None
        self._current_scene_path = Path(filename)
        self._selected_name = None
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self.statusBar().showMessage(f"Cena aberta: {filename}")
        self._log("INFO", f"Cena aberta: {filename}")

    def _connect_hierarchy_to_viewport(self) -> None:
        self.hierarchy_tree.setDragEnabled(True)
        self.hierarchy_tree.setAcceptDrops(True)
        self.hierarchy_tree.setDragDropMode(QTreeWidget.InternalMove)
        self.hierarchy_tree.itemClicked.connect(self._select_hierarchy_item)
        self.hierarchy_tree.itemDoubleClicked.connect(lambda item: self._rename_object(self._hierarchy_item_name(item)))
        self.hierarchy_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.hierarchy_tree.customContextMenuRequested.connect(self._open_hierarchy_menu)

    def _open_hierarchy_menu(self, position) -> None:
        item = self.hierarchy_tree.itemAt(position)
        item_name = self._hierarchy_item_name(item)
        if item is None or item_name not in self._objects_by_name:
            return
        menu = QMenu(self)
        rename_action = menu.addAction("Renomear")
        delete_action = menu.addAction("Excluir")
        rename_action.triggered.connect(lambda _checked=False: self._rename_object(item_name))
        delete_action.triggered.connect(lambda _checked=False: self._delete_object(item_name))
        menu.exec(self.hierarchy_tree.viewport().mapToGlobal(position))

    def _rename_object(self, old_name: str) -> None:
        new_name, accepted = QInputDialog.getText(self, "Renomear objeto", "Nome:", text=old_name)
        new_name = new_name.strip()
        if not accepted or not new_name or (new_name != old_name and new_name in self._objects_by_name):
            return
        self._record_history()
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
        self._record_history()
        self._scene_snapshot = [obj for obj in self._scene_snapshot if obj["name"] != name]
        self._objects_by_name.pop(name, None)
        if self._selected_name == name:
            self._selected_name = None
            self.inspector_name_label.setText("—")
            self.script_selector.clear()
            self.script_selector.setEnabled(False)
            self.create_script_button.setEnabled(False)
            self.edit_script_button.setEnabled(False)
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})

    def _duplicate_selected(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        duplicate = deepcopy(self._objects_by_name[self._selected_name])
        duplicate["id"] = str(uuid.uuid4())
        duplicate["name"] = self._unique_name(f"{self._selected_name}_copy")
        duplicate["x"] = float(duplicate.get("x", 0.0)) + 16.0
        duplicate["y"] = float(duplicate.get("y", 0.0)) + 16.0
        self._scene_snapshot.append(duplicate)
        self._objects_by_name[duplicate["name"]] = duplicate
        self._selected_name = duplicate["name"]
        self._refresh_hierarchy()
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": self._selected_name})
        self._update_inspector(self._selected_name)

    def _refresh_hierarchy(self) -> None:
        self.hierarchy_tree.clear()
        scene_name = self._scene_document.get("scene_name", "MainScene") if self._scene_document else "MainScene"
        root = QTreeWidgetItem(["🟢 " + str(scene_name)])
        root.setExpanded(True)
        for obj in self._scene_snapshot:
            name = str(obj["name"])
            if "player" in name.lower():
                icon = "👤 "
            elif "chao" in name.lower() or "floor" in name.lower():
                icon = "🏔️ "
            else:
                icon = "📦 "
            item = QTreeWidgetItem([icon + name])
            item.setData(0, Qt.UserRole, name)
            root.addChild(item)
        self.hierarchy_tree.addTopLevelItem(root)

    @staticmethod
    def _hierarchy_item_name(item: QTreeWidgetItem | None) -> str:
        if item is None:
            return ""
        stored_name = item.data(0, Qt.UserRole)
        if stored_name:
            return str(stored_name)
        return item.text(0).lstrip("🟢🔴🟡🔵🟣⚫⚪📁🏔️☀️☁️📷🔶💡👤📦 ").strip()

    def _connect_inspector_to_viewport(self) -> None:
        for field in self.inspector_fields.values():
            field.valueChanged.connect(lambda _value: self._send_inspector_transform())
        for field in self.physics_fields.values():
            field.toggled.connect(lambda _checked: self._send_inspector_physics())
        for field in self.collider_fields.values():
            field.valueChanged.connect(lambda _value: self._send_inspector_collider())
        self.collider_trigger_field.toggled.connect(lambda _checked: self._send_inspector_collider())

        # Conecta checkboxes de habilitação de componentes
        self.show_rigidbody_chk.toggled.connect(self._toggle_rigidbody_component)
        self.show_collider_chk.toggled.connect(self._toggle_collider_component)
        self.btn_del_rb.clicked.connect(lambda: self.show_rigidbody_chk.setChecked(False))
        self.btn_del_col.clicked.connect(lambda: self.show_collider_chk.setChecked(False))

    def _toggle_rigidbody_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if checked:
            obj.setdefault("rigidbody", {"mass": 1.0, "gravity_scale": 1.0, "use_gravity": True, "is_kinematic": False})
        else:
            obj.pop("rigidbody", None)

        # Envia atualização completa da cena para a viewport
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)

    def _toggle_collider_component(self, checked: bool) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if checked:
            obj.setdefault("collider", {"type": "box", "is_trigger": False})
        else:
            obj.pop("collider", None)

        # Envia atualização completa da cena para a viewport
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._update_inspector(self._selected_name)

    def _open_add_component_menu(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        menu = QMenu(self)
        for label, component in (("RigidBody", "rigidbody"), ("Box Collider", "box"), ("Circle Collider", "circle"), ("Script", "script")):
            action = menu.addAction(label)
            action.triggered.connect(lambda _checked=False, value=component: self._add_component(value))
        menu.exec(self.add_component_button.mapToGlobal(self.add_component_button.rect().bottomLeft()))

    def _add_component(self, component: str) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        if component == "script":
            scripts = self._get_available_scripts()
            if not scripts:
                self.statusBar().showMessage("Nenhum script encontrado em Assets/Scripts")
                return
            
            script_names = [p.name for p in scripts]
            script_chosen, ok = QInputDialog.getItem(
                self, "Adicionar Script", "Selecione o script para adicionar:", script_names, 0, False
            )
            if ok and script_chosen:
                idx = script_names.index(script_chosen)
                self._attach_script(self._selected_name, scripts[idx])
            return
        self._record_history()
        obj = self._objects_by_name[self._selected_name]
        if component == "rigidbody":
            obj.setdefault("rigidbody", {"mass": 1.0, "gravity_scale": 1.0, "use_gravity": True, "is_kinematic": False})
        elif component in {"box", "circle"}:
            obj["collider"] = {"type": component, "is_trigger": False}
        self._commands.put({"type": "scene_snapshot", "objects": self._scene_snapshot})
        self._commands.put({"type": "select_object", "name": self._selected_name})
        self._update_inspector(self._selected_name)
        self._log("INFO", f"Componente adicionado em {self._selected_name}: {component}")

    def _send_inspector_physics(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        rigidbody = obj.get("rigidbody")
        if rigidbody is None:
            return
        self._record_history()
        rigidbody["use_gravity"] = self.physics_fields["use_gravity"].isChecked()
        rigidbody["is_kinematic"] = self.physics_fields["is_kinematic"].isChecked()
        self._commands.put({"type": "set_physics", "name": self._selected_name, "rigidbody": rigidbody})

    def _send_inspector_transform(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        self._record_history()
        for key, field in self.inspector_fields.items():
            obj[key] = float(field.value())
        self._commands.put({"type": "set_transform", "name": self._selected_name, **{k: obj[k] for k in ("x", "y", "w", "h", "rotation")}})

    def _send_inspector_collider(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        collider = obj.get("collider")
        if not isinstance(collider, dict):
            return
        self._record_history()
        collider_type = str(collider.get("type", "box")).lower()
        keys = ("radius", "offset_x", "offset_y") if collider_type == "circle" else ("width", "height", "offset_x", "offset_y")
        for key in keys:
            collider[key] = float(self.collider_fields[key].value())
        collider["is_trigger"] = self.collider_trigger_field.isChecked()
        self._commands.put({"type": "set_collider", "name": self._selected_name, "collider": deepcopy(collider)})

    def _select_hierarchy_item(self, item: QTreeWidgetItem) -> None:
        name = self._hierarchy_item_name(item)
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
            for key in ("x", "y", "w", "h", "rotation"):
                self.inspector_fields[key].setValue(float(obj[key]))
            rigidbody = obj.get("rigidbody")
            self.show_rigidbody_chk.setChecked(rigidbody is not None)
            for key, field in self.physics_fields.items():
                field.setEnabled(rigidbody is not None)
                field.setChecked(bool((rigidbody or {}).get(key, False)))
            collider = obj.get("collider") if isinstance(obj.get("collider"), dict) else None
            self.show_collider_chk.setChecked(collider is not None)
            collider_type = str((collider or {}).get("type", "box")).lower()
            collider_defaults = {
                "width": float(obj["w"]), "height": float(obj["h"]),
                "radius": min(float(obj["w"]), float(obj["h"])) / 2.0,
                "offset_x": 0.0, "offset_y": 0.0,
            }
            for key, field in self.collider_fields.items():
                relevant = collider is not None and (key not in ("width", "height") or collider_type == "box") and (key != "radius" or collider_type == "circle")
                field.setEnabled(relevant)
                field.setValue(float((collider or {}).get(key, collider_defaults[key])))
            self.collider_trigger_field.setEnabled(collider is not None)
            self.collider_trigger_field.setChecked(bool((collider or {}).get("is_trigger", False)))
            # Limpa todos os widgets de scripts criados anteriormente
            for h_w, b_w in self.script_containers:
                self.inspector_layout.removeWidget(h_w)
                self.inspector_layout.removeWidget(b_w)
                h_w.deleteLater()
                b_w.deleteLater()
            self.script_containers.clear()
            
            scripts_list = obj.get("scripts", [])
            for s_path in scripts_list:
                s_name = Path(s_path).name
                
                # Cria cabeçalho dinâmico para o script: "Player (Script)" ou "Nome (Script)"
                from PySide6.QtWidgets import QToolButton, QFrame
                h_widget = QWidget()
                h_widget.setStyleSheet("background-color: #242424; border-radius: 3px; margin-top: 10px; border-bottom: 1px solid #2b2b2b;")
                h_lay = QHBoxLayout(h_widget)
                h_lay.setContentsMargins(6, 4, 6, 4)
                
                title_text = s_name.removesuffix(".py").capitalize()
                lbl_title = QLabel(f"∨  📄 {title_text} (Script)")
                lbl_title.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 11px;")
                h_lay.addWidget(lbl_title)
                h_lay.addStretch()
                
                # Botões de controle encolher e fechar
                btn_collapse = QToolButton()
                btn_collapse.setText("▼")
                btn_collapse.setFixedSize(18, 18)
                btn_collapse.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")
                h_lay.addWidget(btn_collapse)
                
                btn_del = QToolButton()
                btn_del.setText("✕")
                btn_del.setFixedSize(18, 18)
                btn_del.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")
                btn_del.clicked.connect(lambda checked=False, p=s_path: self._remove_single_script(p))
                h_lay.addWidget(btn_del)
                
                # Corpo do script (Exposição de variáveis/propriedades igual ao transform/collider/screenshot)
                b_widget = QWidget()
                b_lay = QFormLayout(b_widget)
                b_lay.setContentsMargins(4, 4, 4, 4)
                b_lay.setSpacing(6)
                b_lay.setLabelAlignment(Qt.AlignLeft)
                b_lay.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
                
                btn_collapse.clicked.connect(lambda checked=False, target=b_widget: target.setVisible(not target.isVisible()))
                
                # Propriedade 1: Combobox para selecionar/alterar o script deste componente
                script_sel_combo = QComboBox()
                script_sel_combo.setObjectName("InspectorScriptSelector")
                script_sel_combo.setStyleSheet("background-color: #242424; color: #e0e0e0; font-size: 11px;")
                script_sel_combo.setFixedHeight(22)
                
                # Popula combobox com todos os scripts disponíveis
                available = self._get_available_scripts()
                for p in available:
                    rel_p = str(p.relative_to(Path.cwd())).replace("\\", "/")
                    script_sel_combo.addItem(p.name, rel_p)
                
                # Seleciona o script atualmente ativo neste componente
                current_rel = str(Path(s_path).relative_to(Path.cwd())).replace("\\", "/") if not Path(s_path).is_absolute() else s_path
                idx_found = script_sel_combo.findData(current_rel)
                if idx_found >= 0:
                    script_sel_combo.setCurrentIndex(idx_found)
                else:
                    # Tenta busca flexível por nome caso o path do snapshot seja absoluto ou relativo alternativo
                    idx_found = script_sel_combo.findText(Path(s_path).name)
                    if idx_found >= 0:
                        script_sel_combo.setCurrentIndex(idx_found)
                
                # Conecta mudança do combobox para trocar o script anexado no objeto
                script_sel_combo.currentIndexChanged.connect(
                    lambda index, old_p=s_path, combo=script_sel_combo: self._change_attached_script(old_p, combo.itemData(index))
                )
                
                lbl_key = QLabel("Script")
                lbl_key.setStyleSheet("color: #aaaaaa; font-size: 11px;")
                lbl_key.setFixedWidth(50)
                b_lay.addRow(lbl_key, script_sel_combo)
                
                # Botões de Ação: Criar Script e Editar Script expostos logo abaixo da combobox
                actions_panel = QWidget()
                act_lay = QHBoxLayout(actions_panel)
                act_lay.setContentsMargins(50, 0, 0, 0) # Alinha sob a combobox
                act_lay.setSpacing(6)
                
                btn_create = QPushButton("Criar")
                btn_create.setFixedHeight(20)
                btn_create.setStyleSheet("font-size: 10px; background-color: #2b2b2b; color: #ffffff; border: 1px solid #444;")
                btn_create.clicked.connect(self._create_script_asset)
                
                btn_edit = QPushButton("Editar")
                btn_edit.setFixedHeight(20)
                btn_edit.setStyleSheet("font-size: 10px; background-color: #2b2b2b; color: #ffffff; border: 1px solid #444;")
                btn_edit.clicked.connect(lambda checked=False, p_edit=s_path: self._edit_script_path(Path(p_edit)))
                
                act_lay.addWidget(btn_create)
                act_lay.addWidget(btn_edit)
                b_lay.addRow("", actions_panel)
                
                # Procura configurações expostas no script para renderizar (Velocidade, Pulo, etc.)
                try:
                    full_p = Path.cwd() / s_path
                    if full_p.exists():
                        import ast
                        tree = ast.parse(full_p.read_text(encoding="utf-8"))
                        for node in tree.body:
                            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                                target = node.targets[0]
                                if isinstance(target, ast.Name) and target.id == "CONFIG" and isinstance(node.value, ast.Dict):
                                    # Extrai chaves e valores do dicionário CONFIG
                                    for k_node, v_node in zip(node.value.keys, node.value.values):
                                        if isinstance(k_node, ast.Constant) and isinstance(v_node, ast.Constant):
                                            key_name = str(k_node.value)
                                            val = v_node.value
                                            label_name = key_name.replace("_", " ").capitalize()
                                            if key_name == "speed":
                                                label_name = "Velocidade"
                                            elif key_name == "jump_force":
                                                label_name = "Pulo"
                                            
                                            # Label estilizada uniforme com largura fixa
                                            lbl_prop = QLabel(label_name)
                                            lbl_prop.setStyleSheet("color: #aaaaaa; font-size: 11px;")
                                            lbl_prop.setFixedWidth(50)
                                            
                                            if isinstance(val, (int, float)):
                                                sb = QDoubleSpinBox()
                                                sb.setObjectName("InspectorNumberField")
                                                sb.setDecimals(2)
                                                sb.setRange(-100000.0, 100000.0)
                                                sb.setValue(float(val))
                                                sb.setFixedHeight(22)
                                                # Callback para salvar alteração de propriedade no arquivo
                                                sb.valueChanged.connect(lambda val_new, p_script=s_path, k_prop=key_name: self._update_script_config_val(p_script, k_prop, val_new))
                                                b_lay.addRow(lbl_prop, sb)
                                            elif isinstance(val, bool):
                                                cb = QCheckBox()
                                                cb.setObjectName("InspectorCheckBox")
                                                cb.setChecked(val)
                                                cb.toggled.connect(lambda checked_new, p_script=s_path, k_prop=key_name: self._update_script_config_val(p_script, k_prop, checked_new))
                                                b_lay.addRow(lbl_prop, cb)
                except Exception as e:
                    self._log("WARNING", f"Erro ao ler propriedades de {s_name}: {e}")
                
                # Adiciona no layout principal logo acima do botão "Adicionar Componente"
                idx = self.inspector_layout.indexOf(self.add_component_button)
                self.inspector_layout.insertWidget(idx, h_widget)
                self.inspector_layout.insertWidget(idx + 1, b_widget)
                
                self.script_containers.append((h_widget, b_widget))
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
            elif message.get("type") == "transform_begin":
                self._drag_history_snapshot = deepcopy(self._scene_snapshot)
            elif message.get("type") == "transform_end":
                if self._drag_history_snapshot is not None and self._drag_history_snapshot != self._scene_snapshot:
                    self._record_history(self._drag_history_snapshot)
                self._drag_history_snapshot = None
            elif message.get("type") == "transform":
                obj = self._objects_by_name.get(message["name"])
                if obj is not None:
                    obj["x"] = float(message["x"])
                    obj["y"] = float(message["y"])
                    if "w" in message:
                        obj["w"] = float(message["w"])
                    if "h" in message:
                        obj["h"] = float(message["h"])
                    if "rotation" in message:
                        obj["rotation"] = float(message["rotation"])
                    if message["name"] == self._selected_name:
                        self._update_inspector(self._selected_name)
                self.statusBar().showMessage(
                    f"Viewport: {message['name']} em X={message['x']:.1f}, Y={message['y']:.1f}"
                )
            elif message.get("type") == "play_state":
                state = message["state"]
                self.toolbar_actions["Play"].setEnabled(state != "play")
                self.toolbar_actions["Pause"].setEnabled(state in {"play", "pause"})
                self.toolbar_actions["Stop"].setEnabled(state in {"play", "pause"})
                self.statusBar().showMessage(
                    {"play": "Viewport: PLAY", "pause": "Viewport: PAUSE", "edit": "Viewport: EDIT — cena restaurada"}[state]
                )
                self._log("INFO", {"play": "Play iniciado/retomado", "pause": "Play pausado", "edit": "Play finalizado; cena restaurada"}[state])
            elif message.get("type") == "scene_snapshot":
                self._scene_snapshot = [dict(item) for item in message.get("objects", [])]
                self._objects_by_name = {item["name"]: item for item in self._scene_snapshot}
                self._refresh_hierarchy()
                if self._selected_name in self._objects_by_name:
                    self._update_inspector(self._selected_name)
            elif message.get("type") == "viewport_mode":
                state = "embutida" if message.get("embedded") else "em janela separada (fallback)"
                self.statusBar().showMessage(f"Viewport {state}")
            elif message.get("type") == "script_log":
                self._log(str(message.get("level", "INFO")), str(message.get("message", "")))
            elif message.get("type") == "attach_script":
                self._attach_script(str(message.get("name", "")), Path(str(message.get("path", ""))))
            elif message.get("type") == "stats":
                self.profiler_label.setText(
                    f"FPS: {message.get('fps', 0):.0f}\n"
                    f"Objetos: {message.get('objects', 0)}\n"
                    f"Modo: {message.get('mode', 'EDIT')} / {message.get('view', 'SCENE')}\n"
                    f"Câmera: {message.get('camera', 'Editor')}\n"
                    f"Jogador: {message.get('player') or '—'}\n"
                    f"Zoom: {message.get('zoom', 1.0):.2f}"
                )

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
    try:
        from editor.premium_theme import PREMIUM_QSS
        app.setStyleSheet(PREMIUM_QSS)
    except Exception:
        pass
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
