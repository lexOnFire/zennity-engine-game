"""Teste isolado da interface do Zennity Editor, sem Pygame ou Viewport.

Execute a partir da raiz do projeto:
    python -m editor.interface_smoke_test
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from editor.ui.icons import TOOLBAR_ICONS, component_title, editor_icon
from editor.ui.empty_state import EmptyStateWidget
from editor.widgets.logic_graph_editor import LogicGraphEditor


class DetachedWorkspaceWindow(QMainWindow):
    """Janela de ferramenta independente que apenas se oculta ao fechar."""

    def __init__(self, title: str, workspace: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent, Qt.Window)
        self.setWindowTitle(title)
        self.resize(1180, 760)
        self.setMinimumSize(820, 560)
        self.setCentralWidget(workspace)
        workspace.show()

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()


class InterfaceSmokeTest(QMainWindow):
    """Shell do editor para validar dock, splitter, menu e resize do Qt."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Zennity — Teste de Interface (sem Viewport)")
        self.resize(1440, 900)
        self.setMinimumSize(1000, 650)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        self._build_menu()
        self._build_toolbar()
        self._build_center()
        self._build_docks()
        from editor.ui import polish_editor_widgets
        polish_editor_widgets(self)
        self.statusBar().showMessage("Teste isolado: não há Pygame nem renderização de cena.")

    def _build_menu(self) -> None:
        self.editor_menus = {}
        for name in ("Arquivo", "Editar", "Janela", "Criar", "Ferramentas", "Build", "Executar", "Ajuda"):
            menu = self.menuBar().addMenu(name)
            self.editor_menus[name] = menu

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Ferramentas")
        toolbar.setObjectName("CommandBar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(17, 17))
        self.addToolBar(toolbar)
        self.toolbar_actions = {}
        for label, icon_name in TOOLBAR_ICONS.items():
            action = QAction(editor_icon(icon_name), label, self)
            action.setStatusTip(label)
            action.setToolTip(label)
            self.toolbar_actions[label] = action
            toolbar.addAction(action)
        toolbar.addSeparator()
        mode = QComboBox()
        mode.setObjectName("ModeSwitch")
        mode.addItems(["2D", "3D (experimental)"])
        toolbar.addWidget(mode)

    def _build_center(self) -> None:
        self.viewport_tabs = QTabWidget()
        self.viewport_tabs.setObjectName("SceneGameTabs")
        self.viewport_host = QFrame()
        self.viewport_host.setObjectName("IsolatedViewportHost")
        self.viewport_host.setFrameShape(QFrame.StyledPanel)
        self.viewport_host.setAttribute(Qt.WA_NativeWindow, True)
        self.viewport_host.setStyleSheet("#IsolatedViewportHost { background: #16181f; }")

        # Em vez de colocar a viewport_host como widget da aba e perder o HWND parent ao alternar,
        # fazemos a viewport_tabs atuar apenas como seletor visual e inserimos o viewport_host diretamente
        # sob um container que o mantém ativo e visível.
        self.viewport_tabs.addTab(QWidget(), "Scene")
        self.viewport_tabs.addTab(QWidget(), "Game")

        self.animation_workspace = QWidget()
        self.animation_workspace.setObjectName("AnimationWorkspace")
        animation_layout = QVBoxLayout(self.animation_workspace)
        animation_layout.setContentsMargins(8, 8, 8, 8)
        animation_layout.setSpacing(8)
        animation_title_row = QHBoxLayout()
        animation_title = QLabel("Editor de Animação 2D")
        animation_title.setObjectName("WorkspaceTitle")
        self.animation_asset_label = QLabel("Novo clip — ainda não salvo")
        self.animation_asset_label.setObjectName("WorkspaceStatus")
        self.animation_object_label = QLabel("Nenhum objeto selecionado")
        self.animation_object_label.setObjectName("WorkspaceContext")
        animation_title_row.addWidget(animation_title)
        animation_title_row.addWidget(self.animation_asset_label)
        animation_title_row.addStretch(1)
        animation_title_row.addWidget(self.animation_object_label)
        animation_layout.addLayout(animation_title_row)

        animation_toolbar_widget = QWidget()
        animation_toolbar_widget.setObjectName("AnimationToolbar")
        animation_toolbar = QHBoxLayout(animation_toolbar_widget)
        animation_toolbar.setContentsMargins(6, 4, 6, 4)
        animation_toolbar.setSpacing(4)
        asset_tools_label = QLabel("ASSET")
        asset_tools_label.setObjectName("PanelSectionTitle")
        animation_toolbar.addWidget(asset_tools_label)
        self.animation_new_button = QToolButton()
        self.animation_open_button = QToolButton()
        self.animation_save_button = QToolButton()
        self.animation_save_as_button = QToolButton()
        self.animation_duplicate_button = QToolButton()
        self.animation_delete_button = QToolButton()
        for button, tooltip in (
            (self.animation_new_button, "Nova animação"),
            (self.animation_open_button, "Abrir animação"),
            (self.animation_save_button, "Salvar animação"),
            (self.animation_save_as_button, "Salvar animação como..."),
            (self.animation_duplicate_button, "Duplicar animação"),
            (self.animation_delete_button, "Excluir animação"),
        ):
            button.setToolTip(tooltip)
            button.setIconSize(QSize(16, 16))
            button.setProperty("uiRole", "icon")
        self.animation_apply_button = QPushButton("Aplicar ao selecionado")
        self.animation_demo_button = QPushButton("Testar no Player")
        self.animation_open_demo_button = QPushButton("Abrir Demo Animator")
        for button, icon_name in (
            (self.animation_new_button, "new"),
            (self.animation_open_button, "open"),
            (self.animation_save_button, "save"),
            (self.animation_save_as_button, "save"),
            (self.animation_duplicate_button, "duplicate"),
            (self.animation_delete_button, "delete"),
            (self.animation_apply_button, "apply"),
            (self.animation_demo_button, "play"),
            (self.animation_open_demo_button, "open"),
        ):
            button.setIcon(editor_icon(icon_name))
        self.animation_delete_button.setProperty("uiRole", "danger")
        self.animation_apply_button.setProperty("uiRole", "primary")
        self.animation_demo_button.setProperty("uiRole", "play")
        self.animation_open_demo_button.setProperty("uiRole", "primary")
        for button in (
            self.animation_new_button, self.animation_open_button,
            self.animation_save_button, self.animation_save_as_button,
            self.animation_duplicate_button, self.animation_delete_button,
        ):
            animation_toolbar.addWidget(button)
        animation_toolbar.addSpacing(10)
        object_tools_label = QLabel("OBJETO")
        object_tools_label.setObjectName("PanelSectionTitle")
        animation_toolbar.addWidget(object_tools_label)
        animation_toolbar.addWidget(self.animation_apply_button)
        animation_toolbar.addWidget(self.animation_demo_button)
        animation_toolbar.addWidget(self.animation_open_demo_button)
        animation_toolbar.addStretch(1)
        animation_layout.addWidget(animation_toolbar_widget)

        self.animation_content_splitter = QSplitter(Qt.Horizontal)
        self.animation_content_splitter.setObjectName("AnimationContentSplitter")
        self.animation_content_splitter.setChildrenCollapsible(False)

        library_panel = QFrame()
        library_panel.setObjectName("AnimationLibraryPanel")
        library_layout = QVBoxLayout(library_panel)
        library_layout.setContentsMargins(8, 8, 8, 8)
        library_title = QLabel("BIBLIOTECA")
        library_title.setObjectName("PanelSectionTitle")
        library_layout.addWidget(library_title)
        self.animation_library_tree = QTreeWidget()
        self.animation_library_tree.setObjectName("AnimationLibraryTree")
        self.animation_library_tree.setHeaderHidden(True)
        self.animation_library_tree.setMinimumWidth(140)
        self.animation_library_tree.setToolTip("Duplo clique para abrir uma animação salva")
        library_layout.addWidget(self.animation_library_tree, 1)
        library_hint = QLabel("Assets/Animations\nClips .zanim e controllers .zanimator")
        library_hint.setObjectName("PanelHint")
        library_layout.addWidget(library_hint)
        library_panel.setMinimumWidth(150)
        self.animation_content_splitter.addWidget(library_panel)

        preview_panel = QWidget()
        preview_panel.setObjectName("AnimationPreviewPanel")
        preview_panel.setMinimumWidth(220)
        preview_column = QVBoxLayout(preview_panel)
        preview_column.setContentsMargins(8, 8, 8, 8)
        self.animator_preview = QLabel("Selecione um objeto com Animator 2D")
        self.animator_preview.setObjectName("AnimationPreview")
        self.animator_preview.setProperty("uiState", "empty")
        self.animator_preview.setAlignment(Qt.AlignCenter)
        self.animator_preview.setMinimumHeight(160)
        self.animator_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview_column.addWidget(self.animator_preview, 1)

        timeline_panel = QFrame()
        timeline_panel.setObjectName("AnimationTimelinePanel")
        timeline_layout = QVBoxLayout(timeline_panel)
        timeline_layout.setContentsMargins(8, 7, 8, 8)
        timeline_header = QHBoxLayout()
        timeline_title = QLabel("TIMELINE")
        timeline_title.setObjectName("PanelSectionTitle")
        timeline_header.addWidget(timeline_title)
        timeline_header.addStretch(1)
        self.animation_frame_label = QLabel("Frame 1 / 1")
        self.animation_frame_label.setObjectName("AnimationFrameCounter")
        timeline_header.addWidget(self.animation_frame_label)
        timeline_layout.addLayout(timeline_header)
        playback_row = QHBoxLayout()
        self.animation_first_frame_button = QPushButton("|◀")
        self.animation_previous_frame_button = QPushButton("◀")
        self.animation_play_button = QPushButton("⏸")
        self.animation_next_frame_button = QPushButton("▶")
        self.animation_last_frame_button = QPushButton("▶|")
        for button, icon_name in (
            (self.animation_first_frame_button, "first"),
            (self.animation_previous_frame_button, "previous"),
            (self.animation_play_button, "pause"),
            (self.animation_next_frame_button, "next"),
            (self.animation_last_frame_button, "last"),
        ):
            button.setText("")
            button.setIcon(editor_icon(icon_name))
        for button, tooltip in (
            (self.animation_first_frame_button, "Primeiro frame"),
            (self.animation_previous_frame_button, "Frame anterior"),
            (self.animation_play_button, "Reproduzir ou pausar prévia"),
            (self.animation_next_frame_button, "Próximo frame"),
            (self.animation_last_frame_button, "Último frame"),
        ):
            button.setToolTip(tooltip)
        for button in (
            self.animation_first_frame_button, self.animation_previous_frame_button,
            self.animation_play_button, self.animation_next_frame_button,
            self.animation_last_frame_button,
        ):
            button.setMaximumWidth(48)
            button.setProperty("uiRole", "icon")
            playback_row.addWidget(button)
        playback_row.addStretch(1)
        timeline_layout.addLayout(playback_row)
        self.animation_timeline = QSlider(Qt.Horizontal)
        self.animation_timeline.setRange(0, 0)
        self.animation_timeline.setToolTip("Arraste para visualizar qualquer quadro")
        timeline_layout.addWidget(self.animation_timeline)
        event_header = QHBoxLayout()
        event_header.addWidget(QLabel("EVENTOS POR FRAME"))
        event_header.addStretch(1)
        self.animation_add_event_button = QPushButton("+ Evento")
        self.animation_remove_event_button = QPushButton("− Evento")
        event_header.addWidget(self.animation_add_event_button)
        event_header.addWidget(self.animation_remove_event_button)
        timeline_layout.addLayout(event_header)
        self.animation_events_tree = QTreeWidget()
        self.animation_events_tree.setHeaderLabels(["Frame", "Evento", "Payload"])
        self.animation_events_tree.setMaximumHeight(105)
        self.animation_events_tree.setRootIsDecorated(False)
        timeline_layout.addWidget(self.animation_events_tree)
        current_clip_row = QHBoxLayout()
        current_clip_label = QLabel("Clip ativo")
        current_clip_label.setObjectName("PanelHint")
        current_clip_row.addWidget(current_clip_label)
        self.animator_current_lbl = QLineEdit("Nenhum")
        self.animator_current_lbl.setReadOnly(True)
        current_clip_row.addWidget(self.animator_current_lbl, 1)
        timeline_layout.addLayout(current_clip_row)
        preview_column.addWidget(timeline_panel)
        self.animation_content_splitter.addWidget(preview_panel)

        self.animator_body = QWidget()
        self.animator_body.setObjectName("AnimationPropertiesPanel")
        animator_lay = QFormLayout(self.animator_body)
        animator_lay.setContentsMargins(10, 10, 10, 10)
        object_section_title = QLabel("OBJETO SELECIONADO")
        object_section_title.setObjectName("PanelSectionTitle")
        animator_lay.addRow(object_section_title)
        self.show_animator_chk = QCheckBox("Animator 2D ativo")
        animator_lay.addRow(self.show_animator_chk)
        self.btn_del_anim = QPushButton("Excluir Animator")
        self.btn_del_anim.setProperty("uiRole", "dangerAction")
        animator_lay.addRow(self.btn_del_anim)
        controller_section_title = QLabel("ANIMATOR CONTROLLER")
        controller_section_title.setObjectName("PanelSectionTitle")
        animator_lay.addRow(controller_section_title)
        self.animation_controller_combo = QComboBox()
        self.animation_controller_combo.addItem("Nenhum", "")
        animator_lay.addRow("Controller", self.animation_controller_combo)
        controller_actions = QWidget()
        controller_actions_layout = QHBoxLayout(controller_actions)
        controller_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.animation_new_controller_button = QPushButton("Novo")
        self.animation_edit_controller_button = QPushButton("Editar")
        controller_actions_layout.addWidget(self.animation_new_controller_button)
        controller_actions_layout.addWidget(self.animation_edit_controller_button)
        animator_lay.addRow("Ações", controller_actions)
        self.animation_controller_summary = QLabel("Use um controller para criar estados e transições.")
        self.animation_controller_summary.setObjectName("PanelHint")
        self.animation_controller_summary.setWordWrap(True)
        animator_lay.addRow(self.animation_controller_summary)
        clip_runtime_section_title = QLabel("CLIP DIRETO")
        clip_runtime_section_title.setObjectName("PanelSectionTitle")
        animator_lay.addRow(clip_runtime_section_title)
        self.animator_clip_combo = QComboBox()
        animator_lay.addRow("Clip", self.animator_clip_combo)
        self.animator_speed_field = QDoubleSpinBox()
        self.animator_speed_field.setRange(0.0, 100.0)
        self.animator_speed_field.setValue(1.0)
        animator_lay.addRow("Velocidade", self.animator_speed_field)
        clip_actions = QWidget()
        clip_actions_layout = QHBoxLayout(clip_actions)
        clip_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.animator_add_clip_button = QPushButton("+ Clip")
        self.animator_remove_clip_button = QPushButton("− Clip")
        clip_actions_layout.addWidget(self.animator_add_clip_button)
        clip_actions_layout.addWidget(self.animator_remove_clip_button)
        animator_lay.addRow("Clips", clip_actions)
        clip_section_title = QLabel("PROPRIEDADES DO CLIP")
        clip_section_title.setObjectName("PanelSectionTitle")
        animator_lay.addRow(clip_section_title)
        self.animator_sheet_combo = QComboBox()
        animator_lay.addRow("Sprite Sheet", self.animator_sheet_combo)
        self.animator_frame_width = QDoubleSpinBox()
        self.animator_frame_height = QDoubleSpinBox()
        self.animator_start_frame = QDoubleSpinBox()
        self.animator_frame_count = QDoubleSpinBox()
        for field, minimum, maximum in ((self.animator_frame_width, 1, 8192), (self.animator_frame_height, 1, 8192), (self.animator_start_frame, 0, 100000), (self.animator_frame_count, 1, 100000)):
            field.setRange(minimum, maximum)
            field.setDecimals(0)
            field.setKeyboardTracking(False)
        animator_lay.addRow("Largura do frame", self.animator_frame_width)
        animator_lay.addRow("Altura do frame", self.animator_frame_height)
        animator_lay.addRow("Frame inicial", self.animator_start_frame)
        animator_lay.addRow("Nº de frames", self.animator_frame_count)
        self.animator_fps_field = QDoubleSpinBox()
        self.animator_fps_field.setRange(0.1, 240.0)
        self.animator_fps_field.setValue(8.0)
        self.animator_fps_field.setKeyboardTracking(False)
        animator_lay.addRow("FPS", self.animator_fps_field)
        self.animator_loop_field = QCheckBox()
        self.animator_loop_field.setChecked(True)
        animator_lay.addRow("Repetir", self.animator_loop_field)
        properties_hint = QLabel("Escolha o Sprite Sheet e informe o tamanho de cada frame. Salve e aplique ao objeto selecionado.")
        properties_hint.setObjectName("PanelHint")
        properties_hint.setWordWrap(True)
        animator_lay.addRow(properties_hint)

        self.animation_properties_scroll = QScrollArea()
        self.animation_properties_scroll.setObjectName("AnimationPropertiesScroll")
        self.animation_properties_scroll.setWidgetResizable(True)
        self.animation_properties_scroll.setFrameShape(QFrame.NoFrame)
        self.animation_properties_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.animation_properties_scroll.setMinimumWidth(220)
        self.animation_properties_scroll.setWidget(self.animator_body)
        self.animation_content_splitter.addWidget(self.animation_properties_scroll)
        self.animation_content_splitter.setStretchFactor(0, 0)
        self.animation_content_splitter.setStretchFactor(1, 1)
        self.animation_content_splitter.setStretchFactor(2, 0)
        self.animation_content_splitter.setSizes([170, 430, 250])
        animation_layout.addWidget(self.animation_content_splitter, 1)
        self.logic_workspace = LogicGraphEditor()
        self.animation_window = DetachedWorkspaceWindow("Zennity — Editor de Animação", self.animation_workspace, self)
        self.logic_window = DetachedWorkspaceWindow("Zennity — Editor de Lógica Visual", self.logic_workspace, self)

        self.center_container = QWidget()
        layout = QVBoxLayout(self.center_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.viewport_tabs)
        layout.addWidget(self.viewport_host)
        layout.setStretchFactor(self.viewport_host, 1)

    def _build_docks(self) -> None:
        hierarchy = QTreeWidget()
        self.hierarchy_tree = hierarchy
        hierarchy.setObjectName("HierarchyTree")
        hierarchy.setHeaderHidden(True)
        root = QTreeWidgetItem(["MainScene"])
        environment = QTreeWidgetItem(["Environment"])
        environment.addChildren([QTreeWidgetItem(["DirectionalLight"]), QTreeWidgetItem(["Terrain"])])
        root.addChildren([environment, QTreeWidgetItem(["Chao"]), QTreeWidgetItem(["Player"]), QTreeWidgetItem(["Enemies"])])
        hierarchy.addTopLevelItem(root)
        hierarchy.expandAll()

        assets = QTreeWidget()
        self.assets_tree = assets
        assets.setObjectName("AssetsTree")
        assets.setHeaderHidden(True)
        asset_root = QTreeWidgetItem(["Assets"])
        asset_root.addChildren([QTreeWidgetItem(["Scenes"]), QTreeWidgetItem(["Logic"]), QTreeWidgetItem(["Animations"]), QTreeWidgetItem(["Textures"]), QTreeWidgetItem(["Audio"])])
        assets.addTopLevelItem(asset_root)
        assets.expandAll()

        create_panel = QWidget()
        create_layout = QVBoxLayout(create_panel)
        create_layout.setContentsMargins(6, 6, 6, 6)
        self.create_buttons = {}
        for label, kind in (
            ("Empty Object", "Empty"), ("Sprite 2D", "Sprite"),
            ("Player 2D", "Player"), ("Platform 2D", "Platform"),
            ("Enemy 2D", "Enemy"), ("Trigger 2D", "Trigger"),
            ("Camera 2D", "Camera"),
        ):
            button = QPushButton(label)
            button.setObjectName("CreatePresetButton")
            self.create_buttons[kind] = button
            create_layout.addWidget(button)
        create_layout.addStretch(1)

        hierarchy_tabs = QTabWidget()
        hierarchy_tabs.setObjectName("NavigationTabs")
        hierarchy_tabs.addTab(hierarchy, "Hierarchy")
        hierarchy_tabs.addTab(create_panel, "Criar")

        prefab_tree = QTreeWidget()
        self.prefab_tree = prefab_tree
        prefab_tree.setObjectName("PrefabsTree")
        prefab_tree.setHeaderHidden(True)
        prefab_tree.addTopLevelItem(QTreeWidgetItem(["Prefabs disponíveis no projeto"] ))
        asset_tabs = QTabWidget()
        asset_tabs.setObjectName("AssetTabs")
        asset_tabs.addTab(assets, "Assets")
        asset_tabs.addTab(prefab_tree, "Adicionar Prefabs")

        left = QSplitter(Qt.Vertical)
        left.setChildrenCollapsible(False)
        left.addWidget(hierarchy_tabs)
        left.addWidget(asset_tabs)
        left.setSizes([300, 420])
        left.setMinimumWidth(240)

        # Criação do Inspector como QDockWidget para habilitar desgrudar/flutuar e encolher/fechar
        self.inspector_dock = QDockWidget("Inspector", self)
        self.inspector_dock.setObjectName("InspectorDock")
        self.inspector_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.inspector_dock)

        # QScrollArea para evitar que a janela fique apertada e bagunçada
        scroll = QScrollArea()
        scroll.setObjectName("InspectorScrollArea")
        scroll.setWidgetResizable(True)

        inspector = QWidget()
        self.inspector_panel = inspector
        inspector.setObjectName("InspectorPanel")
        main_layout = QVBoxLayout(inspector)
        self.inspector_layout = main_layout
        main_layout.setContentsMargins(8, 8, 8, 10)
        main_layout.setSpacing(6)

        # BARRA DE TÍTULO CUSTOMIZADA DO INSPECTOR (Com botões de encolher, desgrudar/flutuar, acoplar)
        title_bar = QWidget()
        title_bar.setObjectName("InspectorToolbar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(6, 4, 6, 4)

        inspector_lbl = QLabel("🔍 INSPECTOR")
        inspector_lbl.setObjectName("InspectorToolbarTitle")
        title_bar_layout.addWidget(inspector_lbl)
        title_bar_layout.addStretch()

        # Botões de controle da janela
        self.btn_collapse_dock = QPushButton("▼") # Encolher
        self.btn_collapse_dock.setToolTip("Ocultar Painel")
        self.btn_float_dock = QPushButton("⎋")      # Desgrudar / Flutuar
        self.btn_float_dock.setToolTip("Desgrudar/Flutuar Janela")
        self.btn_dock_dock = QPushButton("⚓")       # Acoplar / Travar
        self.btn_dock_dock.setToolTip("Acoplar no Editor")

        for btn in (self.btn_collapse_dock, self.btn_float_dock, self.btn_dock_dock):
            btn.setFixedSize(20, 20)
            btn.setObjectName("InspectorPanelControl")
            btn.setProperty("uiRole", "icon")
            title_bar_layout.addWidget(btn)

        # Conecta as ações nos botões customizados
        self.btn_collapse_dock.clicked.connect(lambda: self.inspector_panel.setVisible(not self.inspector_panel.isVisible()))
        self.btn_float_dock.clicked.connect(lambda: self.inspector_dock.setFloating(True))
        self.btn_dock_dock.clicked.connect(lambda: self.inspector_dock.setFloating(False))

        main_layout.addWidget(title_bar)

        # Cabeçalho do Objeto (Player, Estático, etc.)
        obj_header = QWidget()
        obj_header_layout = QHBoxLayout(obj_header)
        obj_header_layout.setContentsMargins(0, 0, 0, 0)

        self.inspector_name_label = QLabel("Player")
        self.inspector_name_label.setObjectName("InspectorObjectName")

        self.static_checkbox = QCheckBox("Estático")
        self.static_checkbox.setObjectName("InspectorCheckBox")

        obj_header_layout.addWidget(self.inspector_name_label)
        obj_header_layout.addWidget(self.static_checkbox)
        main_layout.addWidget(obj_header)

        # Tag & Layer rows
        tag_layer = QWidget()
        tag_layer_layout = QHBoxLayout(tag_layer)
        tag_layer_layout.setContentsMargins(0, 0, 0, 0)
        tag_layer_layout.addWidget(QLabel("Tag"))
        self.tag_combo = QComboBox()
        self.tag_combo.addItems(["Player", "Untagged", "MainCamera", "Enemy"])
        tag_layer_layout.addWidget(self.tag_combo)
        tag_layer_layout.addWidget(QLabel("Layer"))
        self.layer_combo = QComboBox()
        self.layer_combo.addItems(["Default", "UI", "Water", "Ignore Raycast"])
        tag_layer_layout.addWidget(self.layer_combo)
        main_layout.addWidget(tag_layer)

        # ------------------ COMPONENTE: TRANSFORM (Organização Horizontal X, Y, Z Exata) ------------------
        self.transform_header = QWidget()
        self.transform_header.setObjectName("InspectorComponentHeader")
        self.transform_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
        trans_h_layout = QHBoxLayout(self.transform_header)
        trans_h_layout.setContentsMargins(6, 4, 6, 4)

        # Símbolo expansor e ícone
        trans_title = QLabel(component_title("transform", "Transform"))
        trans_title.setStyleSheet("font-weight: bold; color: #ffffff;")
        trans_h_layout.addWidget(trans_title)
        trans_h_layout.addStretch()

        # Botões de encolher e excluir
        self.btn_collapse_transform = QToolButton()
        self.btn_collapse_transform.setText("▼")
        self.btn_collapse_transform.setFixedSize(18, 18)
        self.btn_collapse_transform.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

        trans_h_layout.addWidget(self.btn_collapse_transform)
        main_layout.addWidget(self.transform_header)

        # Widget container para as propriedades do Transform (encolhível)
        self.transform_body = QWidget()
        trans_body_layout = QVBoxLayout(self.transform_body)
        trans_body_layout.setContentsMargins(0, 0, 0, 0)
        trans_body_layout.setSpacing(6)

        # Conecta as ações

        self.inspector_fields: dict[str, QDoubleSpinBox] = {}

        # 1. Posição
        pos_widget = QWidget()
        pos_layout = QHBoxLayout(pos_widget)
        pos_layout.setContentsMargins(4, 0, 4, 0)
        pos_lbl = QLabel("Posição")
        pos_lbl.setMinimumWidth(50)
        pos_layout.addWidget(pos_lbl)

        self.inspector_fields["x"] = QDoubleSpinBox()
        self.inspector_fields["x"].setObjectName("InspectorNumberField")
        self.inspector_fields["x"].setDecimals(2)
        self.inspector_fields["x"].setRange(-100000.0, 100000.0)
        self.inspector_fields["x"].setKeyboardTracking(False)
        pos_layout.addWidget(QLabel("X"))
        pos_layout.addWidget(self.inspector_fields["x"])

        self.inspector_fields["y"] = QDoubleSpinBox()
        self.inspector_fields["y"].setObjectName("InspectorNumberField")
        self.inspector_fields["y"].setDecimals(2)
        self.inspector_fields["y"].setRange(-100000.0, 100000.0)
        self.inspector_fields["y"].setKeyboardTracking(False)
        pos_layout.addWidget(QLabel("Y"))
        pos_layout.addWidget(self.inspector_fields["y"])

        pos_z = QDoubleSpinBox()
        pos_z.setObjectName("InspectorNumberField")
        pos_z.setDecimals(2)
        pos_z.setValue(0.00)
        pos_z.setEnabled(False)
        pos_layout.addWidget(QLabel("Z"))
        pos_layout.addWidget(pos_z)

        trans_body_layout.addWidget(pos_widget)

        # 2. Rotação
        rot_widget = QWidget()
        rot_layout = QHBoxLayout(rot_widget)
        rot_layout.setContentsMargins(4, 0, 4, 0)
        rot_lbl = QLabel("Rotação")
        rot_lbl.setMinimumWidth(50)
        rot_layout.addWidget(rot_lbl)

        rot_x = QDoubleSpinBox()
        rot_x.setObjectName("InspectorNumberField")
        rot_x.setDecimals(2)
        rot_x.setValue(0.00)
        rot_x.setEnabled(False)
        rot_layout.addWidget(QLabel("X"))
        rot_layout.addWidget(rot_x)

        rot_y = QDoubleSpinBox()
        rot_y.setObjectName("InspectorNumberField")
        rot_y.setDecimals(2)
        rot_y.setValue(0.00)
        rot_y.setEnabled(False)
        rot_layout.addWidget(QLabel("Y"))
        rot_layout.addWidget(rot_y)

        self.inspector_fields["rotation"] = QDoubleSpinBox()
        self.inspector_fields["rotation"].setObjectName("InspectorNumberField")
        self.inspector_fields["rotation"].setDecimals(2)
        self.inspector_fields["rotation"].setRange(-100000.0, 100000.0)
        self.inspector_fields["rotation"].setKeyboardTracking(False)
        rot_layout.addWidget(QLabel("Z"))
        rot_layout.addWidget(self.inspector_fields["rotation"])

        trans_body_layout.addWidget(rot_widget)

        # 3. Escala
        scale_widget = QWidget()
        scale_layout = QHBoxLayout(scale_widget)
        scale_layout.setContentsMargins(4, 0, 4, 0)
        scale_lbl = QLabel("Escala")
        scale_lbl.setMinimumWidth(50)
        scale_layout.addWidget(scale_lbl)

        self.inspector_fields["w"] = QDoubleSpinBox()
        self.inspector_fields["w"].setObjectName("InspectorNumberField")
        self.inspector_fields["w"].setDecimals(2)
        self.inspector_fields["w"].setRange(1.0, 100000.0)
        self.inspector_fields["w"].setKeyboardTracking(False)
        scale_layout.addWidget(QLabel("X"))
        scale_layout.addWidget(self.inspector_fields["w"])

        self.inspector_fields["h"] = QDoubleSpinBox()
        self.inspector_fields["h"].setObjectName("InspectorNumberField")
        self.inspector_fields["h"].setDecimals(2)
        self.inspector_fields["h"].setRange(1.0, 100000.0)
        self.inspector_fields["h"].setKeyboardTracking(False)
        scale_layout.addWidget(QLabel("Y"))
        scale_layout.addWidget(self.inspector_fields["h"])

        scale_z = QDoubleSpinBox()
        scale_z.setObjectName("InspectorNumberField")
        scale_z.setDecimals(2)
        scale_z.setValue(1.00)
        scale_z.setEnabled(False)
        scale_layout.addWidget(QLabel("Z"))
        scale_layout.addWidget(scale_z)

        trans_body_layout.addWidget(scale_widget)
        main_layout.addWidget(self.transform_body)

        # ------------------ COMPONENTE: SPRITE RENDERER ------------------
        self.sprite_renderer_header = QWidget()
        self.sprite_renderer_header.setObjectName("InspectorComponentHeader")
        self.sprite_renderer_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
        sprite_header_layout = QHBoxLayout(self.sprite_renderer_header)
        sprite_header_layout.setContentsMargins(6, 4, 6, 4)
        self.show_renderer_chk = QCheckBox(component_title("sprite", "Sprite Renderer"))
        self.show_renderer_chk.setObjectName("InspectorCheckBox")
        self.show_renderer_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        sprite_header_layout.addWidget(self.show_renderer_chk)
        sprite_header_layout.addStretch(1)
        self.btn_collapse_renderer = QToolButton()
        self.btn_collapse_renderer.setText("▼")
        self.btn_collapse_renderer.setFixedSize(18, 18)
        self.btn_collapse_renderer.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")
        self.btn_delete_renderer = QToolButton()
        self.btn_delete_renderer.setText("✕")
        self.btn_delete_renderer.setFixedSize(18, 18)
        self.btn_delete_renderer.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")
        sprite_header_layout.addWidget(self.btn_collapse_renderer)
        sprite_header_layout.addWidget(self.btn_delete_renderer)
        main_layout.addWidget(self.sprite_renderer_header)

        self.sprite_renderer_body = QWidget()
        sprite_form = QFormLayout(self.sprite_renderer_body)
        sprite_form.setContentsMargins(8, 0, 8, 0)
        texture_row = QWidget()
        texture_layout = QHBoxLayout(texture_row)
        texture_layout.setContentsMargins(0, 0, 0, 0)
        self.sprite_texture_field = QLineEdit()
        self.sprite_texture_field.setReadOnly(True)
        self.sprite_texture_button = QPushButton("...")
        self.sprite_texture_button.setFixedWidth(28)
        texture_layout.addWidget(self.sprite_texture_field)
        texture_layout.addWidget(self.sprite_texture_button)
        sprite_form.addRow("Textura", texture_row)
        self.sprite_color_button = QPushButton("Cor")
        sprite_form.addRow("Cor", self.sprite_color_button)
        self.sprite_layer_combo = QComboBox()
        self.sprite_layer_combo.addItems(["Background", "Default", "Foreground", "UI"])
        sprite_form.addRow("Camada", self.sprite_layer_combo)
        self.sprite_order_field = QDoubleSpinBox()
        self.sprite_order_field.setDecimals(0)
        self.sprite_order_field.setRange(-10000, 10000)
        self.sprite_order_field.setKeyboardTracking(False)
        sprite_form.addRow("Ordem", self.sprite_order_field)
        main_layout.addWidget(self.sprite_renderer_body)

        # ------------------ COMPONENTE: AUDIO SOURCE ------------------
        self.audio_source_header = QWidget()
        self.audio_source_header.setObjectName("InspectorComponentHeader")
        self.audio_source_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
        audio_header_layout = QHBoxLayout(self.audio_source_header)
        audio_header_layout.setContentsMargins(6, 4, 6, 4)
        self.show_audio_chk = QCheckBox(component_title("audio", "Audio Source"))
        self.show_audio_chk.setObjectName("InspectorCheckBox")
        self.show_audio_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        audio_header_layout.addWidget(self.show_audio_chk)
        audio_header_layout.addStretch(1)
        self.btn_collapse_audio = QToolButton()
        self.btn_collapse_audio.setText("▼")
        self.btn_collapse_audio.setFixedSize(18, 18)
        self.btn_collapse_audio.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")
        self.btn_delete_audio = QToolButton()
        self.btn_delete_audio.setText("✕")
        self.btn_delete_audio.setFixedSize(18, 18)
        self.btn_delete_audio.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")
        audio_header_layout.addWidget(self.btn_collapse_audio)
        audio_header_layout.addWidget(self.btn_delete_audio)
        main_layout.addWidget(self.audio_source_header)

        self.audio_source_body = QWidget()
        audio_form = QFormLayout(self.audio_source_body)
        audio_form.setContentsMargins(8, 0, 8, 0)
        self.audio_path_combo = QComboBox()
        self.audio_path_combo.setStyleSheet("background-color: #242424; color: #e0e0e0; font-size: 11px;")
        self.audio_path_combo.setFixedHeight(22)
        audio_form.addRow("Áudio", self.audio_path_combo)
        self.audio_volume_field = QDoubleSpinBox()
        self.audio_volume_field.setRange(0.0, 1.0)
        self.audio_volume_field.setSingleStep(0.05)
        self.audio_volume_field.setDecimals(2)
        self.audio_volume_field.setKeyboardTracking(False)
        audio_form.addRow("Volume", self.audio_volume_field)
        self.audio_loop_field = QCheckBox()
        self.audio_autoplay_field = QCheckBox()
        audio_form.addRow("Repetir", self.audio_loop_field)
        audio_form.addRow("Ao iniciar", self.audio_autoplay_field)
        audio_actions = QWidget()
        audio_actions_layout = QHBoxLayout(audio_actions)
        audio_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.audio_test_button = QPushButton("▶ Testar")
        self.audio_stop_button = QPushButton("■ Parar")
        audio_actions_layout.addWidget(self.audio_test_button)
        audio_actions_layout.addWidget(self.audio_stop_button)
        audio_form.addRow("Controles", audio_actions)
        main_layout.addWidget(self.audio_source_body)
        # ------------------ COMPONENTE: RIGIDBODY 2D ------------------
        self.rigidbody_header = QWidget()
        self.rigidbody_header.setObjectName("InspectorComponentHeader")
        self.rigidbody_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
        rb_h_layout = QHBoxLayout(self.rigidbody_header)
        rb_h_layout.setContentsMargins(6, 4, 6, 4)

        self.show_rigidbody_chk = QCheckBox(component_title("rigidbody", "RigidBody 2D"))
        self.show_rigidbody_chk.setObjectName("InspectorCheckBox")
        self.show_rigidbody_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        rb_h_layout.addWidget(self.show_rigidbody_chk)
        rb_h_layout.addStretch()

        self.btn_collapse_rigidbody = QToolButton()
        self.btn_collapse_rigidbody.setText("▼")
        self.btn_collapse_rigidbody.setFixedSize(18, 18)
        self.btn_collapse_rigidbody.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

        self.btn_del_rb = QToolButton()
        self.btn_del_rb.setText("✕")
        self.btn_del_rb.setFixedSize(18, 18)
        self.btn_del_rb.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")

        rb_h_layout.addWidget(self.btn_collapse_rigidbody)
        rb_h_layout.addWidget(self.btn_del_rb)
        main_layout.addWidget(self.rigidbody_header)

        # Widget container para física
        self.rigidbody_body = QWidget()
        rb_body_layout = QVBoxLayout(self.rigidbody_body)
        rb_body_layout.setContentsMargins(0, 0, 0, 0)


        self.physics_fields = {
            "use_gravity": QCheckBox(),
            "is_kinematic": QCheckBox(),
        }
        self.physics_fields["use_gravity"].setObjectName("InspectorCheckBox")
        self.physics_fields["is_kinematic"].setObjectName("InspectorCheckBox")

        physics_widget = QWidget()
        physics_lay = QFormLayout(physics_widget)
        physics_lay.setContentsMargins(8, 0, 8, 0)
        physics_lay.addRow("Usar gravidade", self.physics_fields["use_gravity"])
        physics_lay.addRow("Cinemático", self.physics_fields["is_kinematic"])
        rb_body_layout.addWidget(physics_widget)
        main_layout.addWidget(self.rigidbody_body)

        # ------------------ COMPONENTE: COLLIDER 2D ------------------
        self.collider_header = QWidget()
        self.collider_header.setObjectName("InspectorComponentHeader")
        self.collider_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
        col_h_layout = QHBoxLayout(self.collider_header)
        col_h_layout.setContentsMargins(6, 4, 6, 4)

        self.show_collider_chk = QCheckBox(component_title("collider", "Box/Circle Collider"))
        self.show_collider_chk.setObjectName("InspectorCheckBox")
        self.show_collider_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        col_h_layout.addWidget(self.show_collider_chk)
        col_h_layout.addStretch()

        self.btn_collapse_collider = QToolButton()
        self.btn_collapse_collider.setText("▼")
        self.btn_collapse_collider.setFixedSize(18, 18)
        self.btn_collapse_collider.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

        self.btn_del_col = QToolButton()
        self.btn_del_col.setText("✕")
        self.btn_del_col.setFixedSize(18, 18)
        self.btn_del_col.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")

        col_h_layout.addWidget(self.btn_collapse_collider)
        col_h_layout.addWidget(self.btn_del_col)
        main_layout.addWidget(self.collider_header)

        # Widget container para collider
        self.collider_body = QWidget()
        col_body_layout = QVBoxLayout(self.collider_body)
        col_body_layout.setContentsMargins(0, 0, 0, 0)


        collider_widget = QWidget()
        collider_lay = QFormLayout(collider_widget)
        collider_lay.setContentsMargins(8, 0, 8, 0)

        self.collider_fields: dict[str, QDoubleSpinBox] = {}
        for label, key in (("Collider Largura", "width"), ("Collider Altura", "height"), ("Collider Raio", "radius"), ("Collider Offset X", "offset_x"), ("Collider Offset Y", "offset_y")):
            editor = QDoubleSpinBox()
            editor.setObjectName("InspectorNumberField")
            editor.setDecimals(2)
            editor.setRange(0.01 if key in ("width", "height", "radius") else -100000.0, 100000.0)
            editor.setKeyboardTracking(False)
            self.collider_fields[key] = editor
            collider_lay.addRow(label, editor)
        self.collider_trigger_field = QCheckBox()
        self.collider_trigger_field.setObjectName("InspectorCheckBox")
        collider_lay.addRow("Collider Trigger", self.collider_trigger_field)
        col_body_layout.addWidget(collider_widget)
        main_layout.addWidget(self.collider_body)
        '''Animator 2D foi movido para a aba Animation.
        # ------------------ COMPONENTE: ANIMATOR 2D ------------------
        anim_header = QWidget()
        anim_header.setStyleSheet("background-color: #242424; border-radius: 3px; margin-top: 10px; border-bottom: 1px solid #2b2b2b;")
        anim_h_layout = QHBoxLayout(anim_header)
        anim_h_layout.setContentsMargins(6, 4, 6, 4)

        self.show_animator_chk = QCheckBox("🎬 Animator 2D")
        self.show_animator_chk.setObjectName("InspectorCheckBox")
        self.show_animator_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        anim_h_layout.addWidget(self.show_animator_chk)
        anim_h_layout.addStretch()

        btn_collapse_anim = QToolButton()
        btn_collapse_anim.setText("▼")
        btn_collapse_anim.setFixedSize(18, 18)
        btn_collapse_anim.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

        self.btn_del_anim = QToolButton()
        self.btn_del_anim.setText("✕")
        self.btn_del_anim.setFixedSize(18, 18)
        self.btn_del_anim.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")

        anim_h_layout.addWidget(btn_collapse_anim)
        anim_h_layout.addWidget(self.btn_del_anim)
        main_layout.addWidget(anim_header)

        # Container do corpo do Animator
        self.animator_body = QWidget()
        anim_body_layout = QVBoxLayout(self.animator_body)
        anim_body_layout.setContentsMargins(0, 0, 0, 0)
        btn_collapse_anim.clicked.connect(lambda: self.animator_body.setVisible(not self.animator_body.isVisible()))

        animator_widget = QWidget()
        animator_lay = QFormLayout(animator_widget)
        animator_lay.setContentsMargins(8, 0, 8, 0)

        self.animator_clip_combo = QComboBox()
        self.animator_clip_combo.addItems(["Idle", "Run", "Jump"])
        animator_lay.addRow("Clip Inicial", self.animator_clip_combo)

        self.animator_current_lbl = QLineEdit("Nenhum")
        self.animator_current_lbl.setReadOnly(True)
        animator_lay.addRow("Clip Atual", self.animator_current_lbl)

        self.animator_speed_field = QDoubleSpinBox()
        self.animator_speed_field.setObjectName("InspectorNumberField")
        self.animator_speed_field.setRange(0.0, 100.0)
        self.animator_speed_field.setValue(1.0)
        animator_lay.addRow("Velocidade", self.animator_speed_field)

        clip_actions = QWidget()
        clip_actions_layout = QHBoxLayout(clip_actions)
        clip_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.animator_add_clip_button = QPushButton("+ Clip")
        self.animator_remove_clip_button = QPushButton("− Clip")
        clip_actions_layout.addWidget(self.animator_add_clip_button)
        clip_actions_layout.addWidget(self.animator_remove_clip_button)
        animator_lay.addRow("Clips", clip_actions)

        self.animator_sheet_combo = QComboBox()
        animator_lay.addRow("Sprite Sheet", self.animator_sheet_combo)
        self.animator_frame_width = QDoubleSpinBox()
        self.animator_frame_width.setRange(1, 8192)
        self.animator_frame_width.setDecimals(0)
        self.animator_frame_width.setKeyboardTracking(False)
        animator_lay.addRow("Quadro Largura", self.animator_frame_width)
        self.animator_frame_height = QDoubleSpinBox()
        self.animator_frame_height.setRange(1, 8192)
        self.animator_frame_height.setDecimals(0)
        self.animator_frame_height.setKeyboardTracking(False)
        animator_lay.addRow("Quadro Altura", self.animator_frame_height)
        self.animator_start_frame = QDoubleSpinBox()
        self.animator_start_frame.setRange(0, 100000)
        self.animator_start_frame.setDecimals(0)
        self.animator_start_frame.setKeyboardTracking(False)
        animator_lay.addRow("Quadro Inicial", self.animator_start_frame)
        self.animator_frame_count = QDoubleSpinBox()
        self.animator_frame_count.setRange(1, 100000)
        self.animator_frame_count.setDecimals(0)
        self.animator_frame_count.setKeyboardTracking(False)
        animator_lay.addRow("Quantidade", self.animator_frame_count)
        self.animator_fps_field = QDoubleSpinBox()
        self.animator_fps_field.setRange(0.1, 240.0)
        self.animator_fps_field.setValue(8.0)
        self.animator_fps_field.setKeyboardTracking(False)
        animator_lay.addRow("FPS", self.animator_fps_field)
        self.animator_loop_field = QCheckBox()
        self.animator_loop_field.setChecked(True)
        animator_lay.addRow("Repetir", self.animator_loop_field)
        self.animator_preview = QLabel("Prévia do primeiro quadro")
        self.animator_preview.setAlignment(Qt.AlignCenter)
        self.animator_preview.setMinimumHeight(90)
        self.animator_preview.setStyleSheet("background: #15171c; border: 1px solid #3a3d46; color: #888;")
        animator_lay.addRow("Prévia", self.animator_preview)

        anim_body_layout.addWidget(animator_widget)
        main_layout.addWidget(self.animator_body)
        '''

        # ------------------ COMPONENTE: CAMERA 2D ------------------
        self.camera_header = QWidget()
        self.camera_header.setObjectName("InspectorComponentHeader")
        self.camera_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
        camera_header_layout = QHBoxLayout(self.camera_header)
        camera_header_layout.setContentsMargins(6, 4, 6, 4)
        self.show_camera_chk = QCheckBox(component_title("camera", "Camera 2D"))
        self.show_camera_chk.setObjectName("InspectorCheckBox")
        self.show_camera_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        camera_header_layout.addWidget(self.show_camera_chk)
        camera_header_layout.addStretch(1)
        self.btn_collapse_camera = QToolButton()
        self.btn_collapse_camera.setText("▼")
        self.btn_collapse_camera.setFixedSize(18, 18)
        self.btn_collapse_camera.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")
        self.btn_delete_camera = QToolButton()
        self.btn_delete_camera.setText("✕")
        self.btn_delete_camera.setFixedSize(18, 18)
        self.btn_delete_camera.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")
        camera_header_layout.addWidget(self.btn_collapse_camera)
        camera_header_layout.addWidget(self.btn_delete_camera)
        main_layout.addWidget(self.camera_header)

        self.camera_body = QWidget()
        camera_form = QFormLayout(self.camera_body)
        camera_form.setContentsMargins(8, 0, 8, 0)
        self.camera_active_field = QCheckBox()
        camera_form.addRow("Ativa", self.camera_active_field)
        self.camera_width_field = QDoubleSpinBox()
        self.camera_width_field.setRange(1, 16384)
        self.camera_width_field.setDecimals(0)
        self.camera_width_field.setKeyboardTracking(False)
        camera_form.addRow("Largura", self.camera_width_field)
        self.camera_height_field = QDoubleSpinBox()
        self.camera_height_field.setRange(1, 16384)
        self.camera_height_field.setDecimals(0)
        self.camera_height_field.setKeyboardTracking(False)
        camera_form.addRow("Altura", self.camera_height_field)
        self.camera_zoom_field = QDoubleSpinBox()
        self.camera_zoom_field.setRange(0.1, 20.0)
        self.camera_zoom_field.setSingleStep(0.1)
        self.camera_zoom_field.setKeyboardTracking(False)
        camera_form.addRow("Zoom", self.camera_zoom_field)
        self.camera_follow_combo = QComboBox()
        camera_form.addRow("Seguir", self.camera_follow_combo)
        self.camera_color_button = QPushButton("Cor de fundo")
        camera_form.addRow("Fundo", self.camera_color_button)
        main_layout.addWidget(self.camera_body)

        # ------------------ COMPONENTE: UI NATIVA ------------------
        self.ui_component_header = QWidget()
        self.ui_component_header.setObjectName("InspectorComponentHeader")
        self.ui_component_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
        ui_header_layout = QHBoxLayout(self.ui_component_header)
        ui_header_layout.setContentsMargins(6, 4, 6, 4)
        self.show_ui_chk = QCheckBox(component_title("ui", "UI"))
        self.show_ui_chk.setObjectName("InspectorCheckBox")
        self.show_ui_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        ui_header_layout.addWidget(self.show_ui_chk)
        ui_header_layout.addStretch(1)
        self.btn_collapse_ui = QToolButton()
        self.btn_collapse_ui.setText("▼")
        self.btn_collapse_ui.setFixedSize(18, 18)
        self.btn_collapse_ui.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; padding: 0px;")
        self.btn_delete_ui = QToolButton()
        self.btn_delete_ui.setText("✕")
        self.btn_delete_ui.setFixedSize(18, 18)
        self.btn_delete_ui.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold; border: none !important; padding: 0px;")
        ui_header_layout.addWidget(self.btn_collapse_ui)
        ui_header_layout.addWidget(self.btn_delete_ui)
        main_layout.addWidget(self.ui_component_header)

        self.ui_component_body = QWidget()
        self.ui_component_form = QFormLayout(self.ui_component_body)
        self.ui_component_form.setContentsMargins(8, 0, 8, 0)
        self.ui_type_field = QLineEdit()
        self.ui_type_field.setReadOnly(True)
        self.ui_component_form.addRow("Tipo", self.ui_type_field)
        self.ui_text_field = QLineEdit()
        self.ui_component_form.addRow("Texto", self.ui_text_field)
        self.ui_position_fields = {}
        for label, key in (("Posição X", "x"), ("Posição Y", "y"), ("Largura", "width"), ("Altura", "height"), ("Ordem", "z_order"), ("Fonte", "font_size"), ("Opacidade", "alpha")):
            field = QDoubleSpinBox()
            field.setDecimals(0)
            field.setRange(-100000.0 if key in {"x", "y", "z_order"} else 0.0, 100000.0 if key != "alpha" else 255.0)
            field.setKeyboardTracking(False)
            self.ui_position_fields[key] = field
            self.ui_component_form.addRow(label, field)
        self.ui_color_button = QPushButton("Cor")
        self.ui_component_form.addRow("Cor", self.ui_color_button)
        ui_image_row = QWidget()
        ui_image_layout = QHBoxLayout(ui_image_row)
        ui_image_layout.setContentsMargins(0, 0, 0, 0)
        self.ui_image_path_field = QLineEdit()
        self.ui_image_path_field.setReadOnly(True)
        self.ui_image_button = QPushButton("...")
        self.ui_image_button.setFixedWidth(28)
        ui_image_layout.addWidget(self.ui_image_path_field)
        ui_image_layout.addWidget(self.ui_image_button)
        self.ui_component_form.addRow("Imagem", ui_image_row)
        self.ui_interactable_field = QCheckBox()
        self.ui_component_form.addRow("Interativo", self.ui_interactable_field)
        self.ui_event_field = QLineEdit()
        self.ui_component_form.addRow("Evento", self.ui_event_field)
        self.ui_target_combo = QComboBox()
        self.ui_component_form.addRow("Alvo", self.ui_target_combo)
        main_layout.addWidget(self.ui_component_body)

        # ------------------ COMPONENTE: LÓGICA VISUAL ------------------
        self.logic_component_header = QWidget()
        self.logic_component_header.setObjectName("InspectorComponentHeader")
        logic_header_layout = QHBoxLayout(self.logic_component_header)
        logic_header_layout.setContentsMargins(6, 4, 6, 4)
        logic_title = QLabel(component_title("logic", "Lógica Visual"))
        logic_title.setObjectName("InspectorComponentTitle")
        logic_header_layout.addWidget(logic_title)
        logic_header_layout.addStretch(1)
        self.btn_collapse_logic = QToolButton()
        self.btn_collapse_logic.setText("▶")
        self.btn_collapse_logic.setFixedSize(18, 18)
        self.btn_collapse_logic.setObjectName("InspectorFoldoutButton")
        self.btn_delete_logic = QToolButton()
        self.btn_delete_logic.setText("✕")
        self.btn_delete_logic.setFixedSize(18, 18)
        self.btn_delete_logic.setObjectName("InspectorDangerButton")
        self.btn_delete_logic.setToolTip("Desvincular todos os Logic Graphs deste objeto")
        logic_header_layout.addWidget(self.btn_collapse_logic)
        logic_header_layout.addWidget(self.btn_delete_logic)
        main_layout.addWidget(self.logic_component_header)

        self.logic_component_body = QWidget()
        logic_body_layout = QVBoxLayout(self.logic_component_body)
        logic_body_layout.setContentsMargins(8, 6, 8, 8)
        logic_body_layout.setSpacing(6)
        self.logic_status_label = QLabel("Nenhum Logic Graph vinculado")
        self.logic_status_label.setObjectName("WorkspaceContext")
        logic_body_layout.addWidget(self.logic_status_label)
        self.logic_graph_combo = QComboBox()
        self.logic_graph_combo.setToolTip("Logic Graphs que controlam o objeto selecionado")
        logic_body_layout.addWidget(self.logic_graph_combo)
        self.logic_summary_label = QLabel("Selecione um grafo para ver seus eventos e blocos.")
        self.logic_summary_label.setWordWrap(True)
        self.logic_summary_label.setObjectName("PanelHint")
        logic_body_layout.addWidget(self.logic_summary_label)
        logic_primary_actions = QHBoxLayout()
        self.logic_open_button = QPushButton("Editar / Receitas")
        self.logic_open_button.setToolTip("Abra o grafo e use receitas pesquisáveis para aprender novas lógicas")
        self.logic_open_button.setProperty("uiRole", "primary")
        self.logic_link_button = QPushButton("Vincular outro")
        logic_primary_actions.addWidget(self.logic_open_button)
        logic_primary_actions.addWidget(self.logic_link_button)
        logic_body_layout.addLayout(logic_primary_actions)
        logic_secondary_actions = QHBoxLayout()
        self.logic_new_button = QPushButton("Criar novo")
        self.logic_unlink_button = QPushButton("Desvincular")
        self.logic_unlink_button.setProperty("uiRole", "danger")
        logic_secondary_actions.addWidget(self.logic_new_button)
        logic_secondary_actions.addWidget(self.logic_unlink_button)
        logic_body_layout.addLayout(logic_secondary_actions)
        main_layout.addWidget(self.logic_component_body)

        # ------------------ PLAY MODE: ORIGEM E MOVIMENTOS ------------------
        self.runtime_debug_header = QWidget()
        self.runtime_debug_header.setObjectName("InspectorComponentHeader")
        runtime_header_layout = QHBoxLayout(self.runtime_debug_header)
        runtime_header_layout.setContentsMargins(6, 4, 6, 4)
        runtime_title = QLabel("▶  Runtime / Logic Debug")
        runtime_title.setObjectName("InspectorComponentTitle")
        runtime_header_layout.addWidget(runtime_title)
        runtime_header_layout.addStretch(1)
        self.btn_collapse_runtime = QToolButton()
        self.btn_collapse_runtime.setText("▼")
        self.btn_collapse_runtime.setFixedSize(18, 18)
        self.btn_collapse_runtime.setObjectName("InspectorFoldoutButton")
        runtime_header_layout.addWidget(self.btn_collapse_runtime)
        main_layout.addWidget(self.runtime_debug_header)

        self.runtime_debug_body = QWidget()
        runtime_body_layout = QVBoxLayout(self.runtime_debug_body)
        runtime_body_layout.setContentsMargins(8, 6, 8, 8)
        self.runtime_debug_label = QLabel("Sem dados de execução")
        self.runtime_debug_label.setObjectName("InspectorRuntimeDetails")
        self.runtime_debug_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.runtime_debug_label.setWordWrap(True)
        runtime_body_layout.addWidget(self.runtime_debug_label)
        main_layout.addWidget(self.runtime_debug_body)

        for component_body in (
            self.transform_body, self.sprite_renderer_body, self.audio_source_body,
            self.rigidbody_body, self.collider_body, self.camera_body,
            self.ui_component_body, self.logic_component_body,
            self.runtime_debug_body,
        ):
            component_body.setObjectName("InspectorComponentBody")
            component_body.setStyleSheet(
                "#InspectorComponentBody { background: #202228; border-left: 1px solid #30343c; "
                "border-right: 1px solid #30343c; border-bottom: 1px solid #30343c; }"
            )

        # O cabeçalho e corpo de scripts/custom agora são inseridos de forma modular dinâmica para cada script ativo
        self.script_containers = []

        self.add_component_button = QPushButton("＋ Adicionar Componente")
        self.add_component_button.setObjectName("InspectorAddComponentButton")
        self.add_component_button.setMinimumHeight(30)
        main_layout.addWidget(self.add_component_button)

        main_layout.addStretch(1)

        # Inspector respirável e redimensionável; não trava mais toda a interface em 290 px.
        inspector.setMinimumWidth(310)
        self.inspector_dock.setMinimumWidth(325)
        self.inspector_dock.resize(350, self.inspector_dock.height())
        scroll.setWidget(inspector)
        self.inspector_dock.setWidget(scroll)

        console_panel = QWidget()
        console_panel.setObjectName("ConsolePanel")
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(6, 6, 6, 6)
        console_layout.setSpacing(5)
        console_toolbar = QWidget()
        console_toolbar.setObjectName("ConsoleToolbar")
        console_filters = QHBoxLayout(console_toolbar)
        console_filters.setContentsMargins(6, 3, 6, 3)
        self.console_level_checks = {}
        for level in ("INFO", "WARNING", "ERROR"):
            check = QCheckBox(level)
            check.setChecked(True)
            self.console_level_checks[level] = check
            console_filters.addWidget(check)
        console_filters.addStretch(1)
        self.console_clear_button = QPushButton("Limpar")
        self.console_clear_button.setFixedHeight(22)
        console_filters.addWidget(self.console_clear_button)
        console_layout.addWidget(console_toolbar)

        console = QPlainTextEdit()
        self.console_output = console
        console.setObjectName("ConsoleOutput")
        console.setReadOnly(True)
        console_layout.addWidget(console)
        self.profiler_label = QLabel("FPS: --\nObjetos: 0\nModo: EDIT")
        self.profiler_label.setObjectName("ProfilerMetric")
        self.profiler_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        profiler = QFrame()
        profiler.setObjectName("ProfilerPanel")
        profiler_layout = QVBoxLayout(profiler)
        profiler_layout.setContentsMargins(10, 10, 10, 10)
        profiler_layout.addWidget(self.profiler_label)
        profiler_layout.addStretch(1)

        console_tabs = QTabWidget()
        console_tabs.setObjectName("BottomPanelTabs")
        console_tabs.addTab(console_panel, "Console")
        console_tabs.addTab(
            EmptyStateWidget("Nenhuma saída disponível", "Mensagens do runtime aparecerão aqui.", "▤"),
            "Saída",
        )
        console_tabs.addTab(
            EmptyStateWidget("Depurador inativo", "Inicie o Play Mode para acompanhar a execução.", "◇"),
            "Depurador",
        )

        # Asset Preview aprimorado (Layout Horizontal: Imagem/Ícone à Esquerda, Detalhes à Direita)
        preview = QWidget()
        preview.setObjectName("AssetPreviewPanel")
        preview_layout = QHBoxLayout(preview)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(15)

        # Container da miniatura (lado esquerdo)
        self.preview_label = QLabel("Selecione um asset\npara visualizar")
        self.preview_label.setObjectName("AssetPreviewThumbnail")
        self.preview_label.setProperty("uiState", "empty")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(128, 104)
        self.preview_label.setMaximumWidth(180)
        self.preview_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        preview_layout.addWidget(self.preview_label)

        # Container dos metadados (lado direito)
        self.preview_details_label = QLabel()
        self.preview_details_label.setObjectName("AssetPreviewDetails")
        self.preview_details_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.preview_details_label.setWordWrap(True)
        self.preview_details_label.setText("<b>Nenhum asset selecionado</b><br><br>Selecione uma imagem, script, cena ou áudio na árvore de Assets para ver as informações detalhadas e pré-visualizar.")
        preview_layout.addWidget(self.preview_details_label, 1)

        console_row = QSplitter(Qt.Horizontal)
        console_row.addWidget(console_tabs)
        console_row.addWidget(profiler)
        console_row.setSizes([650, 240])

        center = QSplitter(Qt.Vertical)
        center.setChildrenCollapsible(False)
        center.addWidget(self.center_container)
        center.addWidget(console_row)
        center.addWidget(preview)
        center.setSizes([560, 150, 150])

        main = QSplitter(Qt.Horizontal)
        main.setChildrenCollapsible(False)
        main.addWidget(left)
        main.addWidget(center)
        main.setStretchFactor(1, 1)
        main.setSizes([270, 1170])
        self.main_splitter = main
        self.setCentralWidget(main)

    def _dock(self, title: str, widget: QWidget, area: Qt.DockWidgetArea, width: int) -> None:
        dock = QDockWidget(title, self)
        dock.setObjectName(f"SmokeTest_{title}")
        dock.setWidget(widget)
        dock.setMinimumWidth(width if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea) else 200)
        self.addDockWidget(area, dock)

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        return EmptyStateWidget(text or "Nenhum conteúdo", "Este painel ainda não possui dados.")


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    from editor.ui import apply_editor_theme
    apply_editor_theme(app)
    window = InterfaceSmokeTest()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
