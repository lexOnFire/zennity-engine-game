"""Toolbar, menu and Play Mode command coordination."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
from PySide6.QtWidgets import QToolBar

from editor.services.shortcut_service import ShortcutService


class EditorCommandController:
    """Owns editor command routing and the controls that emit those commands."""

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()
        self.shortcut_service = ShortcutService(host)

    def build_viewport_toolbar(self) -> None:
        h = self.host
        toolbar = QToolBar("Ligação com Viewport")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setAllowedAreas(Qt.TopToolBarArea)
        toolbar.setStyleSheet("QToolBar::handle { width: 0px; image: none; }")
        h.addToolBar(toolbar)
        for label, payload in (
            ("Selecionar Player", {"type": "select_object", "name": "Player"}),
            ("Mover ←", {"type": "move_selected", "dx": -16}),
            ("Mover →", {"type": "move_selected", "dx": 16}),
            ("Reset", {"type": "reset_from_interface"}),
        ):
            action = QAction(label, h)
            action.triggered.connect(
                lambda checked=False, message=payload: self.dispatch(message)
            )
            toolbar.addAction(action)

    def configure_main_menus(self) -> None:
        h = self.host
        for label in ("Novo", "Abrir", "Salvar"):
            h.editor_menus["Arquivo"].addAction(h.toolbar_actions[label])
        for label in ("Play", "Pause", "Stop"):
            h.editor_menus["Executar"].addAction(h.toolbar_actions[label])
        validate_action = h.editor_menus["Build"].addAction("Validar projeto...")
        validate_action.triggered.connect(h._project_workflow.validate_current_project)
        h.editor_menus["Build"].addSeparator()
        export_action = h.editor_menus["Build"].addAction("Exportar projeto...")
        export_action.triggered.connect(h._project_workflow.export_project)
        report_action = h.editor_menus["Build"].addAction("Último relatório...")
        report_action.setEnabled(False)
        report_action.triggered.connect(h._project_workflow.show_last_build_report)
        h._build_report_action = report_action
        h.toolbar_actions["Pause"].setEnabled(False)
        h.toolbar_actions["Stop"].setEnabled(False)
        snap_action = h.toolbar_actions["Snap: OFF"]
        snap_action.setCheckable(True)
        snap_action.toggled.connect(self.toggle_snap)

    def toggle_snap(self, enabled: bool) -> None:
        h = self.host
        h._snap_enabled = bool(enabled)
        action = h.toolbar_actions["Snap: OFF"]
        action.setText("Snap: ON" if enabled else "Snap: OFF")
        h._commands.put({
            "type": "set_snap", "enabled": bool(enabled), "size": 16.0, "angle": 15.0,
        })
        h.statusBar().showMessage("Snap ativado" if enabled else "Snap desativado")

    def connect_toolbar_actions(self) -> None:
        h = self.host
        commands = {
            "Novo": {"type": "new_scene"}, "Abrir": {"type": "load_scene"},
            "Salvar": {"type": "save_scene"}, "Play": {"type": "play"},
            "Pause": {"type": "pause"}, "Stop": {"type": "stop"},
        }
        for action in h.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            payload = commands.get(label)
            if payload is not None:
                action.triggered.connect(
                    lambda checked=False, message=payload: self.dispatch(message)
                )

    def configure_tools(self) -> None:
        h = self.host
        group = QActionGroup(h)
        group.setExclusive(True)
        shortcuts = {"select": "Q", "move": "W", "rotate": "E", "scale": "R"}
        h._tool_actions = {}
        h._tool_shortcuts = []

        def activate_tool(name: str) -> None:
            action = h._tool_actions.get(name)
            if action is not None and not action.isChecked():
                action.setChecked(True)
            h._commands.put({"type": "set_tool", "tool": name})
            h.statusBar().showMessage(f"Ferramenta ativa: {name.title()}")

        def focus_selected() -> None:
            h._commands.put({"type": "focus_selected"})
            h.statusBar().showMessage("Foco no objeto selecionado")

        def toggle_grid() -> None:
            h._commands.put({"type": "toggle_grid"})
            h.statusBar().showMessage("Grade alternada")

        for action in h.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            tool = label.lower()
            if tool not in shortcuts:
                continue
            action.setCheckable(True)
            self.shortcut_service.bind_action(action, shortcuts[tool])
            action.setChecked(tool == "select")
            group.addAction(action)
            h._tool_actions[tool] = action
            action.triggered.connect(
                lambda checked=False, name=tool: checked and activate_tool(name)
            )
        self.shortcut_service.register(
            ShortcutService.STANDARD_BINDINGS,
            {
                "tool.select": lambda: activate_tool("select"),
                "tool.move": lambda: activate_tool("move"),
                "tool.rotate": lambda: activate_tool("rotate"),
                "tool.scale": lambda: activate_tool("scale"),
                "edit.duplicate": lambda: h._selected_name is not None and h._duplicate_selected(),
                "edit.undo": h._undo,
                "edit.redo": h._redo,
                "edit.delete": lambda: h._selected_name is not None and h._delete_object(h._selected_name),
                "viewport.focus_selected": focus_selected,
                "viewport.toggle_grid": toggle_grid,
            },
        )
        h._tool_shortcuts.extend(self.shortcut_service.shortcuts)
        h._tool_action_group = group

    def dispatch(self, message: dict) -> None:
        h = self.host
        command_type = str(message.get("type", ""))
        if h._play_controller.blocks(command_type):
            h.statusBar().showMessage("Pare o Play Mode antes de alterar a cena")
            return
        if command_type == "new_scene":
            h._new_scene()
            return
        if command_type == "save_scene":
            h._save_scene_snapshot()
            return
        if command_type == "load_scene":
            h._load_scene_snapshot()
            return
        if command_type == "reset_from_interface":
            h._record_history()
            h._scene_snapshot = deepcopy(h._initial_scene_snapshot)
            h._objects_by_name = {item["name"]: item for item in h._scene_snapshot}
            h._refresh_hierarchy()
            h._scene_controller.publish_snapshot(h._scene_snapshot)
            if h._selected_name in h._objects_by_name:
                h._update_inspector(h._selected_name)
            return
        if command_type in {"play", "pause", "stop"}:
            self._dispatch_play_command(message, command_type)
            return
        if command_type == "move_selected" and h._selected_name is not None:
            h._record_history()
        h._commands.put(message)

    def _dispatch_play_command(self, message: dict, command_type: str) -> None:
        h = self.host
        plan = h._play_controller.plan(
            message,
            scene_objects=h._scene_snapshot,
            selected_name=h._selected_name,
            scene_blackboard=(h._scene_document or {}).get("blackboard", {}),
        )
        if command_type == "play":
            h._runtime_playing = True
            self.set_editing_locked(True)
            h.logic_workspace.set_play_state(True)
            h.toolbar_actions["Play"].setEnabled(False)
            h.toolbar_actions["Pause"].setEnabled(False)
            h.toolbar_actions["Stop"].setEnabled(True)
            h.viewport_tabs.setCurrentIndex(1)
            if plan.resuming:
                h._log("INFO", "Retomando Play pausado")
            else:
                logic_directory = self.project_root / "Assets" / "Logic"
                logic_assets = list(logic_directory.rglob("*.zlogic")) if logic_directory.exists() else []
                h._log(
                    "INFO",
                    f"Play solicitado com {len(logic_assets)} Logic Graph(s); scripts Python desativados",
                )
                audio_sources = plan.audio_sources or {}
                enabled_audio = [
                    name for name, audio in audio_sources.items()
                    if audio.get("autoplay") and audio.get("path")
                ]
                h._log(
                    "INFO",
                    f"Play enviando {len(audio_sources)} Audio Source(s); "
                    f"{len(enabled_audio)} configurado(s) para iniciar",
                )
        elif command_type == "stop":
            h.viewport_tabs.setCurrentIndex(0)
        for command in plan.commands:
            h._commands.put(command)

    def set_editing_locked(self, locked: bool) -> None:
        h = self.host
        h.inspector_panel.setEnabled(not locked)
        h.hierarchy_tree.setDragEnabled(not locked)
        for label in ("Desfazer", "Refazer", "Move", "Rotate", "Scale", "Snap: OFF"):
            action = h.toolbar_actions.get(label)
            if action is not None:
                action.setEnabled(not locked)
        create_menu = h.editor_menus.get("Criar")
        if create_menu is not None:
            for action in create_menu.actions():
                action.setEnabled(not locked)

    def configure_create_menu(self) -> None:
        h = self.host
        for menu_action in h.menuBar().actions():
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
                action.triggered.connect(
                    lambda checked=False, object_kind=kind: h._create_object(object_kind)
                )
            break

    def configure_edit_menu(self) -> None:
        h = self.host
        for menu_action in h.menuBar().actions():
            menu = menu_action.menu()
            if menu is None or menu.title() != "Editar":
                continue
            menu.clear()
            undo_action = h.toolbar_actions["Desfazer"]
            undo_action.setShortcut("Ctrl+Z")
            undo_action.triggered.connect(h._undo)
            menu.addAction(undo_action)
            redo_action = h.toolbar_actions["Refazer"]
            redo_action.setShortcut("Ctrl+Y")
            redo_action.triggered.connect(h._redo)
            menu.addAction(redo_action)
            menu.addSeparator()
            duplicate_action = menu.addAction("Duplicar")
            duplicate_action.setShortcut("Ctrl+D")
            duplicate_action.triggered.connect(h._duplicate_selected)
            delete_action = menu.addAction("Excluir")
            delete_action.setShortcut("Delete")
            delete_action.triggered.connect(
                lambda _checked=False: h._selected_name is not None
                and h._delete_object(h._selected_name)
            )
            break
