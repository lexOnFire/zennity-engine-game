"""Diálogo para edição de script e gerenciamento de portas dinâmicas de nós Custom Script."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.logic.runtime.custom_script_sandbox import validate_custom_script

PORT_TYPES = ("number", "bool", "text", "object", "any")


class CustomScriptEditorDialog(QDialog):
    """Editor dedicado para scripts Python e portas de nós custom_script."""

    def __init__(self, node: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.node = node
        self.properties = node.setdefault("properties", {})
        self.node_title = str(node.get("title", "Custom Script"))

        self.setWindowTitle(f"Editar Script: {self.node_title}")
        self.resize(920, 620)
        self.setMinimumSize(640, 440)
        self.setStyleSheet(
            "QDialog { background-color: #0f121a; color: #f1f5f9; }"
            "QLabel { color: #cbd5e1; font-size: 11px; }"
            "QTableWidget { background-color: #141720; gridline-color: #1e2430; border: 1px solid #1e2430; color: #f1f5f9; border-radius: 4px; }"
            "QHeaderView::section { background-color: #1a202c; color: #94a3b8; padding: 4px; border: 1px solid #1e2430; font-weight: bold; font-size: 11px; }"
            "QLineEdit { background-color: #1a202c; border: 1px solid #2d3748; color: #f8fafc; padding: 4px; border-radius: 3px; }"
            "QComboBox { background-color: #1a202c; border: 1px solid #2d3748; color: #f8fafc; padding: 3px; border-radius: 3px; }"
            "QPushButton { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; padding: 6px 14px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #334155; border-color: #475569; }"
            "QPushButton#ApplyButton { background-color: #2563eb; border-color: #3b82f6; }"
            "QPushButton#ApplyButton:hover { background-color: #1d4ed8; }"
            "QPushButton#ValidateButton { background-color: #059669; border-color: #10b981; }"
            "QPushButton#ValidateButton:hover { background-color: #047857; }"
        )

        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel(self.node_title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")

        model_label = QLabel("Modelo:")
        model_label.setStyleSheet("font-weight: bold; color: #94a3b8;")
        self.model_combo = QComboBox()
        self.model_combo.addItem("Pure Data (Evaluator)", "pure_data")
        self.model_combo.addItem("Action (Flow in/next/failure)", "action")
        current_model = str(self.properties.get("execution_model", "pure_data")).lower()
        idx = 1 if current_model == "action" else 0
        self.model_combo.setCurrentIndex(idx)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)

        header_layout.addWidget(title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(model_label)
        header_layout.addWidget(self.model_combo)
        main_layout.addLayout(header_layout)

        # Splitter principal: Painel de Portas à Esquerda, Editor de Script à Direita
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #1e2430; width: 2px; }")

        # Painel Esquerdo: Portas Dinâmicas
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        # Inputs Table
        inputs_header = QHBoxLayout()
        inputs_label = QLabel("Portas de Entrada (Inputs)")
        inputs_label.setStyleSheet("font-weight: bold; color: #34d399;")
        add_input_btn = QPushButton("+ Input")
        add_input_btn.setFixedHeight(24)
        add_input_btn.clicked.connect(self._add_input_row)
        inputs_header.addWidget(inputs_label)
        inputs_header.addStretch(1)
        inputs_header.addWidget(add_input_btn)
        left_layout.addLayout(inputs_header)

        self.inputs_table = self._create_ports_table(is_input=True)
        left_layout.addWidget(self.inputs_table, 1)

        # Outputs Table
        outputs_header = QHBoxLayout()
        outputs_label = QLabel("Portas de Saída (Outputs)")
        outputs_label.setStyleSheet("font-weight: bold; color: #60a5fa;")
        add_output_btn = QPushButton("+ Output")
        add_output_btn.setFixedHeight(24)
        add_output_btn.clicked.connect(self._add_output_row)
        outputs_header.addWidget(outputs_label)
        outputs_header.addStretch(1)
        outputs_header.addWidget(add_output_btn)
        left_layout.addLayout(outputs_header)

        self.outputs_table = self._create_ports_table(is_input=False)
        left_layout.addWidget(self.outputs_table, 1)

        splitter.addWidget(left_panel)

        # Painel Direito: Código Python
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)

        script_label = QLabel("Código Python Restrito (ctx.get_input / ctx.set_output)")
        script_label.setStyleSheet("font-weight: bold; color: #f8fafc;")
        right_layout.addWidget(script_label)

        self.script_edit = QPlainTextEdit()
        self.script_edit.setStyleSheet(
            "QPlainTextEdit { background-color: #0b0d14; color: #38bdf8; font-family: Consolas, 'Courier New', monospace; "
            "font-size: 13px; line-height: 1.4; border: 1px solid #1e2430; border-radius: 4px; padding: 10px; selection-background-color: #1e3a8a; }"
        )
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.script_edit.setFont(font)
        right_layout.addWidget(self.script_edit, 1)

        # Status / Erro de Validação
        self.status_label = QLabel("Pronto para validação.")
        self.status_label.setStyleSheet("font-size: 11px; color: #94a3b8; font-family: Consolas, monospace;")
        right_layout.addWidget(self.status_label)

        splitter.addWidget(right_panel)
        splitter.setSizes([380, 540])
        main_layout.addWidget(splitter, 1)

        # Rodapé de Ações
        footer_layout = QHBoxLayout()
        validate_btn = QPushButton("Validar Sintaxe")
        validate_btn.setObjectName("ValidateButton")
        validate_btn.clicked.connect(self._validate_only)

        export_btn = QPushButton("Exportar como .znode...")
        export_btn.clicked.connect(self._export_as_znode)

        apply_btn = QPushButton("Aplicar e Salvar")
        apply_btn.setObjectName("ApplyButton")
        apply_btn.clicked.connect(self._apply_and_close)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)

        footer_layout.addWidget(validate_btn)
        footer_layout.addWidget(export_btn)
        footer_layout.addStretch(1)
        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(apply_btn)
        main_layout.addLayout(footer_layout)

    def _create_ports_table(self, is_input: bool) -> QTableWidget:
        table = QTableWidget()
        cols = ["Nome", "Tipo", "Default", ""] if is_input else ["Nome", "Tipo", ""]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        if is_input:
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(len(cols) - 1, QHeaderView.Fixed)
        table.setColumnWidth(len(cols) - 1, 32)
        table.verticalHeader().setVisible(False)
        return table

    def _load_data(self) -> None:
        inputs = self.properties.get("inputs", [])
        outputs = self.properties.get("outputs", [])
        script = str(self.properties.get("script", "# Exemplo:\n# a = ctx.get_input('a', 0.0)\n# ctx.set_output('result', a * 2.0)"))

        self.script_edit.setPlainText(script)

        # Preenche Inputs
        self.inputs_table.setRowCount(0)
        if isinstance(inputs, list):
            for entry in inputs:
                if isinstance(entry, Mapping):
                    self._add_input_row(
                        name=str(entry.get("name", "")),
                        ptype=str(entry.get("type", "number")),
                        default=str(entry.get("default", 0.0)),
                    )

        # Preenche Outputs
        self.outputs_table.setRowCount(0)
        if isinstance(outputs, list):
            for entry in outputs:
                if isinstance(entry, Mapping):
                    self._add_output_row(
                        name=str(entry.get("name", "")),
                        ptype=str(entry.get("type", "number")),
                    )

    def _add_input_row(self, name: str = "input_1", ptype: str = "number", default: str = "0.0") -> None:
        row = self.inputs_table.rowCount()
        self.inputs_table.insertRow(row)

        name_edit = QLineEdit(str(name))
        self.inputs_table.setCellWidget(row, 0, name_edit)

        type_combo = QComboBox()
        for t in PORT_TYPES:
            type_combo.addItem(t)
        type_combo.setCurrentText(ptype if ptype in PORT_TYPES else "number")
        self.inputs_table.setCellWidget(row, 1, type_combo)

        default_edit = QLineEdit(str(default))
        self.inputs_table.setCellWidget(row, 2, default_edit)

        remove_btn = QPushButton("✕")
        remove_btn.setStyleSheet("color: #ef4444; font-weight: bold; border: none; background: transparent;")
        remove_btn.clicked.connect(lambda _, r=row: self._remove_input_row(r))
        self.inputs_table.setCellWidget(row, 3, remove_btn)

    def _add_output_row(self, name: str = "result", ptype: str = "number") -> None:
        row = self.outputs_table.rowCount()
        self.outputs_table.insertRow(row)

        name_edit = QLineEdit(str(name))
        self.outputs_table.setCellWidget(row, 0, name_edit)

        type_combo = QComboBox()
        for t in PORT_TYPES:
            type_combo.addItem(t)
        type_combo.setCurrentText(ptype if ptype in PORT_TYPES else "number")
        self.outputs_table.setCellWidget(row, 1, type_combo)

        remove_btn = QPushButton("✕")
        remove_btn.setStyleSheet("color: #ef4444; font-weight: bold; border: none; background: transparent;")
        remove_btn.clicked.connect(lambda _, r=row: self._remove_output_row(r))
        self.outputs_table.setCellWidget(row, 2, remove_btn)

    def _remove_input_row(self, row: int) -> None:
        self.inputs_table.removeRow(row)

    def _remove_output_row(self, row: int) -> None:
        self.outputs_table.removeRow(row)

    def _collect_ports(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        inputs: list[dict[str, Any]] = []
        for r in range(self.inputs_table.rowCount()):
            name_widget = self.inputs_table.cellWidget(r, 0)
            type_widget = self.inputs_table.cellWidget(r, 1)
            default_widget = self.inputs_table.cellWidget(r, 2)
            name = name_widget.text().strip() if isinstance(name_widget, QLineEdit) else ""
            ptype = type_widget.currentText() if isinstance(type_widget, QComboBox) else "number"
            def_text = default_widget.text().strip() if isinstance(default_widget, QLineEdit) else "0.0"

            # Coerção segura de default
            def_val: Any = def_text
            if ptype == "number":
                try:
                    def_val = float(def_text) if "." in def_text else int(def_text)
                except ValueError:
                    def_val = 0.0
            elif ptype == "bool":
                def_val = def_text.lower() in ("true", "1", "yes")

            if name:
                inputs.append({"name": name, "type": ptype, "default": def_val})

        outputs: list[dict[str, Any]] = []
        for r in range(self.outputs_table.rowCount()):
            name_widget = self.outputs_table.cellWidget(r, 0)
            type_widget = self.outputs_table.cellWidget(r, 1)
            name = name_widget.text().strip() if isinstance(name_widget, QLineEdit) else ""
            ptype = type_widget.currentText() if isinstance(type_widget, QComboBox) else "number"
            if name:
                outputs.append({"name": name, "type": ptype})

        return inputs, outputs

    def _on_model_changed(self, index: int) -> None:
        model = self.model_combo.currentData()
        if model == "action":
            self.status_label.setText("Modo Action selecionado: requer fluxo 'in' e saídas 'next' / 'failure'. Use ctx.emit().")
        else:
            self.status_label.setText("Modo Pure Data selecionado: avaliado sob demanda pelo Evaluator.")

    def _validate_only(self) -> bool:
        inputs, outputs = self._collect_ports()
        declared_in = {entry["name"] for entry in inputs}
        declared_out = {entry["name"] for entry in outputs}
        source = self.script_edit.toPlainText()
        model = self.model_combo.currentData()

        valid, err = validate_custom_script(source, declared_in, declared_out, execution_model=model)
        if not valid:
            self.status_label.setText(f"Erro: {err.splitlines()[0]}")
            self.status_label.setStyleSheet("font-size: 11px; color: #ef4444; font-family: Consolas, monospace;")
            QMessageBox.warning(self, "Erro de Validação", err)
            return False

        self.status_label.setText("✓ Validação de sintaxe e portas concluída com sucesso.")
        self.status_label.setStyleSheet("font-size: 11px; color: #10b981; font-family: Consolas, monospace;")
        return True

    def _apply_and_close(self) -> None:
        if not self._validate_only():
            return

        inputs, outputs = self._collect_ports()
        source = self.script_edit.toPlainText()
        model = self.model_combo.currentData()

        # Identifica portas removidas para remoção de edges órfãs
        old_inputs = {entry.get("name") for entry in self.properties.get("inputs", []) if isinstance(entry, Mapping)}
        old_outputs = {entry.get("name") for entry in self.properties.get("outputs", []) if isinstance(entry, Mapping)}
        new_inputs = {entry["name"] for entry in inputs}
        new_outputs = {entry["name"] for entry in outputs}

        removed_inputs = old_inputs - new_inputs
        removed_outputs = old_outputs - new_outputs

        self.properties["execution_model"] = model
        self.properties["inputs"] = inputs
        self.properties["outputs"] = outputs
        self.properties["script"] = source

        # Notifica o editor para limpar edges conectadas a portas removidas
        parent_editor = getattr(self.parent(), "editor", self.parent())
        if parent_editor and hasattr(parent_editor, "graph"):
            node_id = str(self.node.get("id"))
            edges = parent_editor.graph.get("edges", [])
            cleaned_edges = [
                e for e in edges
                if not (str(e.get("to_node")) == node_id and str(e.get("to_port")) in removed_inputs)
                and not (str(e.get("from_node")) == node_id and str(e.get("from_port")) in removed_outputs)
            ]
            parent_editor.graph["edges"] = cleaned_edges
            if hasattr(parent_editor, "mark_dirty"):
                parent_editor.mark_dirty()
            if hasattr(parent_editor, "refresh_graph_layout"):
                parent_editor.refresh_graph_layout()

        self.accept()

    def _export_as_znode(self) -> None:
        """Exporta a definição atual do nó para um asset reutilizável .znode."""
        if not self._validate_only():
            return

        from PySide6.QtWidgets import QInputDialog
        from pathlib import Path
        from engine.logic.custom_node_asset import (
            CANONICAL_CUSTOM_NODE_DIR,
            is_valid_custom_node_id,
            save_custom_node_asset,
        )
        from engine.logic.custom_node_registry import get_custom_node_registry
        from engine.logic.graph_asset import NODE_DEFINITIONS

        # Solicita o node_id
        suggested_id = self.node_title.lower().replace(" ", "_")
        node_id, ok = QInputDialog.getText(
            self,
            "Exportar como Node Reutilizável",
            "Identificador técnico do nó (snake_case, ex: calculate_damage):",
            text=suggested_id,
        )
        if not ok or not node_id.strip():
            return

        node_id = node_id.strip().lower()
        if not is_valid_custom_node_id(node_id):
            QMessageBox.warning(self, "Identificador Inválido", "O node_id deve conter apenas letras minúsculas, números e sublinhados.")
            return

        if node_id in NODE_DEFINITIONS:
            QMessageBox.warning(self, "Colisão de Nome", f"'{node_id}' já é um nó built-in da engine.")
            return

        # Diretório do projeto
        parent_editor = getattr(self.parent(), "editor", self.parent())
        project_root = Path.cwd()
        if parent_editor and hasattr(parent_editor, "project_path") and parent_editor.project_path:
            project_root = Path(parent_editor.project_path)

        target_dir = project_root / CANONICAL_CUSTOM_NODE_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{node_id}.znode"

        inputs, outputs = self._collect_ports()
        source = self.script_edit.toPlainText()
        model = self.model_combo.currentData()

        asset_data = {
            "node_id": node_id,
            "title": self.node_title,
            "category": "Custom",
            "execution_model": model,
            "inputs": inputs,
            "outputs": outputs,
            "script": source,
        }

        try:
            save_custom_node_asset(target_file, asset_data)
            # Atualiza o registry global
            get_custom_node_registry(project_root).refresh()
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Nó customizado salvo com sucesso em:\n{CANONICAL_CUSTOM_NODE_DIR}/{node_id}.znode\n\nEle estará disponível na paleta sob a categoria 'Custom'.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao Exportar", f"Falha ao salvar asset: {exc}")
