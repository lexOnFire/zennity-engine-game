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
    QLineEdit,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QTextBrowser,
    QFileDialog,
    QMessageBox,
)

from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata import NodeDefinition, PinType
from editor.widgets.graph_editor.graph_canvas import GraphCanvas
from editor.widgets.graph_editor.inspector.graph_inspector import GraphNodeInspector


BT_NODE_GUIDE = {
    "bt.selector": {
        "name": "Seletor",
        "summary": "Tenta os filhos em ordem até encontrar um que tenha sucesso.",
        "use": "Escolhas e alternativas: perseguir o jogador; se não puder, patrulhar.",
        "tip": "Ordene as opções da mais importante para a alternativa de segurança.",
    },
    "bt.sequence": {
        "name": "Sequência",
        "summary": "Executa os filhos em ordem e falha assim que um deles falhar.",
        "use": "Planos compostos: localizar alvo, aproximar e então atacar.",
        "tip": "Coloque condições antes das ações para impedir ações inválidas.",
    },
    "bt.inverter": {
        "name": "Inversor",
        "summary": "Troca Success por Failure e Failure por Success no único filho.",
        "use": "Transformar uma condição, como “não está vendo o jogador”.",
        "tip": "Conecte somente um filho; Running continua sendo Running.",
    },
    "bt.wait": {
        "name": "Esperar",
        "summary": "Mantém o ramo em Running durante o tempo configurado.",
        "use": "Pausas de patrulha, intervalo entre ataques e tempo de reação.",
        "tip": "Use duração curta para a IA continuar responsiva.",
    },
    "bt.move_to": {
        "name": "Mover até",
        "summary": "Move o objeto até a posição-alvo usando a velocidade informada.",
        "use": "Perseguição, patrulha, retorno ao posto e aproximação de combate.",
        "tip": "Forneça uma posição válida e ajuste a velocidade ao timestep do jogo.",
    },
    "bt.repeat": {"name": "Repetir", "summary": "Repete o filho um número de vezes ou continuamente.", "use": "Rotinas, rondas e comportamentos persistentes.", "tip": "Use zero como contagem para repetição contínua."},
    "bt.cooldown": {"name": "Cooldown", "summary": "Bloqueia o filho durante um intervalo após o sucesso.", "use": "Cadência de ataque, habilidades e decisões espaçadas.", "tip": "Coloque o ataque como filho direto do Cooldown."},
    "bt.target_in_range": {"name": "Alvo no alcance", "summary": "Testa se um alvo existe dentro da distância configurada.", "use": "Visão, alcance de combate e ativação de inimigos.", "tip": "Use antes de Perseguir ou Atacar dentro de uma Sequência."},
    "bt.parameter_condition": {"name": "Condição de parâmetro", "summary": "Compara um parâmetro do Behavior Tree.", "use": "Estados como alerta, vida baixa ou chefe enfurecido.", "tip": "Operadores aceitos: ==, !=, >, >=, < e <=."},
    "bt.chase": {"name": "Perseguir alvo", "summary": "Move até um alvo mantendo uma distância de parada.", "use": "Inimigos, aliados seguidores e NPCs de escolta.", "tip": "Use uma distância de parada compatível com o alcance do ataque."},
    "bt.patrol": {"name": "Patrulhar", "summary": "Alterna continuamente entre dois pontos.", "use": "Guardas, plataformas móveis e NPCs em ronda.", "tip": "Informe os pontos como x,y no Inspector."},
    "bt.attack": {"name": "Atacar alvo", "summary": "Aplica dano ao alvo quando ele está no alcance.", "use": "Combate corpo a corpo e perigos por contato.", "tip": "Combine com Cooldown para evitar dano a cada frame."},
    "bt.play_animation": {"name": "Reproduzir animação", "summary": "Ativa um estado ou clip no Animator.", "use": "Sincronizar Idle, Walk, Attack e outras respostas visuais.", "tip": "O nome deve corresponder ao estado configurado no Animator."},
}

BT_CATEGORY_LABELS = {
    "Composite": "Composição",
    "Decorator": "Decoradores",
    "Action": "Ações",
    "Condition": "Condições",
}


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
        self._palette_category_filter = "Todas"

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
        self.btn_starter = QPushButton("⚡ Estrutura inicial", self)
        self.btn_starter.setToolTip("Adiciona os blocos essenciais deste tipo de grafo")
        self.btn_starter.clicked.connect(self.create_starter_graph)
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
        toolbar.addWidget(self.btn_starter)
        toolbar.addWidget(self.btn_zoom_fit)
        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_open)
        toolbar.addWidget(self.btn_save)
        layout.addLayout(toolbar)
        utility_bar = QHBoxLayout()
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText(
            f"Pesquisar blocos de {graph_category_filter}..."
        )
        self.search_edit.textChanged.connect(self.populate_node_palette)
        self.document_status = QLabel("Novo documento • sem alterações", self)
        self.document_status.setStyleSheet("color: #7f8ca3;")
        utility_bar.addWidget(self.search_edit, 1)
        utility_bar.addWidget(self.document_status)
        layout.addLayout(utility_bar)

        # ── Splitter Principal: Paleta | Canvas | Inspector ────────────────
        # Outer splitter: (Paleta + Canvas) | Inspector
        outer_splitter = QSplitter(Qt.Horizontal, self)

        # Inner splitter: Paleta | Canvas
        inner_splitter = QSplitter(Qt.Horizontal)

        # Paleta de Nós
        palette_panel = QWidget(inner_splitter)
        palette_layout = QVBoxLayout(palette_panel)
        palette_layout.setContentsMargins(4, 4, 4, 4)
        palette_layout.setSpacing(6)
        self.palette_category = QComboBox(palette_panel)
        self.palette_category.addItems(("Todas", "Composição", "Decoradores", "Condições", "Ações"))
        self.palette_category.currentTextChanged.connect(self._on_palette_category_changed)
        self.node_palette = QTreeWidget(palette_panel)
        self.node_palette.setHeaderLabel("Paleta de Nós")
        self.node_palette.itemDoubleClicked.connect(self._on_node_double_clicked)
        self.palette_summary = QLabel(palette_panel)
        self.palette_summary.setWordWrap(True)
        self.palette_summary.setStyleSheet("color: #7f8ca3; font-size: 10px;")
        if self.category_filter.casefold() == "behavior tree":
            palette_layout.addWidget(self.palette_category)
            self.palette_summary.setText(
                "Duplo clique adiciona um nó. Monte a árvore da esquerda para a direita."
            )
        else:
            self.palette_category.hide()
        palette_layout.addWidget(self.node_palette, 1)
        palette_layout.addWidget(self.palette_summary)
        inner_splitter.addWidget(palette_panel)

        # Canvas do Graph Framework
        self.canvas = GraphCanvas(inner_splitter)
        inner_splitter.addWidget(self.canvas)
        inner_splitter.setSizes([180, 600])

        outer_splitter.addWidget(inner_splitter)

        # Inspector lateral + ajuda contextual
        self.inspector_tabs = QTabWidget(outer_splitter)
        self.graph_inspector = GraphNodeInspector(self.inspector_tabs)
        self.graph_inspector.setMinimumWidth(200)
        self.graph_inspector.setMaximumWidth(280)
        self.help_browser = QTextBrowser(self.inspector_tabs)
        self.help_browser.setOpenExternalLinks(True)
        self.inspector_tabs.addTab(self.graph_inspector, "Propriedades")
        self.inspector_tabs.addTab(self.help_browser, "Ajuda")
        self.inspector_tabs.setMinimumWidth(240)
        self.inspector_tabs.setMaximumWidth(340)
        outer_splitter.addWidget(self.inspector_tabs)
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
        self._show_behavior_help(None)
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
            guide = BT_NODE_GUIDE.get(str(getattr(ndef, "id", "")), {})
            guide_text = " ".join(str(value) for value in guide.values()).lower()

            # Filtro por tipo de editor
            requested = self.category_filter.casefold()
            category = str(cat).casefold()
            is_matching_category = not requested or (
                category == requested or category.startswith(f"{requested}/")
            )

            if is_matching_category:
                matches_search = (
                    not query
                    or query in node_id
                    or query in name_key
                    or query in guide_text
                    or query in cat.lower()
                    or any(query in tag for tag in tags)
                )

                if matches_search:
                    category_nodes.setdefault(cat, []).append(ndef)

        visible_count = 0
        for cat_name, ndefs in sorted(category_nodes.items()):
            section = str(cat_name).split("/")[-1]
            localized_category = BT_CATEGORY_LABELS.get(section, section)
            if (
                self.category_filter.casefold() == "behavior tree"
                and self._palette_category_filter != "Todas"
                and localized_category != self._palette_category_filter
            ):
                continue
            cat_item = QTreeWidgetItem(self.node_palette, [localized_category])
            cat_item.setExpanded(True)
            for ndef in sorted(ndefs, key=lambda item: str(item.id)):
                guide = BT_NODE_GUIDE.get(str(ndef.id), {})
                display_name = guide.get("name") or getattr(ndef, "name_key", ndef.id)
                node_item = QTreeWidgetItem(cat_item, [display_name])
                node_item.setData(0, Qt.UserRole, ndef)
                node_item.setToolTip(0, guide.get("summary", str(ndef.id)))
                visible_count += 1
        if self.category_filter.casefold() == "behavior tree":
            self.node_palette.setHeaderLabel(f"Biblioteca Behavior Tree • {visible_count} nós")

    def _on_palette_category_changed(self, category: str) -> None:
        self._palette_category_filter = category
        self.populate_node_palette(self.search_edit.text())

    # ── Graph↔Inspector Sync (Item 3) ─────────────────────────────────────
    def _on_node_selected(self, node_item) -> None:
        """Relay canvas selection to the graph inspector and the outer signal."""
        self.graph_inspector.inspect_node(node_item)
        node_def = getattr(node_item, "node_def", None) if node_item is not None else None
        self._show_behavior_help(node_def)
        self.node_selected.emit(node_item)

    def _show_behavior_help(self, node_def: Any | None) -> None:
        if self.category_filter.casefold() != "behavior tree":
            self.help_browser.setHtml(
                "<h3>Ajuda do grafo</h3><p>Selecione um nó para consultar seus metadados.</p>"
            )
            return
        node_id = str(getattr(node_def, "id", ""))
        guide = BT_NODE_GUIDE.get(node_id)
        if guide is None:
            self.help_browser.setHtml(
                "<h2>Behavior Tree</h2>"
                "<p>Selecione um nó para ver como ele funciona.</p>"
                "<h3>Estados</h3><ul>"
                "<li><b>Success</b>: a tarefa terminou corretamente.</li>"
                "<li><b>Failure</b>: a tarefa não pôde ser concluída.</li>"
                "<li><b>Running</b>: a tarefa continuará no próximo frame.</li>"
                "</ul><h3>Como começar</h3>"
                "<p>Use uma Sequência para um plano ou um Seletor para alternativas. "
                "Depois conecte Ações e Decoradores.</p>"
            )
            return
        self.help_browser.setHtml(
            f"<h2>{guide['name']}</h2><code>{node_id}</code>"
            f"<h3>O que faz</h3><p>{guide['summary']}</p>"
            f"<h3>Uso em jogos</h3><p>{guide['use']}</p>"
            f"<h3>Boa prática</h3><p>{guide['tip']}</p>"
            "<p><b>Dica:</b> edite os valores na aba Propriedades e conecte "
            "as saídas na ordem em que devem ser avaliadas.</p>"
        )

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
        data = self.canvas.graph_data()
        connections = [
            {
                **edge,
                "from_node": edge.get("source_node", ""),
                "to_node": edge.get("target_node", ""),
            }
            for edge in data["edges"]
        ]
        errors = val_service.validate_graph(data["nodes"], connections)
        if errors:
            self.document_status.setText(
                f"Validação • {len(errors)} problema(s) encontrado(s)"
            )
            self.document_status.setToolTip(
                "\n".join(str(error) for error in errors)
            )
        else:
            self.document_status.setText("Validação • grafo pronto")
            self.document_status.setToolTip("")
        return errors

    def create_starter_graph(self) -> None:
        """Create a useful editable baseline for the active graph domain."""
        starters = {
            "behavior tree": ("bt.sequence", "bt.wait"),
            "dialogue": ("dialogue.speech", "dialogue.end"),
            "material": ("material.color_constant", "material.pbr_output"),
            "animation": ("animation.parameter", "animation.state"),
        }
        node_ids = starters.get(self.category_filter.casefold(), ())
        if not node_ids or self.canvas.scene.nodes:
            self.document_status.setText(
                "Estrutura inicial disponível somente em documento vazio"
            )
            return
        for index, node_id in enumerate(node_ids):
            self.canvas._spawn_pos = QPointF(80 + index * 300, 120)
            self.canvas._spawn_node(node_id)
        self.auto_layout()
        self._mark_dirty()

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
        self.document_status.setText("Novo documento • sem alterações")
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
        self.document_status.setText(f"Aberto • {self.current_path.name}")
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
        self.document_status.setText(f"Salvo • {self.current_path.name}")
        self.document_changed.emit(self.current_path)
        return True

    def _mark_dirty(self) -> None:
        self.is_dirty = True
        name = self.current_path.name if self.current_path else "novo documento"
        self.document_status.setText(f"Editando • {name}")
