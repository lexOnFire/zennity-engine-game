"""Dialog Builder Dock - ferramenta visual para criar diálogos."""

from __future__ import annotations
from typing import Any
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QFileDialog,
    QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit,
    QGroupBox
)
from PySide6.QtCore import Qt

from .csv_importer import CSVDialogueImporter


class DialogBuilderDock(QDockWidget):
    """Dock para construir diálogos visualmente."""

    def __init__(self, parent=None):
        super().__init__("Dialog Builder", parent)
        self.setObjectName("DialogBuilderDock")

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # === Toolbar ===
        toolbar_layout = QHBoxLayout()

        new_btn = QPushButton("New Dialog")
        new_btn.clicked.connect(self._new_dialog)
        toolbar_layout.addWidget(new_btn)

        load_btn = QPushButton("Load CSV")
        load_btn.clicked.connect(self._load_csv)
        toolbar_layout.addWidget(load_btn)

        save_btn = QPushButton("Save .zdialogue")
        save_btn.clicked.connect(self._save_dialog)
        toolbar_layout.addWidget(save_btn)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # === Editor de Nós ===
        nodes_group = QGroupBox("Dialogue Nodes")
        nodes_layout = QVBoxLayout()

        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(3)
        self.nodes_table.setHorizontalHeaderLabels(["Speaker", "Text", "Next Node"])
        self.nodes_table.setMaximumHeight(300)

        nodes_layout.addWidget(self.nodes_table)

        # Botões para tabela
        nodes_btn_layout = QHBoxLayout()
        add_row_btn = QPushButton("Add Node")
        add_row_btn.clicked.connect(self._add_node_row)
        nodes_btn_layout.addWidget(add_row_btn)

        del_row_btn = QPushButton("Delete Node")
        del_row_btn.clicked.connect(self._delete_node_row)
        nodes_btn_layout.addWidget(del_row_btn)

        nodes_btn_layout.addStretch()
        nodes_layout.addLayout(nodes_btn_layout)

        nodes_group.setLayout(nodes_layout)
        layout.addWidget(nodes_group)

        # === Editor de Conexões ===
        connections_group = QGroupBox("Connections (Edges)")
        connections_layout = QVBoxLayout()

        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(2)
        self.connections_table.setHorizontalHeaderLabels(["From Node", "To Node"])
        self.connections_table.setMaximumHeight(200)

        connections_layout.addWidget(self.connections_table)

        # Botões
        conn_btn_layout = QHBoxLayout()
        add_conn_btn = QPushButton("Add Connection")
        add_conn_btn.clicked.connect(self._add_connection)
        conn_btn_layout.addWidget(add_conn_btn)

        del_conn_btn = QPushButton("Delete")
        del_conn_btn.clicked.connect(self._delete_connection)
        conn_btn_layout.addWidget(del_conn_btn)

        conn_btn_layout.addStretch()
        connections_layout.addLayout(conn_btn_layout)

        connections_group.setLayout(connections_layout)
        layout.addWidget(connections_group)

        # === Preview ===
        preview_group = QGroupBox("Preview / Export")
        preview_layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setPlaceholderText("JSON preview will appear here")

        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        layout.addStretch()
        self.setWidget(main_widget)

        self.current_file = None
        self.importer = CSVDialogueImporter()

    def _new_dialog(self) -> None:
        """Cria novo diálogo vazio."""
        self.nodes_table.setRowCount(1)
        self.connections_table.setRowCount(0)
        self.current_file = None
        self._update_preview()

    def _load_csv(self) -> None:
        """Carrega diálogo de arquivo CSV."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Dialogue CSV", "", "CSV Files (*.csv)"
        )
        if not path:
            return

        # Importa CSV
        self.importer = CSVDialogueImporter()
        dialogue_json = self.importer.import_from_csv(path)

        try:
            dialogue_dict = json.loads(dialogue_json)
            self._load_from_dict(dialogue_dict)
            self.current_file = path
            QMessageBox.information(self, "Success", f"Loaded {len(self.importer.nodes)} nodes!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {e}")

    def _save_dialog(self) -> None:
        """Salva diálogo como .zdialogue."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Dialogue", "", "Dialogue Files (*.zdialogue)"
        )
        if not path:
            return

        # Constrói dict a partir da tabela
        dialogue_dict = self._build_dialogue_dict()

        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(dialogue_dict, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Success", f"Saved to {path}")
            self.current_file = path
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def _add_node_row(self) -> None:
        """Adiciona linha vazia na tabela de nós."""
        row = self.nodes_table.rowCount()
        self.nodes_table.insertRow(row)
        self._update_preview()

    def _delete_node_row(self) -> None:
        """Deleta linha selecionada."""
        row = self.nodes_table.currentRow()
        if row >= 0:
            self.nodes_table.removeRow(row)
            self._update_preview()

    def _add_connection(self) -> None:
        """Adiciona conexão entre nós."""
        row = self.connections_table.rowCount()
        self.connections_table.insertRow(row)

    def _delete_connection(self) -> None:
        """Deleta conexão selecionada."""
        row = self.connections_table.currentRow()
        if row >= 0:
            self.connections_table.removeRow(row)

    def _load_from_dict(self, dialogue_dict: dict) -> None:
        """Carrega diálogo a partir de dict."""
        nodes = dialogue_dict.get("nodes", [])
        edges = dialogue_dict.get("edges", [])

        # Carrega nós
        self.nodes_table.setRowCount(len(nodes))
        for idx, node in enumerate(nodes):
            speaker = node.get("inputs", {}).get("speaker", "")
            text = node.get("inputs", {}).get("text", "")
            self.nodes_table.setItem(idx, 0, QTableWidgetItem(speaker))
            self.nodes_table.setItem(idx, 1, QTableWidgetItem(text))

        # Carrega edges
        self.connections_table.setRowCount(len(edges))
        for idx, edge in enumerate(edges):
            from_node = edge.get("source_node", "")
            to_node = edge.get("target_node", "")
            self.connections_table.setItem(idx, 0, QTableWidgetItem(from_node))
            self.connections_table.setItem(idx, 1, QTableWidgetItem(to_node))

        self._update_preview()

    def _build_dialogue_dict(self) -> dict:
        """Constrói dict de diálogo a partir das tabelas."""
        nodes = []
        for row in range(self.nodes_table.rowCount()):
            speaker_item = self.nodes_table.item(row, 0)
            text_item = self.nodes_table.item(row, 1)

            if not text_item or not text_item.text().strip():
                continue

            node = {
                "id": f"node_{row:03d}",
                "type": "dialogue.speech",
                "inputs": {
                    "speaker": speaker_item.text() if speaker_item else "",
                    "text": text_item.text()
                }
            }
            nodes.append(node)

        edges = []
        for row in range(self.connections_table.rowCount()):
            from_item = self.connections_table.item(row, 0)
            to_item = self.connections_table.item(row, 1)

            if from_item and to_item:
                edge = {
                    "source_node": from_item.text(),
                    "source_port": "out",
                    "target_node": to_item.text(),
                    "target_port": "in"
                }
                edges.append(edge)

        return {
            "format": "zennity.generic_graph",
            "category": "Dialogue",
            "nodes": nodes,
            "edges": edges
        }

    def _update_preview(self) -> None:
        """Atualiza preview JSON."""
        dialogue_dict = self._build_dialogue_dict()
        preview_json = json.dumps(dialogue_dict, indent=2, ensure_ascii=False)
        self.preview_text.setText(preview_json[:500] + "..." if len(preview_json) > 500 else preview_json)
