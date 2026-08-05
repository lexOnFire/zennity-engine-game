"""Detailed UI composition for the modern Logic Graph workspace."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGraphicsScene, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QPushButton, QSplitter, QTabWidget, QToolButton,
    QTreeWidget, QVBoxLayout, QWidget,
)

from editor.ui.icons import editor_icon
from engine.localization import tr

from .views import LogicGraphView, LogicMiniMapView


def build_logic_graph_ui(self) -> None:
    root = QVBoxLayout(self)
    root.setContentsMargins(4, 4, 4, 4)
    root.setSpacing(4)

    self.header_widget = QWidget()
    self.header_widget.setObjectName("LogicHeader")
    self.header_widget.setStyleSheet(
        "QWidget { background-color: #0d0f17; border-bottom: 1px solid #1c2230; padding: 2px 4px; }"
        "QLabel#Breadcrumb { color: #94a3b8; font-weight: 500; font-size: 12px; }"
        "QLabel#BreadcrumbBold { color: #f8fafc; font-weight: bold; font-size: 12px; }"
    )
    title_row = QHBoxLayout(self.header_widget)
    title_row.setContentsMargins(6, 4, 6, 4)
    title_row.setSpacing(6)

    brand_logo = QLabel("❖ Zennity Engine")
    brand_logo.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px; margin-right: 8px;")
    title_row.addWidget(brand_logo)

    breadcrumb = QLabel("Projetos  ›  Plataforma 2D  ›  Personagem  ›  PlayerController  ›  ")
    breadcrumb.setObjectName("Breadcrumb")
    title_row.addWidget(breadcrumb)

    self.asset_label = QLabel("Grafo Principal")
    self.asset_label.setObjectName("BreadcrumbBold")
    title_row.addWidget(self.asset_label)

    title_row.addStretch(1)

    # Botões de ação agrupados à direita
    self.save_button = QPushButton("💾 Salvar")
    self.undo_button = QPushButton("↩ Desfazer")
    self.redo_button = QPushButton("↪ Refazer")
    self.compile_button = QPushButton("⟁ Compilar")
    self.play_button = QPushButton("▶ Play")
    self.pause_button = QPushButton("❚❚ Pausar")
    self.stop_button = QPushButton("◼ Parar")

    self.undo_button.setShortcut("Ctrl+Z")
    self.redo_button.setShortcut("Ctrl+Y")

    btn_style = (
        "QPushButton { background-color: #1a202c; color: #cbd5e1; border: 1px solid #2d3748; "
        "border-radius: 6px; padding: 5px 12px; font-size: 12px; font-weight: 600; }"
        "QPushButton:hover { background-color: #2d3748; color: #f8fafc; }"
    )
    self.save_button.setStyleSheet(btn_style)
    self.undo_button.setStyleSheet(btn_style)
    self.redo_button.setStyleSheet(btn_style)
    self.compile_button.setStyleSheet(btn_style)
    self.pause_button.setStyleSheet(btn_style)
    self.stop_button.setStyleSheet(btn_style)

    # Botão Play destacado com ciano/azul neon idêntico à imagem de referência
    self.play_button.setStyleSheet(
        "QPushButton { background-color: #06b6d4; color: #0f172a; border: none; "
        "border-radius: 6px; padding: 5px 16px; font-size: 12px; font-weight: bold; }"
        "QPushButton:hover { background-color: #22d3ee; }"
    )

    for btn in (self.save_button, self.undo_button, self.redo_button, self.compile_button, self.play_button, self.pause_button, self.stop_button):
        title_row.addWidget(btn)

    root.addWidget(self.header_widget)

    # Atributos auxiliares necessários para bindings, validação e testes do LogicGraphEditor
    self.validation_label = QLabel("Grafo limpo")
    self.debug_status_label = QLabel("● DEBUG INATIVO")
    self.new_button = QToolButton()
    self.open_button = QToolButton()
    self.save_as_button = QToolButton()
    self.new_subgraph_button = QPushButton("Novo subgrafo")
    self.demo_button = QPushButton("Abrir exemplo...")
    self.graph_enabled_check = QCheckBox("Ativo no Play")
    self.target_type = QComboBox()
    self.target_value = QLineEdit("Player")
    self.help_button = QPushButton("📖 Ajuda")
    self.fit_button = QPushButton("Enquadrar")
    self.breakpoint_button = QPushButton("● Breakpoint")
    self.continue_debug_button = QPushButton("Continuar")
    self.step_debug_button = QPushButton("Próximo nó")
    self.restart_debug_button = QPushButton("Reiniciar")
    self.connect_button = QPushButton("Conectar selecionados")
    self.delete_button = QPushButton("Excluir selecionado")

    # Compatibility placeholder for older bindings. It is not in a layout,
    # so it needs an owner to prevent Qt from creating a blank native window.
    self.toolbar_widget = QWidget(self)
    self.toolbar_widget.setObjectName("LogicToolbar")
    self.toolbar_widget.hide()  # Toolbar secundária oculta para manter o visual limpo da casca

    self.category_widget = QWidget()
    self.category_widget.setObjectName("LogicCategories")
    categories = QHBoxLayout(self.category_widget)
    categories.setContentsMargins(4, 4, 4, 4)
    categories.setSpacing(6)
    categories.addWidget(QLabel("Categoria"))
    self.category_combo = QComboBox()
    self.category_combo.addItem(tr("graph.categories.movement", "Movimento"), "Movement")
    self.category_combo.addItem(tr("graph.categories.position", "Posição"), "Position")
    self.category_combo.addItem(tr("graph.categories.action", "Ação"), "Action")
    self.category_combo.addItem(tr("graph.categories.logic", "Lógica"), "Logic")
    self.category_combo.addItem(tr("graph.categories.condition", "Condição"), "Condition")
    self.category_combo.addItem(tr("graph.categories.events", "Eventos"), "Events")
    self.category_combo.addItem(tr("graph.categories.objects", "Objetos"), "Objects")
    self.category_combo.addItem(tr("graph.categories.variables", "Variáveis"), "Variables")
    self.category_combo.addItem(tr("graph.categories.math", "Matemática"), "Math")
    self.category_combo.addItem(tr("graph.categories.text", "Texto"), "Text")
    self.category_combo.addItem(tr("graph.categories.subgraphs", "Subgrafos"), "Subgraphs")
    self.category_combo.addItem(tr("graph.categories.all", "Todos"), "All")
    self.category_combo.setMinimumWidth(150)
    self.category_combo.setToolTip("Filtra a biblioteca de blocos por categoria")
    categories.addWidget(self.category_combo)
    self.add_group_button = QPushButton("+ Grupo")
    self.add_comment_button = QPushButton("+ Comentário")
    self.organize_button = QPushButton("Organizar grafo")
    self.align_button = QPushButton("Alinhar")
    self.distribute_button = QPushButton("Distribuir")
    categories.addWidget(self.add_group_button)
    categories.addWidget(self.add_comment_button)
    categories.addWidget(self.organize_button)
    categories.addWidget(self.align_button)
    categories.addWidget(self.distribute_button)
    categories.addStretch(1)
    root.addWidget(self.category_widget)

    self.content_splitter = QSplitter(Qt.Horizontal)
    self.content_splitter.setObjectName("LogicContentSplitter")
    self.content_splitter.setChildrenCollapsible(False)

    palette_panel = QFrame()
    palette_panel.setObjectName("LogicPalettePanel")
    palette_panel.setStyleSheet(
        "QFrame#LogicPalettePanel { background-color: #141720; border-right: 1px solid #1e2430; }"
        "QLineEdit { background-color: #1a1e2a; color: #f1f5f9; border: 1px solid #282f42; border-radius: 6px; padding: 6px 10px; font-size: 12px; }"
        "QLineEdit:focus { border: 1px solid #3b82f6; }"
        "QListWidget#LogicNodePalette { background-color: #141720; border: none; outline: none; }"
        "QTabWidget::pane { border: none; background: transparent; }"
        "QTabBar::tab { background: #181c28; color: #94a3b8; padding: 6px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; font-size: 11px; font-weight: bold; }"
        "QTabBar::tab:selected { background: #232a3b; color: #f8fafc; border-bottom: 2px solid #3b82f6; }"
    )

    # Layout horizontal dividindo o Rail Vertical da Biblioteca
    outer_palette_layout = QHBoxLayout(palette_panel)
    outer_palette_layout.setContentsMargins(0, 0, 0, 0)
    outer_palette_layout.setSpacing(0)

    # Rail vertical de navegação (Graph, Variables, Events, Components, Debug)
    nav_rail = QFrame()
    nav_rail.setObjectName("LogicNavRail")
    nav_rail.setFixedWidth(58)
    nav_rail.setStyleSheet(
        "QFrame { background-color: #0f121a; border-right: 1px solid #1e2430; }"
        "QToolButton { background: transparent; color: #94a3b8; border: none; font-size: 10px; font-weight: bold; border-left: 3px solid transparent; }"
        "QToolButton:hover { color: #f1f5f9; background-color: #1a202c; }"
        "QToolButton:checked { color: #3b82f6; background-color: #1c2436; border-left: 3px solid #3b82f6; }"
    )
    rail_layout = QVBoxLayout(nav_rail)
    rail_layout.setContentsMargins(0, 8, 0, 8)
    rail_layout.setSpacing(12)

    self.rail_buttons = {}
    for name, icon_str, tab_index in (
        ("Graph", "🌐", 0),
        ("Variables", "{x}", 3),
        ("Events", "⚡", 0),
        ("Components", "📦", 0),
        ("Debug", "🪲", 1),
    ):
        btn = QToolButton()
        btn.setText(f"{icon_str}\n{name}")
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setCheckable(True)
        btn.setObjectName("RailButton")
        btn.setFixedWidth(56)
        btn.setFixedHeight(58)
        if name == "Graph":
            btn.setChecked(True)
        rail_layout.addWidget(btn)
        self.rail_buttons[name] = btn

    rail_layout.addStretch(1)
    outer_palette_layout.addWidget(nav_rail)

    # Conteúdo da biblioteca de nós
    library_content = QWidget()
    palette_layout = QVBoxLayout(library_content)
    palette_layout.setContentsMargins(8, 8, 8, 8)

    self.library_tabs = QTabWidget()
    self.library_tabs.setObjectName("LogicLibraryTabs")
    self.library_tabs.setUsesScrollButtons(False)
    self.library_tabs.tabBar().setExpanding(True)
    palette_layout.addWidget(self.library_tabs, 1)

    # Conectar botões do rail às abas da biblioteca
    def _switch_rail_tab(target_index: int, clicked_name: str) -> None:
        self.library_tabs.setCurrentIndex(target_index)
        for name, btn in self.rail_buttons.items():
            btn.setChecked(name == clicked_name)

    self.rail_buttons["Graph"].clicked.connect(lambda: _switch_rail_tab(0, "Graph"))
    self.rail_buttons["Variables"].clicked.connect(lambda: _switch_rail_tab(3, "Variables"))
    self.rail_buttons["Events"].clicked.connect(lambda: _switch_rail_tab(0, "Events"))
    self.rail_buttons["Components"].clicked.connect(lambda: _switch_rail_tab(0, "Components"))
    self.rail_buttons["Debug"].clicked.connect(lambda: _switch_rail_tab(1, "Debug"))

    blocks_page = QWidget()
    blocks_layout = QVBoxLayout(blocks_page)
    blocks_layout.setContentsMargins(4, 6, 4, 6)
    blocks_layout.setSpacing(6)

    # Header da biblioteca
    lib_header = QLabel("Biblioteca de Nós")
    lib_header.setStyleSheet("font-weight: bold; font-size: 13px; color: #f1f5f9; padding-bottom: 2px;")
    blocks_layout.addWidget(lib_header)

    self.node_search = QLineEdit()
    self.node_search.setObjectName("NodeSearch")
    self.node_search.setPlaceholderText("Buscar nós...")
    self.node_search.setClearButtonEnabled(True)
    blocks_layout.addWidget(self.node_search)

    self.palette = QListWidget()
    self.palette.setObjectName("LogicNodePalette")
    self.palette.setToolTip("Duplo clique para adicionar um nó")
    blocks_layout.addWidget(self.palette, 1)

    self.palette_count = QLabel()
    self.palette_count.setObjectName("PanelHint")
    self.palette_count.setStyleSheet("color: #64748b; font-size: 11px;")
    blocks_layout.addWidget(self.palette_count)

    self.library_tabs.addTab(blocks_page, "Blocos")

    recipes_page = QWidget()
    recipes_layout = QVBoxLayout(recipes_page)
    recipes_layout.setContentsMargins(5, 6, 5, 6)
    recipes_layout.setSpacing(6)
    self.recipe_topic_label = QLabel("Receitas de Movimento")
    self.recipe_topic_label.setObjectName("PanelSectionTitle")
    recipes_layout.addWidget(self.recipe_topic_label)
    self.recipe_search = QLineEdit()
    self.recipe_search.setPlaceholderText("O que você quer fazer? ex.: mover sozinho")
    self.recipe_search.setClearButtonEnabled(True)
    recipes_layout.addWidget(self.recipe_search)
    self.recipe_list = QListWidget()
    self.recipe_list.setToolTip("Escolha uma lógica pronta para aprender e inserir")
    recipes_layout.addWidget(self.recipe_list, 1)
    self.recipe_summary = QLabel("Escolha uma receita para ver como ela funciona.")
    self.recipe_summary.setObjectName("PanelHint")
    self.recipe_summary.setWordWrap(True)
    recipes_layout.addWidget(self.recipe_summary)
    self.recipe_apply_button = QPushButton("Inserir receita no grafo")
    self.recipe_apply_button.setProperty("uiRole", "primary")
    self.recipe_apply_button.setEnabled(False)
    recipes_layout.addWidget(self.recipe_apply_button)
    self.library_tabs.addTab(recipes_page, "Receitas")

    subgraphs_page = QWidget()
    subgraphs_layout = QVBoxLayout(subgraphs_page)
    subgraphs_layout.setContentsMargins(5, 6, 5, 6)
    subgraphs_layout.setSpacing(6)
    self.subgraph_list = QListWidget()
    self.subgraph_list.setToolTip("Duplo clique adiciona uma chamada ao subgrafo")
    subgraphs_layout.addWidget(self.subgraph_list, 1)
    subgraph_hint = QLabel("Funções visuais reutilizáveis salvas em Assets/Logic.")
    subgraph_hint.setObjectName("PanelHint")
    subgraph_hint.setWordWrap(True)
    subgraphs_layout.addWidget(subgraph_hint)
    self.library_tabs.addTab(subgraphs_page, "Subgrafos")

    data_page = QWidget()
    data_layout = QVBoxLayout(data_page)
    data_layout.setContentsMargins(5, 6, 5, 6)
    data_layout.setSpacing(6)
    self.blackboard_tree = QTreeWidget()
    self.blackboard_tree.setHeaderLabels(["Nome", "Tipo", "Escopo"])
    data_layout.addWidget(self.blackboard_tree, 1)
    self.blackboard_name_edit = QLineEdit()
    self.blackboard_name_edit.setPlaceholderText("nome_da_variável")
    data_layout.addWidget(self.blackboard_name_edit)
    blackboard_options = QHBoxLayout()
    self.blackboard_type_combo = QComboBox()
    for label, value in (("Número", "number"), ("Booleano", "bool"), ("Texto", "text"), ("Objeto", "object")):
        self.blackboard_type_combo.addItem(label, value)
    self.blackboard_scope_combo = QComboBox()
    for label, value in (("Objeto", "object"), ("Cena", "scene"), ("Projeto", "project")):
        self.blackboard_scope_combo.addItem(label, value)
    blackboard_options.addWidget(self.blackboard_type_combo)
    blackboard_options.addWidget(self.blackboard_scope_combo)
    data_layout.addLayout(blackboard_options)
    self.blackboard_default_edit = QLineEdit("0")
    self.blackboard_default_edit.setPlaceholderText("Valor inicial")
    data_layout.addWidget(self.blackboard_default_edit)
    blackboard_edit_actions = QHBoxLayout()
    self.blackboard_save_button = QPushButton("Adicionar")
    self.blackboard_remove_button = QPushButton("Excluir")
    blackboard_edit_actions.addWidget(self.blackboard_save_button)
    blackboard_edit_actions.addWidget(self.blackboard_remove_button)
    data_layout.addLayout(blackboard_edit_actions)
    blackboard_node_actions = QHBoxLayout()
    self.blackboard_get_button = QPushButton("Ler")
    self.blackboard_set_button = QPushButton("Definir")
    blackboard_node_actions.addWidget(self.blackboard_get_button)
    blackboard_node_actions.addWidget(self.blackboard_set_button)
    data_layout.addLayout(blackboard_node_actions)
    data_hint = QLabel("Variáveis organizadas por objeto, cena ou projeto.")
    data_hint.setObjectName("PanelHint")
    data_hint.setWordWrap(True)
    data_layout.addWidget(data_hint)
    self.library_tabs.addTab(data_page, "Dados")

    outer_palette_layout.addWidget(library_content, 1)
    palette_panel.setMinimumWidth(300)
    self.content_splitter.addWidget(palette_panel)

    self.scene = QGraphicsScene(self)
    self.scene.setSceneRect(-2000.0, -1400.0, 4000.0, 2800.0)
    canvas_splitter = QSplitter(Qt.Vertical)
    canvas_splitter.setChildrenCollapsible(False)

    canvas_panel = QWidget()
    canvas_layout = QVBoxLayout(canvas_panel)
    canvas_layout.setContentsMargins(0, 0, 0, 0)
    canvas_layout.setSpacing(0)

    # Barra de Abas de Grafos
    graph_tabs_bar = QWidget()
    graph_tabs_bar.setStyleSheet(
        "QWidget { background-color: #0f121a; border-bottom: 1px solid #1e2430; }"
        "QToolButton { background-color: #1a202c; color: #f8fafc; border: 1px solid #2d3748; "
        "border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; padding: 4px 12px; font-weight: bold; font-size: 11px; }"
        "QToolButton#AddTab { background-color: transparent; border: none; color: #94a3b8; font-size: 14px; }"
    )
    gt_layout = QHBoxLayout(graph_tabs_bar)
    gt_layout.setContentsMargins(6, 4, 6, 0)
    gt_layout.setSpacing(4)

    active_graph_tab = QToolButton()
    active_graph_tab.setText("Grafo Principal   ✕")
    add_tab_btn = QToolButton()
    add_tab_btn.setObjectName("AddTab")
    add_tab_btn.setText("＋")

    gt_layout.addWidget(active_graph_tab)
    gt_layout.addWidget(add_tab_btn)
    gt_layout.addStretch(1)

    canvas_layout.addWidget(graph_tabs_bar)
    self.view = LogicGraphView(self.scene, self)
    canvas_layout.addWidget(self.view, 1)
    minimap_row = QHBoxLayout()
    minimap_row.addStretch(1)
    self.minimap = LogicMiniMapView(self.scene, self)
    minimap_row.addWidget(self.minimap)
    canvas_layout.addLayout(minimap_row)
    canvas_splitter.addWidget(canvas_panel)
    
    self.center_vertical_splitter = QSplitter(Qt.Vertical)
    self.center_vertical_splitter.setObjectName("LogicCenterVerticalSplitter")
    self.center_vertical_splitter.setChildrenCollapsible(False)
    self.center_vertical_splitter.addWidget(canvas_splitter)
    
    self.content_splitter.addWidget(self.center_vertical_splitter)

    right_panel = QSplitter(Qt.Vertical)
    right_panel.setObjectName("LogicRightSplitter")

    # 1. Painel Superior Direito — Mini Viewport — Play Mode
    mini_viewport_frame = QFrame()
    mini_viewport_frame.setStyleSheet("QFrame { background-color: #0f121a; border-left: 1px solid #1e2430; }")
    mv_layout = QVBoxLayout(mini_viewport_frame)
    mv_layout.setContentsMargins(3, 3, 3, 3)
    mv_layout.setSpacing(2)

    mv_header = QHBoxLayout()
    self.mini_viewport_title = QLabel("● Mini Viewport — Editor")
    self.mini_viewport_title.setStyleSheet("color: #60a5fa; font-weight: bold; font-size: 11px;")
    self.camera_combo = QComboBox()
    self.camera_combo.addItems(("Câmera Principal", "Câmera do Editor"))
    self.camera_combo.setStyleSheet("QComboBox { font-size: 10px; padding: 2px 6px; }")
    self.audio_preview_button = QToolButton()
    self.audio_preview_button.setText("🔊")
    self.audio_preview_button.setCheckable(True)
    self.audio_preview_button.setChecked(True)
    self.audio_preview_button.setToolTip("Ativar overlays de áudio")
    self.fullscreen_viewport_button = QToolButton()
    self.fullscreen_viewport_button.setText("⤢")
    self.fullscreen_viewport_button.setToolTip("Expandir ou restaurar a mini viewport")
    self.fps_badge = QLabel("— FPS")
    self.fps_badge.setStyleSheet("background-color: #16231a; color: #22c55e; font-weight: bold; font-size: 10px; border-radius: 3px; padding: 2px 6px;")

    mv_header.addWidget(self.mini_viewport_title)
    mv_header.addStretch(1)
    mv_header.addWidget(self.camera_combo)
    mv_header.addWidget(self.audio_preview_button)
    mv_header.addWidget(self.fullscreen_viewport_button)
    mv_header.addWidget(self.fps_badge)
    mv_layout.addLayout(mv_header)

    from editor.visual_scripting.mini_live_viewport import MiniLiveViewportWidget, ViewportMode
    self.mini_live_viewport = MiniLiveViewportWidget(mini_viewport_frame)
    self.mini_live_viewport.external_fps_label = self.fps_badge
    self.mini_live_viewport.set_mode(ViewportMode.EDITOR)
    mv_layout.addWidget(self.mini_live_viewport, 1)

    self.camera_combo.currentIndexChanged.connect(
        lambda index: self.mini_live_viewport.camera_selector.setCurrentText(
            "Main Camera" if index == 0 else "Editor Camera"
        )
    )
    self.audio_preview_button.toggled.connect(
        lambda enabled: (
            setattr(self.mini_live_viewport.unified_viewport, "show_audio", enabled),
            self.mini_live_viewport.unified_viewport.update(),
        )
    )

    right_panel.addWidget(mini_viewport_frame)

    # 2. Painel Inferior Direito — Abas de Propriedades do Nó & Ajuda
    right_tabs = QTabWidget()
    right_tabs.setObjectName("LogicRightTabs")

    properties_panel = QFrame()
    properties_panel.setObjectName("LogicPropertiesPanel")
    properties_layout = QVBoxLayout(properties_panel)
    properties_layout.setContentsMargins(6, 6, 6, 6)
    properties_layout.setSpacing(4)

    prop_header = QHBoxLayout()
    properties_title = QLabel("PROPRIEDADES DO NÓ")
    properties_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #94a3b8; letter-spacing: 0.5px;")
    self.validation_badge = QLabel("Sem seleção")
    self.validation_badge.setStyleSheet("color: #64748b; font-weight: bold; font-size: 11px;")
    prop_header.addWidget(properties_title)
    prop_header.addStretch(1)
    prop_header.addWidget(self.validation_badge)
    properties_layout.addLayout(prop_header)

    self.selected_label = QLabel("Nenhum nó selecionado")
    self.selected_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc; padding: 2px 0;")
    properties_layout.addWidget(self.selected_label)

    # Tabela de Propriedades principal (espaçosa e limpa)
    self.property_tree = QTreeWidget()
    self.property_tree.setObjectName("LogicPropertyTree")
    self.property_tree.setHeaderLabels(["Propriedade", "Valor"])
    self.property_tree.setColumnWidth(0, 160)
    self.property_tree.setStyleSheet(
        "QTreeWidget { background: #141720; border: 1px solid #1e2430; border-radius: 6px; color: #cbd5e1; font-size: 12px; }"
        "QHeaderView::section { background: #181c28; color: #94a3b8; font-weight: bold; font-size: 11px; border: none; padding: 6px 8px; }"
        "QTreeWidget::item { min-height: 28px; padding: 4px 8px; margin: 2px 0px; border-bottom: 1px solid #1e2430; }"
    )
    properties_layout.addWidget(self.property_tree, 1)

    self.property_asset_button = QPushButton("Selecionar asset do projeto...")
    self.property_asset_button.hide()
    properties_layout.addWidget(self.property_asset_button)
    self.property_color_button = QPushButton("Escolher cor...")
    self.property_color_button.hide()
    properties_layout.addWidget(self.property_color_button)

    self.breakpoint_condition_label = QLabel("CONDIÇÃO DO BREAKPOINT")
    self.breakpoint_condition_edit = QLineEdit()
    self.breakpoint_condition_edit.setPlaceholderText("Ex.: vida <= 0 ou grounded == true")
    self.runtime_values_title = QLabel("VALORES EM EXECUÇÃO")
    self.runtime_values_tree = QTreeWidget()
    self.runtime_values_tree.setHeaderLabels(["Expressão", "Valor"])
    self.watch_values_tree = QTreeWidget()
    self.watch_values_tree.setHeaderLabels(["OBSERVADORES", "Valor"])
    self.watch_expression_edit = QLineEdit()
    self.watch_expression_edit.setPlaceholderText("vida, velocidade, grounded...")
    self.add_watch_button = QPushButton("Adicionar observador")
    self.remove_watch_button = QPushButton("Remover")

    right_tabs.addTab(properties_panel, tr("editor.tabs.properties", "Propriedades"))
    debug_panel = QWidget()
    debug_layout = QVBoxLayout(debug_panel)
    debug_layout.setContentsMargins(10, 10, 10, 10)
    debug_layout.addWidget(self.breakpoint_condition_label)
    debug_layout.addWidget(self.breakpoint_condition_edit)
    debug_layout.addWidget(self.runtime_values_title)
    debug_layout.addWidget(self.runtime_values_tree, 1)
    debug_layout.addWidget(self.watch_values_tree, 1)
    debug_watch_actions = QHBoxLayout()
    debug_watch_actions.addWidget(self.watch_expression_edit, 1)
    debug_watch_actions.addWidget(self.add_watch_button)
    debug_watch_actions.addWidget(self.remove_watch_button)
    debug_layout.addLayout(debug_watch_actions)
    debug_layout.setContentsMargins(6, 6, 6, 6)
    right_tabs.addTab(debug_panel, "Depuração")
    from .help_dock import LogicHelpDock
    self.help_dock = LogicHelpDock()
    right_tabs.addTab(self.help_dock, tr("editor.tabs.help", "Ajuda"))

    right_panel.addWidget(right_tabs)
    right_panel.setSizes([240, 460])

    self._mini_viewport_expanded = False
    def _toggle_mini_viewport() -> None:
        self._mini_viewport_expanded = not self._mini_viewport_expanded
        right_panel.setSizes(
            [700, 0] if self._mini_viewport_expanded else [340, 360]
        )
        self.fullscreen_viewport_button.setText(
            "⤡" if self._mini_viewport_expanded else "⤢"
        )
    self.fullscreen_viewport_button.clicked.connect(_toggle_mini_viewport)

    self.content_splitter.addWidget(right_panel)
    self.content_splitter.setStretchFactor(0, 0)
    self.content_splitter.setStretchFactor(1, 1)
    self.content_splitter.setStretchFactor(2, 0)
    self.content_splitter.setSizes([260, 670, 440])
    root.addWidget(self.content_splitter, 1)

    # Rodapé da casca do editor
    footer_panel = QFrame()
    footer_panel.setStyleSheet(
        "QFrame { background-color: #0f121a; border-top: 1px solid #1e2430; }"
        "QTabWidget::pane { border: none; background: transparent; }"
        "QTabBar::tab { background: #141824; color: #94a3b8; padding: 6px 16px; font-size: 11px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; }"
        "QTabBar::tab:selected { background: #1e2536; color: #f8fafc; border-bottom: 2px solid #38bdf8; }"
    )
    footer_layout = QVBoxLayout(footer_panel)
    footer_layout.setContentsMargins(2, 2, 2, 2)

    self.footer_tabs = QTabWidget()

    # Aba Compilação
    compilation_tab = QWidget()
    comp_layout = QHBoxLayout(compilation_tab)
    comp_layout.setContentsMargins(12, 6, 12, 6)

    status_box = QVBoxLayout()
    self.compilation_status_icon = QLabel("●")
    self.compilation_status_icon.setStyleSheet("color: #64748b; font-size: 32px; font-weight: bold;")
    self.compilation_status_text = QLabel("Grafo ainda não compilado")
    self.compilation_status_text.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
    status_box.addWidget(self.compilation_status_icon, 0, Qt.AlignCenter)
    status_box.addWidget(self.compilation_status_text, 0, Qt.AlignCenter)
    comp_layout.addLayout(status_box)

    trace_box = QVBoxLayout()
    trace_label = QLabel("Rastreamento de Execução (Play Mode)")
    trace_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
    trace_box.addWidget(trace_label)

    from PySide6.QtWidgets import QTextEdit
    self.trace_console = QTextEdit()
    self.trace_console.setReadOnly(True)
    self.trace_console.setPlaceholderText("O rastreamento real aparecerá durante o Play Mode.")
    self.trace_console.setStyleSheet(
        "QTextEdit { background-color: #0b0e14; color: #a3e635; font-family: Consolas; font-size: 11px; border: 1px solid #1e2430; border-radius: 4px; }"
    )
    trace_box.addWidget(self.trace_console, 1)
    comp_layout.addLayout(trace_box, 1)

    self.errors_console = QTextEdit()
    self.errors_console.setReadOnly(True)
    self.errors_console.setPlaceholderText("Nenhum erro de validação.")
    self.debug_console = QTextEdit()
    self.debug_console.setReadOnly(True)
    self.debug_console.setPlaceholderText("Eventos de breakpoint e passos aparecerão aqui.")
    self.output_console = QTextEdit()
    self.output_console.setReadOnly(True)
    self.output_console.setPlaceholderText("Mensagens do Logic Graph aparecerão aqui.")
    self.footer_tabs.addTab(compilation_tab, "Compilação")
    self.footer_tabs.addTab(self.errors_console, "Erros")
    self.footer_tabs.addTab(self.debug_console, "Depuração")
    self.footer_tabs.addTab(self.output_console, "Console")

    footer_layout.addWidget(self.footer_tabs)
    self.center_vertical_splitter.addWidget(footer_panel)
    self.center_vertical_splitter.setStretchFactor(0, 1)
    self.center_vertical_splitter.setStretchFactor(1, 0)
    self.center_vertical_splitter.setSizes([800, 100])

    self._refresh_palette("Movimento")
    self._refresh_recipes("")
