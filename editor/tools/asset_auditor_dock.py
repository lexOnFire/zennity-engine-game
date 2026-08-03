"""Dock do Auditor de Assets e Capacidades Transversais (Asset Auditor Dock)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition
from engine.assets.capabilities import AssetCapabilitiesRegistry


class AssetAuditorDock(QDockWidget):
    """Dock para Auditoria de Assets e Validação de Capacidades Transversais."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🔍 Asset Auditor & Capabilities", parent)
        self.setObjectName("AssetAuditorDock")

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        self.tree_audit = QTreeWidget(self)
        self.tree_audit.setHeaderLabels(["Asset Type", "Extensions", "Searchable", "Previewable", "Exportable"])
        layout.addWidget(self.tree_audit, 1)

        self.setWidget(container)
        self.audit_assets()

    def audit_assets(self) -> None:
        self.tree_audit.clear()
        context = EngineContext.current()
        if not context:
            return

        meta_manager = context.services.get_optional(MetadataManager)
        if not meta_manager:
            return

        asset_defs = meta_manager.get_all(AssetTypeDefinition)
        for adef in asset_defs:
            cap = AssetCapabilitiesRegistry.get(adef.id)
            item = QTreeWidgetItem(self.tree_audit, [
                adef.id,
                ", ".join(adef.extensions),
                "YES" if cap.is_searchable else "NO",
                "YES" if cap.is_previewable else "NO",
                "YES" if cap.is_exportable else "NO",
            ])

        self.tree_audit.expandAll()
