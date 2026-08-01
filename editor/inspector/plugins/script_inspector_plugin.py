from __future__ import annotations
from typing import Any
from pathlib import Path
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.inspector.plugin_ui_utils import *


class ScriptInspectorPlugin(InspectorPlugin):
    component_type = "Script"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        owner_name = getattr(getattr(component, "game_object", None), "name", "Player")
        widget, body = _section(f"{owner_name} (Script)")
        field = QComboBox()
        field.setObjectName("InspectorTextField")
        field.setEditable(True)

        def refresh_scripts_list() -> None:
            current = str(getattr(component, "script_path", "") or "")
            field.blockSignals(True)
            field.clear()
            field.addItem("Nenhum")
            paths = _available_script_paths()
            if current and current not in paths:
                paths.insert(0, current)
            for path in paths:
                field.addItem(path)
            field.setCurrentText(current or "Nenhum")
            field.blockSignals(False)

        edit_button = QPushButton("Editar")
        edit_button.setObjectName("InspectorScriptEditButton")
        create_button = QPushButton("Criar")
        create_button.setObjectName("InspectorScriptCreateButton")

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(create_button)

        refresh_scripts_list()
        edit_button.setEnabled(bool(getattr(component, "script_path", "")))
        body.addWidget(_property_row("Script", field))
        body.addWidget(_property_row("", buttons))

        def set_script_path(new_value: str) -> None:
            old_value = str(getattr(component, "script_path", ""))
            if new_value == "Nenhum":
                new_value = ""
            if old_value == new_value:
                return

            def apply(value: str = new_value) -> None:
                component.script_path = value
                refresh_scripts_list()
                edit_button.setEnabled(bool(value))
                if refresh is not None:
                    refresh()

            def undo(value: str = old_value) -> None:
                component.script_path = value
                refresh_scripts_list()
                edit_button.setEnabled(bool(value))
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand("Set Script.script_path", apply, undo))

        def on_script_activated(index: int) -> None:
            new_value = field.itemText(index) if index >= 0 else field.currentText()
            set_script_path(new_value)

        def edit_current_script() -> None:
            script_path = str(getattr(component, "script_path", "") or "").strip()
            if not script_path:
                return
            path = Path(script_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

        def create_script() -> None:
            owner = getattr(component, "game_object", None)
            name = getattr(owner, "name", owner_name)
            scripts_root = Path.cwd() / "Assets" / "Scripts"
            scripts_root.mkdir(parents=True, exist_ok=True)
            base = _safe_script_name(str(name))
            path = scripts_root / f"{base}.py"
            suffix = 1
            while path.exists():
                path = scripts_root / f"{base}_{suffix}.py"
                suffix += 1
            path.write_text(_script_template(_safe_class_name(str(name))), encoding="utf-8")
            set_script_path(_project_relative(path))

        field.activated.connect(on_script_activated)
        edit_button.clicked.connect(edit_current_script)
        create_button.clicked.connect(create_script)
        widget.cb_scripts = field
        widget.btn_edit = edit_button
        widget.btn_create = create_button
        widget.refresh_scripts_list = refresh_scripts_list
        widget.on_script_activated = on_script_activated
        widget.create_script = create_script
        widget.setProperty("component_type", self.component_type)
        return widget
