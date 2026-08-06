"""Inspector plugin para AnimationController com visualização de parâmetros."""

from __future__ import annotations
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QSpinBox, QDoubleSpinBox,
    QCheckBox, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from editor.inspector.plugin import InspectorPlugin
from editor.runtime.command_manager import CommandManager


class AnimationControllerPlugin(InspectorPlugin):
    """Editor visual para AnimationController com parameter viewer."""

    component_type = "AnimationController"
    title = "Animation Controller"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        """Cria widget editor para AnimationController."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # === Configuração Básica ===
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()

        # Default State
        state_layout = QHBoxLayout()
        state_label = QLabel("Default State:")
        self.state_input = QLineEdit()
        self.state_input.setText(getattr(component, "default_state", "idle"))
        self.state_input.setPlaceholderText("idle")
        state_layout.addWidget(state_label)
        state_layout.addWidget(self.state_input)
        config_layout.addLayout(state_layout)

        # Blend Duration
        blend_layout = QHBoxLayout()
        blend_label = QLabel("Blend Duration:")
        self.blend_spin = QDoubleSpinBox()
        self.blend_spin.setValue(getattr(component, "blend_duration", 0.2))
        self.blend_spin.setMinimum(0.0)
        self.blend_spin.setMaximum(5.0)
        self.blend_spin.setSingleStep(0.1)
        blend_layout.addWidget(blend_label)
        blend_layout.addWidget(self.blend_spin)
        config_layout.addLayout(blend_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # === Estados ===
        states_group = QGroupBox("States")
        states_layout = QVBoxLayout()

        self.states_table = QTableWidget()
        self.states_table.setColumnCount(2)
        self.states_table.setHorizontalHeaderLabels(["State Name", "Clip Name"])
        self.states_table.setMaximumHeight(150)

        # Popula com estados existentes
        states = getattr(component, "_states", {})
        self.states_table.setRowCount(len(states))
        for idx, (state_name, clip_name) in enumerate(states.items()):
            self.states_table.setItem(idx, 0, QTableWidgetItem(state_name))
            self.states_table.setItem(idx, 1, QTableWidgetItem(clip_name))

        states_layout.addWidget(self.states_table)
        states_group.setLayout(states_layout)
        layout.addWidget(states_group)

        # === Parâmetros (Play Mode) ===
        params_group = QGroupBox("Parameters (Play Mode)")
        params_layout = QVBoxLayout()

        self.params_table = QTableWidget()
        self.params_table.setColumnCount(3)
        self.params_table.setHorizontalHeaderLabels(["Parameter", "Type", "Value"])
        self.params_table.setMaximumHeight(200)

        # Popula com parâmetros
        params = getattr(component, "_parameters", {})
        self.params_table.setRowCount(len(params))
        for idx, (param_name, value) in enumerate(params.items()):
            param_type = type(value).__name__
            self.params_table.setItem(idx, 0, QTableWidgetItem(param_name))
            self.params_table.setItem(idx, 1, QTableWidgetItem(param_type))
            self.params_table.setItem(idx, 2, QTableWidgetItem(str(value)))
            # Colore row se estiver em Play Mode
            self.params_table.item(idx, 0).setBackground(QColor(100, 150, 200, 50))

        params_layout.addWidget(self.params_table)

        # Current State
        current_layout = QHBoxLayout()
        current_label = QLabel("Current State:")
        self.current_state_label = QLabel(getattr(component, "_current_state", "none"))
        self.current_state_label.setStyleSheet("font-weight: bold; color: #00ff00;")
        current_layout.addWidget(current_label)
        current_layout.addWidget(self.current_state_label)
        current_layout.addStretch()
        params_layout.addLayout(current_layout)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # === Transições ===
        trans_group = QGroupBox("Transitions")
        trans_layout = QVBoxLayout()

        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(2)
        self.trans_table.setHorizontalHeaderLabels(["From", "To"])
        self.trans_table.setMaximumHeight(150)

        # Popula com transições
        transitions = getattr(component, "_transitions", [])
        self.trans_table.setRowCount(len(transitions))
        for idx, trans in enumerate(transitions):
            from_state = trans.get("from", "?")
            to_state = trans.get("to", "?")
            self.trans_table.setItem(idx, 0, QTableWidgetItem(from_state))
            self.trans_table.setItem(idx, 1, QTableWidgetItem(to_state))

        trans_layout.addWidget(self.trans_table)
        trans_group.setLayout(trans_layout)
        layout.addWidget(trans_group)

        layout.addStretch()

        # Conecta mudanças
        self.state_input.textChanged.connect(
            lambda text: self._set_property(component, "default_state", text, command_manager, refresh)
        )
        self.blend_spin.valueChanged.connect(
            lambda value: self._set_property(component, "blend_duration", value, command_manager, refresh)
        )

        # Store references
        self.component = component
        self.command_manager = command_manager
        self.refresh = refresh

        return widget

    def _set_property(self, component: Any, prop_name: str, value: Any, command_manager: CommandManager | None, refresh: callable | None) -> None:
        """Define propriedade com undo/redo."""
        self.set_property(component, prop_name, value, command_manager, refresh)

    def refresh_widget(self, widget: QWidget, component: Any) -> None:
        """Atualiza widget com dados em tempo real (para Play Mode)."""
        # Atualiza estado atual
        if hasattr(self, "current_state_label"):
            current = getattr(component, "_current_state", "none")
            self.current_state_label.setText(current)

        # Atualiza tabela de parâmetros
        if hasattr(self, "params_table"):
            params = getattr(component, "_parameters", {})
            self.params_table.setRowCount(len(params))
            for idx, (param_name, value) in enumerate(params.items()):
                param_type = type(value).__name__
                self.params_table.setItem(idx, 0, QTableWidgetItem(param_name))
                self.params_table.setItem(idx, 1, QTableWidgetItem(param_type))
                self.params_table.setItem(idx, 2, QTableWidgetItem(str(value)))

        # Atualiza tabela de estados
        if hasattr(self, "states_table"):
            states = getattr(component, "_states", {})
            self.states_table.setRowCount(len(states))
            for idx, (state_name, clip_name) in enumerate(states.items()):
                self.states_table.setItem(idx, 0, QTableWidgetItem(state_name))
                self.states_table.setItem(idx, 1, QTableWidgetItem(clip_name))

        # Atualiza tabela de transições
        if hasattr(self, "trans_table"):
            transitions = getattr(component, "_transitions", [])
            self.trans_table.setRowCount(len(transitions))
            for idx, trans in enumerate(transitions):
                from_state = trans.get("from", "?")
                to_state = trans.get("to", "?")
                self.trans_table.setItem(idx, 0, QTableWidgetItem(from_state))
                self.trans_table.setItem(idx, 1, QTableWidgetItem(to_state))
