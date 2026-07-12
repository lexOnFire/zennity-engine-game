"""Teste isolado da interface do Zennity Editor, sem Pygame ou Viewport.

Execute a partir da raiz do projeto:
    python -m editor.interface_smoke_test
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
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
    QSplitter,
    QTabWidget,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


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
        self.addToolBar(toolbar)
        self.toolbar_actions = {}
        icons = {
            "Novo": "📋", "Abrir": "📂", "Salvar": "💾",
            "Desfazer": "↶", "Refazer": "↷", "Select": "⛶",
            "Move": "✛", "Rotate": "🔄", "Scale": "📐",
            "Snap: OFF": "⚙️", "Play": "▶️", "Pause": "⏸️", "Stop": "⏹️",
        }
        for label, icon in icons.items():
            action = QAction(icon, self)
            action.setStatusTip(label)
            action.setToolTip(label)
            self.toolbar_actions[label] = action
            toolbar.addAction(action)
        toolbar.addSeparator()
        mode = QComboBox()
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
        hierarchy.setHeaderHidden(True)
        root = QTreeWidgetItem(["MainScene"])
        environment = QTreeWidgetItem(["Environment"])
        environment.addChildren([QTreeWidgetItem(["DirectionalLight"]), QTreeWidgetItem(["Terrain"])])
        root.addChildren([environment, QTreeWidgetItem(["Chao"]), QTreeWidgetItem(["Player"]), QTreeWidgetItem(["Enemies"])])
        hierarchy.addTopLevelItem(root)
        hierarchy.expandAll()

        assets = QTreeWidget()
        self.assets_tree = assets
        assets.setHeaderHidden(True)
        asset_root = QTreeWidgetItem(["Assets"])
        asset_root.addChildren([QTreeWidgetItem(["Scenes"]), QTreeWidgetItem(["Scripts"]), QTreeWidgetItem(["Textures"]), QTreeWidgetItem(["Audio"])])
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
        hierarchy_tabs.addTab(hierarchy, "Hierarchy")
        hierarchy_tabs.addTab(create_panel, "Criar")

        prefab_tree = QTreeWidget()
        self.prefab_tree = prefab_tree
        prefab_tree.setHeaderHidden(True)
        prefab_tree.addTopLevelItem(QTreeWidgetItem(["Prefabs disponíveis no projeto"] ))
        asset_tabs = QTabWidget()
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
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #1c1c1c; }")

        inspector = QWidget()
        self.inspector_panel = inspector
        inspector.setStyleSheet("background-color: #1c1c1c;")
        main_layout = QVBoxLayout(inspector)
        self.inspector_layout = main_layout
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(10)

        # BARRA DE TÍTULO CUSTOMIZADA DO INSPECTOR (Com botões de encolher, desgrudar/flutuar, acoplar)
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: #2b2b2b; border-radius: 4px; border: 1px solid #3d3d3d;")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(6, 4, 6, 4)

        inspector_lbl = QLabel("🔍 INSPECTOR")
        inspector_lbl.setStyleSheet("font-weight: bold; color: #4caf50; font-size: 11px;")
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
            btn.setStyleSheet("background-color: #202020; color: #ffffff; border: 1px solid #444; border-radius: 2px; font-size: 10px; font-weight: bold;")
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
        self.inspector_name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")

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
        trans_header = QWidget()
        trans_header.setStyleSheet("background-color: #242424; border-radius: 3px; border-bottom: 1px solid #2b2b2b;")
        trans_h_layout = QHBoxLayout(trans_header)
        trans_h_layout.setContentsMargins(6, 4, 6, 4)

        # Símbolo expansor e ícone
        trans_title = QLabel("🏃 Transform")
        trans_title.setStyleSheet("font-weight: bold; color: #ffffff;")
        trans_h_layout.addWidget(trans_title)
        trans_h_layout.addStretch()

        # Botões de encolher e excluir
        btn_collapse_trans = QToolButton()
        btn_collapse_trans.setText("▼")
        btn_collapse_trans.setFixedSize(18, 18)
        btn_collapse_trans.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

        btn_del_trans = QToolButton()
        btn_del_trans.setText("✕")
        btn_del_trans.setFixedSize(18, 18)
        btn_del_trans.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")

        trans_h_layout.addWidget(btn_collapse_trans)
        trans_h_layout.addWidget(btn_del_trans)
        main_layout.addWidget(trans_header)

        # Widget container para as propriedades do Transform (encolhível)
        trans_body = QWidget()
        trans_body_layout = QVBoxLayout(trans_body)
        trans_body_layout.setContentsMargins(0, 0, 0, 0)
        trans_body_layout.setSpacing(6)

        # Conecta as ações
        btn_collapse_trans.clicked.connect(lambda: trans_body.setVisible(not trans_body.isVisible()))

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
        main_layout.addWidget(trans_body)

        # ------------------ COMPONENTE: SPRITE RENDERER ------------------
        sprite_header = QWidget()
        sprite_header.setStyleSheet("background-color: #242424; border-radius: 3px; margin-top: 10px; border-bottom: 1px solid #2b2b2b;")
        sprite_header_layout = QHBoxLayout(sprite_header)
        sprite_header_layout.setContentsMargins(6, 4, 6, 4)
        self.show_renderer_chk = QCheckBox("🖼 Sprite Renderer")
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
        main_layout.addWidget(sprite_header)

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
        audio_header = QWidget()
        audio_header.setStyleSheet("background-color: #242424; border-radius: 3px; margin-top: 10px; border-bottom: 1px solid #2b2b2b;")
        audio_header_layout = QHBoxLayout(audio_header)
        audio_header_layout.setContentsMargins(6, 4, 6, 4)
        self.show_audio_chk = QCheckBox("🔊 Audio Source")
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
        main_layout.addWidget(audio_header)

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
        main_layout.addWidget(self.audio_source_body)
        # ------------------ COMPONENTE: RIGIDBODY 2D ------------------
        rb_header = QWidget()
        rb_header.setStyleSheet("background-color: #242424; border-radius: 3px; margin-top: 10px; border-bottom: 1px solid #2b2b2b;")
        rb_h_layout = QHBoxLayout(rb_header)
        rb_h_layout.setContentsMargins(6, 4, 6, 4)

        self.show_rigidbody_chk = QCheckBox("⚙️ RigidBody 2D")
        self.show_rigidbody_chk.setObjectName("InspectorCheckBox")
        self.show_rigidbody_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        rb_h_layout.addWidget(self.show_rigidbody_chk)
        rb_h_layout.addStretch()

        btn_collapse_rb = QToolButton()
        btn_collapse_rb.setText("▼")
        btn_collapse_rb.setFixedSize(18, 18)
        btn_collapse_rb.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

        self.btn_del_rb = QToolButton()
        self.btn_del_rb.setText("✕")
        self.btn_del_rb.setFixedSize(18, 18)
        self.btn_del_rb.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")

        rb_h_layout.addWidget(btn_collapse_rb)
        rb_h_layout.addWidget(self.btn_del_rb)
        main_layout.addWidget(rb_header)

        # Widget container para física
        rb_body = QWidget()
        rb_body_layout = QVBoxLayout(rb_body)
        rb_body_layout.setContentsMargins(0, 0, 0, 0)

        btn_collapse_rb.clicked.connect(lambda: rb_body.setVisible(not rb_body.isVisible()))

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
        main_layout.addWidget(rb_body)

        # ------------------ COMPONENTE: COLLIDER 2D ------------------
        col_header = QWidget()
        col_header.setStyleSheet("background-color: #242424; border-radius: 3px; margin-top: 10px; border-bottom: 1px solid #2b2b2b;")
        col_h_layout = QHBoxLayout(col_header)
        col_h_layout.setContentsMargins(6, 4, 6, 4)

        self.show_collider_chk = QCheckBox("🟢 Box/Circle Collider")
        self.show_collider_chk.setObjectName("InspectorCheckBox")
        self.show_collider_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        col_h_layout.addWidget(self.show_collider_chk)
        col_h_layout.addStretch()

        btn_collapse_col = QToolButton()
        btn_collapse_col.setText("▼")
        btn_collapse_col.setFixedSize(18, 18)
        btn_collapse_col.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

        self.btn_del_col = QToolButton()
        self.btn_del_col.setText("✕")
        self.btn_del_col.setFixedSize(18, 18)
        self.btn_del_col.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")

        col_h_layout.addWidget(btn_collapse_col)
        col_h_layout.addWidget(self.btn_del_col)
        main_layout.addWidget(col_header)

        # Widget container para collider
        col_body = QWidget()
        col_body_layout = QVBoxLayout(col_body)
        col_body_layout.setContentsMargins(0, 0, 0, 0)

        btn_collapse_col.clicked.connect(lambda: col_body.setVisible(not col_body.isVisible()))

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
        main_layout.addWidget(col_body)
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

        anim_body_layout.addWidget(animator_widget)
        main_layout.addWidget(self.animator_body)

        # ------------------ COMPONENTE: CAMERA 2D ------------------
        camera_header = QWidget()
        camera_header.setStyleSheet("background-color: #242424; border-radius: 3px; margin-top: 10px; border-bottom: 1px solid #2b2b2b;")
        camera_header_layout = QHBoxLayout(camera_header)
        camera_header_layout.setContentsMargins(6, 4, 6, 4)
        self.show_camera_chk = QCheckBox("📷 Camera 2D")
        self.show_camera_chk.setObjectName("InspectorCheckBox")
        self.show_camera_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
        camera_header_layout.addWidget(self.show_camera_chk)
        camera_header_layout.addStretch(1)
        self.btn_collapse_camera = QToolButton()
        self.btn_collapse_camera.setText("▼")
        self.btn_collapse_camera.setFixedSize(18, 18)
        self.btn_delete_camera = QToolButton()
        self.btn_delete_camera.setText("✕")
        self.btn_delete_camera.setFixedSize(18, 18)
        self.btn_delete_camera.setStyleSheet("color: #ff5555; background: transparent; border: none; font-weight: bold;")
        camera_header_layout.addWidget(self.btn_collapse_camera)
        camera_header_layout.addWidget(self.btn_delete_camera)
        main_layout.addWidget(camera_header)

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

        # O cabeçalho e corpo de scripts/custom agora são inseridos de forma modular dinâmica para cada script ativo
        self.script_containers = []

        self.add_component_button = QPushButton("Adicionar Componente")
        self.add_component_button.setObjectName("InspectorAddComponentButton")
        main_layout.addWidget(self.add_component_button)

        main_layout.addStretch(1)

        # Tamanho máximo e mínimo fixado para manter proporção perfeita do painel lateral
        inspector.setFixedWidth(280)
        self.inspector_dock.setFixedWidth(290)
        scroll.setWidget(inspector)
        self.inspector_dock.setWidget(scroll)

        console_panel = QWidget()
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(4, 4, 4, 4)
        console_layout.setSpacing(3)
        console_filters = QHBoxLayout()
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
        console_layout.addLayout(console_filters)

        console = QPlainTextEdit()
        self.console_output = console
        console.setReadOnly(True)
        console_layout.addWidget(console)
        self.profiler_label = QLabel("FPS: --\nObjetos: 0\nModo: EDIT")
        self.profiler_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        profiler = self._placeholder("")
        profiler.layout().addWidget(self.profiler_label)

        console_tabs = QTabWidget()
        console_tabs.addTab(console_panel, "Console")
        console_tabs.addTab(self._placeholder("Saída da engine"), "Saída")
        console_tabs.addTab(self._placeholder("Depurador"), "Depurador")

        # Asset Preview aprimorado (Layout Horizontal: Imagem/Ícone à Esquerda, Detalhes à Direita)
        preview = QWidget()
        preview.setObjectName("PremiumPanel")
        preview_layout = QHBoxLayout(preview)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(15)

        # Container da miniatura (lado esquerdo)
        self.preview_label = QLabel("Selecione um asset\npara visualizar")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFixedSize(140, 120)
        self.preview_label.setStyleSheet("background-color: #121212; border: 1px dashed #3a3a3a; border-radius: 4px; color: #888888;")
        preview_layout.addWidget(self.preview_label)

        # Container dos metadados (lado direito)
        self.preview_details_label = QLabel()
        self.preview_details_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.preview_details_label.setStyleSheet("color: #e2e2e2; font-size: 11px; line-height: 140%;")
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
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #aeb6c2;")
        layout.addWidget(label)
        return frame


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = InterfaceSmokeTest()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
