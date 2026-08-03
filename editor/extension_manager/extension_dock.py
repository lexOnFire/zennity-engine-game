"""Dock do Extension Platform / Plugin Ecosystem (Cliente oficial da Extension Platform)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
)

from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.extension.metadata import ExtensionPackageDefinition, ExtensionType


class ExtensionManagerDock(QDockWidget):
    """Dock do Gerenciador do Plugin Ecosystem / Extension Platform."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🧩 Extension Platform & Plugin Ecosystem", parent)
        self.setObjectName("ExtensionManagerDock")

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        # Toolbar & Filtros
        toolbar = QHBoxLayout()
        self.combo_filter = QComboBox(self)
        self.combo_filter.addItems(["All Types", "Plugin", "Template", "Asset Pack", "Node Pack", "Theme", "Extension", "Sample Project"])
        self.combo_filter.currentTextChanged.connect(self.populate_extensions)

        self.txt_search = QLineEdit(self)
        self.txt_search.setPlaceholderText("🔍 Search extensions...")
        self.txt_search.textChanged.connect(self.populate_extensions)

        toolbar.addWidget(QLabel("Type:", self))
        toolbar.addWidget(self.combo_filter)
        toolbar.addWidget(self.txt_search)
        layout.addLayout(toolbar)

        # Lista de Extensões (TreeWidget)
        self.tree_ext = QTreeWidget(self)
        self.tree_ext.setHeaderLabels(["Extensão / Plugin", "Tipo", "Versão", "Status"])
        layout.addWidget(self.tree_ext, 1)

        self.setWidget(container)
        self.populate_extensions()

    def populate_extensions(self) -> None:
        self.tree_ext.clear()
        context = EngineContext.current()
        if not context:
            return

        meta_manager = context.services.get_optional(MetadataManager)
        if not meta_manager:
            return

        filter_type = self.combo_filter.currentText()
        search = self.txt_search.text().lower()

        ext_defs = meta_manager.get_all(ExtensionPackageDefinition)
        for ext in ext_defs:
            if filter_type != "All Types" and ext.extension_type != filter_type:
                continue
            if search and search not in ext.name.lower() and search not in ext.id.lower():
                continue

            status = "✅ Enabled" if ext.enabled else "❌ Disabled"
            item = QTreeWidgetItem(self.tree_ext, [ext.name, ext.extension_type, ext.version, status])
            item.setData(0, Qt.UserRole, ext)

        self.tree_ext.expandAll()
