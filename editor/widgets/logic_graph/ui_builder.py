"""UI composition for the visual Logic Graph workspace."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGraphicsScene, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QPushButton, QSplitter, QTabWidget, QToolButton,
    QTreeWidget, QVBoxLayout, QWidget,
)

from editor.ui.icons import editor_icon

from .views import LogicGraphView, LogicMiniMapView


def build_logic_graph_ui(self) -> None:
    root = QVBoxLayout(self)
    root.setContentsMargins(8, 8, 8, 8)
    root.setSpacing(8)
    _build_header(self, root)
    _build_toolbar(self, root)
    _build_categories(self, root)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setObjectName("LogicContentSplitter")
    splitter.setChildrenCollapsible(False)
    splitter.addWidget(_build_library(self))
    splitter.addWidget(_build_canvas(self))
    splitter.addWidget(_build_properties(self))
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    splitter.setStretchFactor(2, 0)
    splitter.setSizes([190, 700, 240])
    root.addWidget(splitter, 1)
    self._refresh_palette("Movimento")
    self._refresh_recipes("")


def _build_header(self, root: QVBoxLayout) -> None:
    row = QHBoxLayout()
    title = QLabel("Editor de Lógica Visual")
    title.setObjectName("WorkspaceTitle")
    self.asset_label = QLabel("Novo Logic Graph — ainda não salvo")
    self.asset_label.setObjectName("WorkspaceStatus")
    self.validation_label = QLabel("Grafo vazio")
    self.validation_label.setObjectName("WorkspaceContext")
    self.debug_status_label = QLabel("● DEBUG INATIVO")
    self.debug_status_label.setObjectName("WorkspaceContext")
    row.addWidget(title)
    row.addWidget(self.asset_label)
    row.addStretch(1)
    row.addWidget(self.validation_label)
    row.addWidget(self.debug_status_label)
    root.addLayout(row)


def _tool_button(icon_name: str, tooltip: str) -> QToolButton:
    button = QToolButton()
    button.setIcon(editor_icon(icon_name))
    button.setToolTip(tooltip)
    button.setProperty("uiRole", "icon")
    return button


def _build_toolbar(self, root: QVBoxLayout) -> None:
    widget = QWidget()
    widget.setObjectName("LogicToolbar")
    toolbar = QHBoxLayout(widget)
    toolbar.setContentsMargins(6, 4, 6, 4)
    toolbar.setSpacing(4)
    self.new_button = _tool_button("new", "Novo Logic Graph")
    self.open_button = _tool_button("open", "Abrir Logic Graph")
    self.save_button = _tool_button("save", "Salvar")
    self.save_as_button = _tool_button("save", "Salvar como...")
    for button in (self.new_button, self.open_button, self.save_button, self.save_as_button):
        toolbar.addWidget(button)
    toolbar.addSpacing(8)
    self.new_subgraph_button = QPushButton("Novo subgrafo")
    self.new_subgraph_button.setToolTip("Cria uma função visual reutilizável com entrada e retorno")
    self.demo_button = QPushButton("Abrir exemplo...")
    self.demo_button.setIcon(editor_icon("open"))
    self.demo_button.setProperty("uiRole", "primary")
    self.demo_button.setToolTip("Escolha e abra um exemplo salvo de Logic Graph")
    toolbar.addWidget(self.new_subgraph_button)
    toolbar.addWidget(self.demo_button)
    toolbar.addSpacing(8)
    self.play_button = QPushButton("Play")
    self.play_button.setIcon(editor_icon("play"))
    self.play_button.setProperty("uiRole", "primary")
    self.play_button.setToolTip("Salva o grafo atual e inicia o Play Mode")
    self.stop_button = QPushButton("Stop")
    self.stop_button.setIcon(editor_icon("stop"))
    self.stop_button.setProperty("uiRole", "danger")
    self.stop_button.setToolTip("Interrompe o Play Mode e restaura a cena")
    self.stop_button.setEnabled(False)
    toolbar.addWidget(self.play_button)
    toolbar.addWidget(self.stop_button)
    toolbar.addSpacing(12)
    _build_toolbar_target(self, toolbar)
    _build_toolbar_actions(self, toolbar)
    root.addWidget(widget)


def _build_toolbar_target(self, toolbar: QHBoxLayout) -> None:
    self.graph_enabled_check = QCheckBox("Ativo no Play")
    self.graph_enabled_check.setChecked(True)
    self.graph_enabled_check.setToolTip("Desative para preservar o asset sem executá-lo")
    toolbar.addWidget(self.graph_enabled_check)
    toolbar.addWidget(QLabel("OBJETO ALVO"))
    self.target_type = QComboBox()
    self.target_type.addItem("Nome", "name")
    self.target_type.addItem("Tag", "tag")
    self.target_type.setMaximumWidth(82)
    self.target_value = QLineEdit("Player")
    self.target_value.setPlaceholderText("Player")
    self.target_value.setMaximumWidth(150)
    toolbar.addWidget(self.target_type)
    toolbar.addWidget(self.target_value)
    toolbar.addStretch(1)


def _build_toolbar_actions(self, toolbar: QHBoxLayout) -> None:
    self.fit_button = QPushButton("Enquadrar")
    self.undo_button = QPushButton("Desfazer")
    self.redo_button = QPushButton("Refazer")
    self.undo_button.setShortcut("Ctrl+Z")
    self.redo_button.setShortcut("Ctrl+Y")
    self.undo_button.setEnabled(False)
    self.redo_button.setEnabled(False)
    self.breakpoint_button = QPushButton("● Breakpoint")
    self.breakpoint_button.setToolTip("Alterna um breakpoint no nó selecionado")
    self.continue_debug_button = QPushButton("Continuar")
    self.step_debug_button = QPushButton("Próximo nó")
    self.restart_debug_button = QPushButton("Reiniciar")
    for button in (
        self.continue_debug_button, self.step_debug_button, self.restart_debug_button
    ):
        button.setEnabled(False)
    self.connect_button = QPushButton("Conectar selecionados")
    self.delete_button = QPushButton("Excluir selecionado")
    self.delete_button.setProperty("uiRole", "danger")
    for button in (
        self.fit_button, self.undo_button, self.redo_button, self.breakpoint_button,
        self.continue_debug_button, self.step_debug_button, self.restart_debug_button,
        self.connect_button, self.delete_button,
    ):
        toolbar.addWidget(button)


def _build_categories(self, root: QVBoxLayout) -> None:
    widget = QWidget()
    widget.setObjectName("LogicCategories")
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.setSpacing(6)
    layout.addWidget(QLabel("Categoria"))
    self.category_combo = QComboBox()
    self.category_combo.addItems((
        "Movimento", "Posição", "Ação", "Lógica", "Condição", "Eventos",
        "Objetos", "Variáveis", "Matemática", "Texto", "Subgrafos", "Todos",
    ))
    self.category_combo.setMinimumWidth(150)
    self.category_combo.setToolTip("Filtra a biblioteca de blocos por categoria")
    layout.addWidget(self.category_combo)
    self.add_group_button = QPushButton("+ Grupo")
    self.add_comment_button = QPushButton("+ Comentário")
    self.organize_button = QPushButton("Organizar grafo")
    self.align_button = QPushButton("Alinhar")
    self.distribute_button = QPushButton("Distribuir")
    for button in (
        self.add_group_button, self.add_comment_button, self.organize_button,
        self.align_button, self.distribute_button,
    ):
        layout.addWidget(button)
    layout.addStretch(1)
    root.addWidget(widget)


def _build_library(self) -> QFrame:
    panel = QFrame()
    panel.setObjectName("LogicPalettePanel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(8, 8, 8, 8)
    self.library_tabs = QTabWidget()
    self.library_tabs.setObjectName("LogicLibraryTabs")
    layout.addWidget(self.library_tabs, 1)
    _add_blocks_tab(self)
    _add_recipes_tab(self)
    _add_subgraphs_tab(self)
    _add_data_tab(self)
    panel.setMinimumWidth(230)
    return panel


def _tab(self, name: str) -> tuple[QWidget, QVBoxLayout]:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(5, 6, 5, 6)
    layout.setSpacing(6)
    self.library_tabs.addTab(page, name)
    return page, layout


def _add_blocks_tab(self) -> None:
    _, layout = _tab(self, "Blocos")
    self.node_search = QLineEdit()
    self.node_search.setPlaceholderText("Pesquisar blocos...  ex.: colisão, som, somar")
    self.node_search.setClearButtonEnabled(True)
    self.palette = QListWidget()
    self.palette.setObjectName("LogicNodePalette")
    self.palette.setToolTip("Duplo clique para adicionar um nó")
    self.palette_count = QLabel()
    self.palette_count.setObjectName("PanelHint")
    hint = QLabel("Duplo clique adiciona o bloco. Arraste uma porta para conectar.")
    hint.setObjectName("PanelHint")
    hint.setWordWrap(True)
    layout.addWidget(self.node_search)
    layout.addWidget(self.palette, 1)
    layout.addWidget(self.palette_count)
    layout.addWidget(hint)


def _add_recipes_tab(self) -> None:
    _, layout = _tab(self, "Receitas")
    self.recipe_topic_label = QLabel("Receitas de Movimento")
    self.recipe_topic_label.setObjectName("PanelSectionTitle")
    self.recipe_search = QLineEdit()
    self.recipe_search.setPlaceholderText("O que você quer fazer? ex.: mover sozinho")
    self.recipe_search.setClearButtonEnabled(True)
    self.recipe_list = QListWidget()
    self.recipe_list.setToolTip("Escolha uma lógica pronta para aprender e inserir")
    self.recipe_summary = QLabel("Escolha uma receita para ver como ela funciona.")
    self.recipe_summary.setObjectName("PanelHint")
    self.recipe_summary.setWordWrap(True)
    self.recipe_apply_button = QPushButton("Inserir receita no grafo")
    self.recipe_apply_button.setProperty("uiRole", "primary")
    self.recipe_apply_button.setEnabled(False)
    for widget in (
        self.recipe_topic_label, self.recipe_search, self.recipe_list,
        self.recipe_summary, self.recipe_apply_button,
    ):
        layout.addWidget(widget, 1 if widget is self.recipe_list else 0)


def _add_subgraphs_tab(self) -> None:
    _, layout = _tab(self, "Subgrafos")
    self.subgraph_list = QListWidget()
    self.subgraph_list.setToolTip("Duplo clique adiciona uma chamada ao subgrafo")
    hint = QLabel("Funções visuais reutilizáveis salvas em Assets/Logic.")
    hint.setObjectName("PanelHint")
    hint.setWordWrap(True)
    layout.addWidget(self.subgraph_list, 1)
    layout.addWidget(hint)


def _add_data_tab(self) -> None:
    _, layout = _tab(self, "Dados")
    self.blackboard_tree = QTreeWidget()
    self.blackboard_tree.setHeaderLabels(["Nome", "Tipo", "Escopo"])
    self.blackboard_name_edit = QLineEdit()
    self.blackboard_name_edit.setPlaceholderText("nome_da_variável")
    layout.addWidget(self.blackboard_tree, 1)
    layout.addWidget(self.blackboard_name_edit)
    options = QHBoxLayout()
    self.blackboard_type_combo = QComboBox()
    for label, value in (("Número", "number"), ("Booleano", "bool"), ("Texto", "text"), ("Objeto", "object")):
        self.blackboard_type_combo.addItem(label, value)
    self.blackboard_scope_combo = QComboBox()
    for label, value in (("Objeto", "object"), ("Cena", "scene"), ("Projeto", "project")):
        self.blackboard_scope_combo.addItem(label, value)
    options.addWidget(self.blackboard_type_combo)
    options.addWidget(self.blackboard_scope_combo)
    layout.addLayout(options)
    self.blackboard_default_edit = QLineEdit("0")
    self.blackboard_default_edit.setPlaceholderText("Valor inicial")
    layout.addWidget(self.blackboard_default_edit)
    _add_blackboard_actions(self, layout)


def _add_blackboard_actions(self, layout: QVBoxLayout) -> None:
    edit_actions = QHBoxLayout()
    self.blackboard_save_button = QPushButton("Adicionar")
    self.blackboard_remove_button = QPushButton("Excluir")
    edit_actions.addWidget(self.blackboard_save_button)
    edit_actions.addWidget(self.blackboard_remove_button)
    layout.addLayout(edit_actions)
    node_actions = QHBoxLayout()
    self.blackboard_get_button = QPushButton("Ler")
    self.blackboard_set_button = QPushButton("Definir")
    node_actions.addWidget(self.blackboard_get_button)
    node_actions.addWidget(self.blackboard_set_button)
    layout.addLayout(node_actions)
    hint = QLabel("Variáveis organizadas por objeto, cena ou projeto.")
    hint.setObjectName("PanelHint")
    hint.setWordWrap(True)
    layout.addWidget(hint)


def _build_canvas(self) -> QWidget:
    self.scene = QGraphicsScene(self)
    self.scene.setSceneRect(-2000.0, -1400.0, 4000.0, 2800.0)
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)
    self.view = LogicGraphView(self.scene, self)
    layout.addWidget(self.view, 1)
    minimap_row = QHBoxLayout()
    minimap_row.addStretch(1)
    self.minimap = LogicMiniMapView(self.scene, self)
    minimap_row.addWidget(self.minimap)
    layout.addLayout(minimap_row)
    return panel


def _build_properties(self) -> QFrame:
    panel = QFrame()
    panel.setObjectName("LogicPropertiesPanel")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(8, 8, 8, 8)
    title = QLabel("PROPRIEDADES DO NÓ")
    title.setObjectName("PanelSectionTitle")
    self.selected_label = QLabel("Nenhum nó selecionado")
    self.selected_label.setObjectName("WorkspaceContext")
    self.selected_label.setWordWrap(True)
    self.property_tree = QTreeWidget()
    self.property_tree.setObjectName("LogicPropertyTree")
    self.property_tree.setHeaderLabels(["Propriedade", "Valor"])
    self.property_tree.setColumnWidth(0, 105)
    layout.addWidget(title)
    layout.addWidget(self.selected_label)
    layout.addWidget(self.property_tree, 1)
    _add_property_asset_and_breakpoint(self, layout)
    _add_runtime_and_watches(self, layout)
    hint = QLabel(
        "Delete remove, Ctrl+D duplica e Esc cancela uma conexão. "
        "Use −/+ no bloco para recolher e a alça inferior para redimensionar."
    )
    hint.setObjectName("PanelHint")
    hint.setWordWrap(True)
    layout.addWidget(hint)
    panel.setMinimumWidth(230)
    return panel


def _add_property_asset_and_breakpoint(self, layout: QVBoxLayout) -> None:
    self.property_asset_button = QPushButton("Selecionar asset do projeto...")
    self.property_asset_button.setToolTip("Vincula uma imagem, animação ou som da pasta Assets")
    self.property_asset_button.hide()
    layout.addWidget(self.property_asset_button)
    self.breakpoint_condition_label = QLabel("CONDIÇÃO DO BREAKPOINT")
    self.breakpoint_condition_label.setObjectName("PanelSectionTitle")
    self.breakpoint_condition_edit = QLineEdit()
    self.breakpoint_condition_edit.setPlaceholderText("Ex.: vida <= 0 ou estado == andando")
    self.breakpoint_condition_edit.setEnabled(False)
    layout.addWidget(self.breakpoint_condition_label)
    layout.addWidget(self.breakpoint_condition_edit)


def _add_runtime_and_watches(self, layout: QVBoxLayout) -> None:
    self.runtime_values_title = QLabel("VALORES EM EXECUÇÃO")
    self.runtime_values_title.setObjectName("PanelSectionTitle")
    self.runtime_values_title.hide()
    self.runtime_values_tree = QTreeWidget()
    self.runtime_values_tree.setHeaderLabels(["Nó / variável", "Valor"])
    self.runtime_values_tree.setMaximumHeight(155)
    self.runtime_values_tree.hide()
    layout.addWidget(self.runtime_values_title)
    layout.addWidget(self.runtime_values_tree)
    watch_title = QLabel("OBSERVADORES")
    watch_title.setObjectName("PanelSectionTitle")
    self.watch_values_tree = QTreeWidget()
    self.watch_values_tree.setHeaderLabels(["Expressão", "Valor"])
    self.watch_values_tree.setMaximumHeight(135)
    layout.addWidget(watch_title)
    layout.addWidget(self.watch_values_tree)
    row = QHBoxLayout()
    self.watch_expression_edit = QLineEdit()
    self.watch_expression_edit.setPlaceholderText("vida, x, grounded...")
    self.add_watch_button = QPushButton("+")
    self.add_watch_button.setToolTip("Adicionar observador")
    self.remove_watch_button = QPushButton("−")
    self.remove_watch_button.setToolTip("Remover observador selecionado")
    row.addWidget(self.watch_expression_edit, 1)
    row.addWidget(self.add_watch_button)
    row.addWidget(self.remove_watch_button)
    layout.addLayout(row)
