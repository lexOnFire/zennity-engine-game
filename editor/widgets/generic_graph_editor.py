"""Editor de Grafos Genérico (GenericGraphEditorWidget) da Zennity Engine.

Plataforma visual unificada reutilizada por:
- Behavior Tree Editor
- Dialogue Graph Editor
- Material Graph Editor
- Visual Scripting / Logic Graph
- Animator State Machine

Item 3 — Graph↔Inspector Sync:
  Conecta o Signal node_selected do GraphCanvas ao GraphNodeInspector lateral.
  A seleção de qualquer nó no canvas atualiza imediatamente o inspector.

Consome 100% o Graph Framework e o MetadataManager oficiais.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional, Any
from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QFileDialog,
    QMessageBox,
)

from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata import NodeDefinition, PinType
from editor.widgets.graph_editor.graph_canvas import GraphCanvas
from editor.widgets.graph_editor.inspector.graph_inspector import GraphNodeInspector


class GenericGraphEditorWidget(QWidget):
    """Widget de Editor de Grafos Genérico da Zennity Engine (Migrado para Editor Framework 2.0)."""

    node_added = Signal(str)
    node_selected = Signal(object)
    document_changed = Signal(object)

    def __init__(self, graph_category_filter: str = "Behavior Tree", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.category_filter = graph_category_filter
        self.current_path: Path | None = None
        self.is_dirty = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Toolbar Superior ───────────────────────────────────────────────
        toolbar = QHBoxLayout()
        self.label_title = QLabel(f"🌐 Graph Editor ({graph_category_filter})", self)
        self.label_title.setStyleSheet("font-weight: bold; color: #EEEEFF;")

        self.btn_zoom_fit = QPushButton("🔍 Fit View", self)
        self.btn_zoom_fit.clicked.connect(self._on_zoom_fit)

        self.btn_auto_layout = QPushButton("🪄 Auto Layout", self)
        self.btn_auto_layout.clicked.connect(self.auto_layout)

        self.btn_validate = QPushButton("✔️ Validate", self)
        self.btn_validate.clicked.connect(self.validate_graph)
        self.btn_new = QPushButton("＋ Novo", self)
        self.btn_open = QPushButton("📂 Abrir", self)
        self.btn_save = QPushButton("💾 Salvar", self)
        self.btn_new.clicked.connect(self.new_document)
        self.btn_open.clicked.connect(self.open_dialog)
        self.btn_save.clicked.connect(self.save)

        toolbar.addWidget(self.label_title)
        toolbar.addStretch(1)
        toolbar.addWidget(self.btn_auto_layout)
        toolbar.addWidget(self.btn_validate)
        toolbar.addWidget(self.btn_zoom_fit)
        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_open)
        toolbar.addWidget(self.btn_save)
        layout.addLayout(toolbar)

        # ── Splitter Principal: Paleta | Canvas | Inspector ────────────────
        # Outer splitter: (Paleta + Canvas) | Inspector
        outer_splitter = QSplitter(Qt.Horizontal, self)

        # Inner splitter: Paleta | Canvas
        inner_splitter = QSplitter(Qt.Horizontal)

        # Paleta de Nós (TreeWidget)
        self.node_palette = QTreeWidget(inner_splitter)
        self.node_palette.setHeaderLabel("Paleta de Nós")
        self.node_palette.itemDoubleClicked.connect(self._on_node_double_clicked)
        inner_splitter.addWidget(self.node_palette)

        # Canvas do Graph Framework
        self.canvas = GraphCanvas(inner_splitter)
        inner_splitter.addWidget(self.canvas)
        inner_splitter.setSizes([180, 600])

        outer_splitter.addWidget(inner_splitter)

        # Inspector lateral (Item 3)
        self.graph_inspector = GraphNodeInspector(outer_splitter)
        self.graph_inspector.setMinimumWidth(200)
        self.graph_inspector.setMaximumWidth(280)
        outer_splitter.addWidget(self.graph_inspector)
        outer_splitter.setSizes([780, 240])

        layout.addWidget(outer_splitter, 1)

        # ── Signals ────────────────────────────────────────────────────────
        # Canvas → Inspector: seleção de nó
        self.canvas.node_selected.connect(self._on_node_selected)
        self.canvas.asset_changed.connect(self._mark_dirty)

        # Inspector → exterior: value changes
        self.graph_inspector.value_changed.connect(
            lambda node_id, pin_id, val: self.canvas.asset_changed.emit()
        )

        self.clipboard_nodes: List[dict] = []
        self.populate_node_palette()

    # ── Node Palette ───────────────────────────────────────────────────────
    def populate_node_palette(self, search_text: str = "") -> None:
        self.node_palette.clear()
        context = EngineContext.current()
        if not context:
            return

        meta_manager = context.services.get_optional(MetadataManager)
        if not meta_manager:
            return

        node_defs = meta_manager.get_all(NodeDefinition)
        category_nodes: dict[str, List[NodeDefinition]] = {}
        query = search_text.lower().strip()

        for ndef in node_defs:
            cat = getattr(ndef, "category_key", "General") or getattr(ndef, "category", "General")
            node_id = str(getattr(ndef, "id", "")).lower()
            name_key = str(getattr(ndef, "name_key", "")).lower()
            tags = [t.lower() for t in getattr(ndef, "tags", [])]

            # Filtro por tipo de editor
            is_matching_category = (
                not self.category_filter
                or (self.category_filter.lower() in cat.lower())
                or cat.lower() in [
                    "events", "flow", "variables", "movement", "physics",
                    "math", "ai", "animation", "audio", "objects", "ui", "transform",
                ]
            )

            if is_matching_category:
                matches_search = (
                    not query
                    or query in node_id
                    or query in name_key
                    or query in cat.lower()
                    or any(query in tag for tag in tags)
                )

                if matches_search:
                    category_nodes.setdefault(cat, []).append(ndef)

        for cat_name, ndefs in category_nodes.items():
            cat_item = QTreeWidgetItem(self.node_palette, [cat_name])
            cat_item.setExpanded(True)
            for ndef in ndefs:
                display_name = getattr(ndef, "name_key", ndef.id)
                node_item = QTreeWidgetItem(cat_item, [f"{display_name} ({ndef.id})"])
                node_item.setData(0, Qt.UserRole, ndef)

    # ── Graph↔Inspector Sync (Item 3) ─────────────────────────────────────
    def _on_node_selected(self, node_item) -> None:
        """Relay canvas selection to the graph inspector and the outer signal."""
        self.graph_inspector.inspect_node(node_item)
        self.node_selected.emit(node_item)

    # ── Auto Layout ────────────────────────────────────────────────────────
    def auto_layout(self) -> None:
        """Organização automática hierárquica (Auto-Layout) dos nós no canvas."""
        items = self.canvas.scene.nodes
        x_start, y_start = 50, 50
        cols = 3
        col_width, row_height = 240, 160

        for idx, (node_id, item) in enumerate(items.items()):
            row = idx // cols
            col = idx % cols
            if hasattr(item, "setPos"):
                item.setPos(x_start + col * col_width, y_start + row * row_height)

        self.canvas.scene.refresh_connections()

    # ── Validation ─────────────────────────────────────────────────────────
    def validate_graph(self) -> List[Any]:
        """Chama o GraphValidationService oficial do EngineCore."""
        context = EngineContext.current()
        if not context:
            return []
        from engine.graph.validation_service import GraphValidationService
        val_service = context.services.get_optional(GraphValidationService)
        if not val_service:
            return []
        return val_service.validate_graph([], [])

    # ── Clipboard ──────────────────────────────────────────────────────────
    def copy_selection(self) -> None:
        self.clipboard_nodes = [{"copied": True}]

    def paste_selection(self) -> None:
        if self.clipboard_nodes:
            self.node_added.emit("pasted_node")

    # ── Internal Handlers ──────────────────────────────────────────────────
    def _on_node_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        ndef = item.data(0, Qt.UserRole)
        if isinstance(ndef, NodeDefinition):
            center = self.canvas.mapToScene(self.canvas.viewport().rect().center())
            self.canvas._spawn_pos = center
            self.canvas._spawn_node(ndef.id)
            self.node_added.emit(ndef.id)

    def _on_zoom_fit(self) -> None:
        if self.canvas.scene.nodes:
            self.canvas.fitInView(self.canvas.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    # ── Document persistence ────────────────────────────────────────────────
    def _document_extension(self) -> str:
        return {
            "behavior tree": ".zbehavior",
            "dialogue": ".zdialogue",
            "material": ".zmat",
            "animation": ".zanimator",
        }.get(self.category_filter.casefold(), ".zgraph")

    def _document_filter(self) -> str:
        extension = self._document_extension()
        return f"{self.category_filter} (*{extension})"

    def new_document(self) -> None:
        self.canvas.new_document()
        self.current_path = None
        self.is_dirty = False
        self.document_changed.emit(None)

    def graph_data(self) -> dict[str, Any]:
        data = self.canvas.graph_data()
        return {
            "format": "zennity.generic_graph",
            "version": 1,
            "category": self.category_filter,
            "nodes": data["nodes"],
            "edges": data["edges"],
        }

    def load_document(self, path: str | Path) -> bool:
        source = Path(path)
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("O documento deve conter um objeto JSON.")
            self.canvas.load_graph_data(data)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "Grafo inválido", str(exc))
            return False
        self.current_path = source.resolve()
        self.canvas.current_path = self.current_path
        self.is_dirty = False
        self.document_changed.emit(self.current_path)
        return True

    def open_dialog(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, f"Abrir {self.category_filter}", str(Path.cwd() / "Assets"),
            self._document_filter(),
        )
        if filename:
            self.load_document(filename)

    def save(self) -> bool:
        path = self.current_path
        if path is None:
            filename, _ = QFileDialog.getSaveFileName(
                self, f"Salvar {self.category_filter}",
                str(Path.cwd() / "Assets" / f"New{self.category_filter.replace(' ', '')}{self._document_extension()}"),
                self._document_filter(),
            )
            if not filename:
                return False
            path = Path(filename)
        if path.suffix.lower() != self._document_extension():
            path = path.with_suffix(self._document_extension())
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(self.graph_data(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(path)
        except OSError as exc:
            QMessageBox.warning(self, "Erro ao salvar", str(exc))
            return False
        self.current_path = path.resolve()
        self.canvas.current_path = self.current_path
        self.is_dirty = False
        self.document_changed.emit(self.current_path)
        return True

    def _mark_dirty(self) -> None:
        self.is_dirty = True
