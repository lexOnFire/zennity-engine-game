
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDockWidget, QDoubleSpinBox,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPlainTextEdit, QPushButton, QScrollArea, QSlider, QSizePolicy,
    QSplitter, QTabWidget, QToolBar, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)
from editor.ui.icons import TOOLBAR_ICONS, component_title, editor_icon
from editor.ui.empty_state import EmptyStateWidget
from editor.widgets.logic_graph_editor import LogicGraphEditor
from editor.interface_smoke_test import DetachedWorkspaceWindow

def _build_inspector_shell(window):
    # Criação do Inspector como QDockWidget para habilitar desgrudar/flutuar e encolher/fechar
    window.inspector_dock = QDockWidget("Inspector", window)
    window.inspector_dock.setObjectName("InspectorDock")
    window.inspector_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
    window.addDockWidget(Qt.RightDockWidgetArea, window.inspector_dock)

    # QScrollArea para evitar que a janela fique apertada e bagunçada
    scroll = QScrollArea()
    scroll.setObjectName("InspectorScrollArea")
    scroll.setWidgetResizable(True)

    inspector = QWidget()
    window.inspector_panel = inspector
    inspector.setObjectName("InspectorPanel")
    main_layout = QVBoxLayout(inspector)
    window.inspector_layout = main_layout
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
    window.btn_collapse_dock = QPushButton("▼") # Encolher
    window.btn_collapse_dock.setToolTip("Ocultar Painel")
    window.btn_float_dock = QPushButton("⎋")      # Desgrudar / Flutuar
    window.btn_float_dock.setToolTip("Desgrudar/Flutuar Janela")
    window.btn_dock_dock = QPushButton("⚓")       # Acoplar / Travar
    window.btn_dock_dock.setToolTip("Acoplar no Editor")

    for btn in (window.btn_collapse_dock, window.btn_float_dock, window.btn_dock_dock):
        btn.setFixedSize(20, 20)
        btn.setObjectName("InspectorPanelControl")
        btn.setProperty("uiRole", "icon")
        title_bar_layout.addWidget(btn)

    # Conecta as ações nos botões customizados
    window.btn_collapse_dock.clicked.connect(lambda: window.inspector_panel.setVisible(not window.inspector_panel.isVisible()))
    window.btn_float_dock.clicked.connect(lambda: window.inspector_dock.setFloating(True))
    window.btn_dock_dock.clicked.connect(lambda: window.inspector_dock.setFloating(False))

    main_layout.addWidget(title_bar)

    # Cabeçalho do Objeto (Player, Estático, etc.)
    obj_header = QWidget()
    obj_header_layout = QHBoxLayout(obj_header)
    obj_header_layout.setContentsMargins(0, 0, 0, 0)

    window.inspector_name_label = QLabel("Player")
    window.inspector_name_label.setObjectName("InspectorObjectName")

    window.static_checkbox = QCheckBox("Estático")
    window.static_checkbox.setObjectName("InspectorCheckBox")

    obj_header_layout.addWidget(window.inspector_name_label)
    obj_header_layout.addWidget(window.static_checkbox)
    main_layout.addWidget(obj_header)

    # Tag & Layer rows
    tag_layer = QWidget()
    tag_layer_layout = QHBoxLayout(tag_layer)
    tag_layer_layout.setContentsMargins(0, 0, 0, 0)
    tag_layer_layout.addWidget(QLabel("Tag"))
    window.tag_combo = QComboBox()
    window.tag_combo.addItems(["Player", "Untagged", "MainCamera", "Enemy"])
    tag_layer_layout.addWidget(window.tag_combo)
    tag_layer_layout.addWidget(QLabel("Layer"))
    window.layer_combo = QComboBox()
    window.layer_combo.addItems(["Default", "UI", "Water", "Ignore Raycast"])
    tag_layer_layout.addWidget(window.layer_combo)
    main_layout.addWidget(tag_layer)

    return scroll, inspector, main_layout

def _build_transform_component(window, main_layout):
    # ------------------ COMPONENTE: TRANSFORM (Organização Horizontal X, Y, Z Exata) ------------------
    window.transform_header = QWidget()
    window.transform_header.setObjectName("InspectorComponentHeader")
    window.transform_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
    trans_h_layout = QHBoxLayout(window.transform_header)
    trans_h_layout.setContentsMargins(6, 4, 6, 4)

    # Símbolo expansor e ícone
    trans_title = QLabel(component_title("transform", "Transform"))
    trans_title.setStyleSheet("font-weight: bold; color: #ffffff;")
    trans_h_layout.addWidget(trans_title)
    trans_h_layout.addStretch()

    # Botões de encolher e excluir
    window.btn_collapse_transform = QToolButton()
    window.btn_collapse_transform.setText("▼")
    window.btn_collapse_transform.setFixedSize(18, 18)
    window.btn_collapse_transform.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

    trans_h_layout.addWidget(window.btn_collapse_transform)
    main_layout.addWidget(window.transform_header)

    # Widget container para as propriedades do Transform (encolhível)
    window.transform_body = QWidget()
    trans_body_layout = QVBoxLayout(window.transform_body)
    trans_body_layout.setContentsMargins(0, 0, 0, 0)
    trans_body_layout.setSpacing(6)

    # Conecta as ações

    window.inspector_fields: dict[str, QDoubleSpinBox] = {}

    # 1. Posição
    pos_widget = QWidget()
    pos_layout = QHBoxLayout(pos_widget)
    pos_layout.setContentsMargins(4, 0, 4, 0)
    pos_lbl = QLabel("Posição")
    pos_lbl.setMinimumWidth(50)
    pos_layout.addWidget(pos_lbl)

    window.inspector_fields["x"] = QDoubleSpinBox()
    window.inspector_fields["x"].setObjectName("InspectorNumberField")
    window.inspector_fields["x"].setButtonSymbols(QDoubleSpinBox.NoButtons)
    window.inspector_fields["x"].setDecimals(2)
    window.inspector_fields["x"].setRange(-100000.0, 100000.0)
    window.inspector_fields["x"].setKeyboardTracking(False)
    pos_layout.addWidget(QLabel("X"))
    pos_layout.addWidget(window.inspector_fields["x"])

    window.inspector_fields["y"] = QDoubleSpinBox()
    window.inspector_fields["y"].setObjectName("InspectorNumberField")
    window.inspector_fields["y"].setButtonSymbols(QDoubleSpinBox.NoButtons)
    window.inspector_fields["y"].setDecimals(2)
    window.inspector_fields["y"].setRange(-100000.0, 100000.0)
    window.inspector_fields["y"].setKeyboardTracking(False)
    pos_layout.addWidget(QLabel("Y"))
    pos_layout.addWidget(window.inspector_fields["y"])

    pos_z = QDoubleSpinBox()
    pos_z.setObjectName("InspectorNumberField")
    pos_z.setButtonSymbols(QDoubleSpinBox.NoButtons)
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
    rot_x.setButtonSymbols(QDoubleSpinBox.NoButtons)
    rot_x.setDecimals(2)
    rot_x.setValue(0.00)
    rot_x.setEnabled(False)
    rot_layout.addWidget(QLabel("X"))
    rot_layout.addWidget(rot_x)

    rot_y = QDoubleSpinBox()
    rot_y.setObjectName("InspectorNumberField")
    rot_y.setButtonSymbols(QDoubleSpinBox.NoButtons)
    rot_y.setDecimals(2)
    rot_y.setValue(0.00)
    rot_y.setEnabled(False)
    rot_layout.addWidget(QLabel("Y"))
    rot_layout.addWidget(rot_y)

    window.inspector_fields["rotation"] = QDoubleSpinBox()
    window.inspector_fields["rotation"].setObjectName("InspectorNumberField")
    window.inspector_fields["rotation"].setButtonSymbols(QDoubleSpinBox.NoButtons)
    window.inspector_fields["rotation"].setDecimals(2)
    window.inspector_fields["rotation"].setRange(-100000.0, 100000.0)
    window.inspector_fields["rotation"].setKeyboardTracking(False)
    rot_layout.addWidget(QLabel("Z"))
    rot_layout.addWidget(window.inspector_fields["rotation"])

    trans_body_layout.addWidget(rot_widget)

    # 3. Escala
    scale_widget = QWidget()
    scale_layout = QHBoxLayout(scale_widget)
    scale_layout.setContentsMargins(4, 0, 4, 0)
    scale_lbl = QLabel("Escala")
    scale_lbl.setMinimumWidth(50)
    scale_layout.addWidget(scale_lbl)

    window.inspector_fields["w"] = QDoubleSpinBox()
    window.inspector_fields["w"].setObjectName("InspectorNumberField")
    window.inspector_fields["w"].setButtonSymbols(QDoubleSpinBox.NoButtons)
    window.inspector_fields["w"].setDecimals(2)
    window.inspector_fields["w"].setRange(1.0, 100000.0)
    window.inspector_fields["w"].setKeyboardTracking(False)
    scale_layout.addWidget(QLabel("X"))
    scale_layout.addWidget(window.inspector_fields["w"])

    window.inspector_fields["h"] = QDoubleSpinBox()
    window.inspector_fields["h"].setObjectName("InspectorNumberField")
    window.inspector_fields["h"].setButtonSymbols(QDoubleSpinBox.NoButtons)
    window.inspector_fields["h"].setDecimals(2)
    window.inspector_fields["h"].setRange(1.0, 100000.0)
    window.inspector_fields["h"].setKeyboardTracking(False)
    scale_layout.addWidget(QLabel("Y"))
    scale_layout.addWidget(window.inspector_fields["h"])

    scale_z = QDoubleSpinBox()
    scale_z.setObjectName("InspectorNumberField")
    scale_z.setButtonSymbols(QDoubleSpinBox.NoButtons)
    scale_z.setDecimals(2)
    scale_z.setValue(1.00)
    scale_z.setEnabled(False)
    scale_layout.addWidget(QLabel("Z"))
    scale_layout.addWidget(scale_z)

    trans_body_layout.addWidget(scale_widget)
    main_layout.addWidget(window.transform_body)


def _build_sprite_component(window, main_layout):
    # ------------------ COMPONENTE: SPRITE RENDERER ------------------
    window.sprite_renderer_header = QWidget()
    window.sprite_renderer_header.setObjectName("InspectorComponentHeader")
    window.sprite_renderer_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
    sprite_header_layout = QHBoxLayout(window.sprite_renderer_header)
    sprite_header_layout.setContentsMargins(6, 4, 6, 4)
    window.show_renderer_chk = QCheckBox(component_title("sprite", "Sprite Renderer"))
    window.show_renderer_chk.setObjectName("InspectorCheckBox")
    window.show_renderer_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
    sprite_header_layout.addWidget(window.show_renderer_chk)
    sprite_header_layout.addStretch(1)
    window.btn_collapse_renderer = QToolButton()
    window.btn_collapse_renderer.setText("▼")
    window.btn_collapse_renderer.setFixedSize(18, 18)
    window.btn_collapse_renderer.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")
    window.btn_delete_renderer = QToolButton()
    window.btn_delete_renderer.setText("✕")
    window.btn_delete_renderer.setFixedSize(18, 18)
    window.btn_delete_renderer.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")
    sprite_header_layout.addWidget(window.btn_collapse_renderer)
    sprite_header_layout.addWidget(window.btn_delete_renderer)
    main_layout.addWidget(window.sprite_renderer_header)

    window.sprite_renderer_body = QWidget()
    sprite_form = QFormLayout(window.sprite_renderer_body)
    sprite_form.setContentsMargins(8, 0, 8, 0)
    texture_row = QWidget()
    texture_layout = QHBoxLayout(texture_row)
    texture_layout.setContentsMargins(0, 0, 0, 0)
    window.sprite_texture_field = QLineEdit()
    window.sprite_texture_field.setReadOnly(True)
    window.sprite_texture_button = QPushButton("...")
    window.sprite_texture_button.setFixedWidth(28)
    texture_layout.addWidget(window.sprite_texture_field)
    texture_layout.addWidget(window.sprite_texture_button)
    sprite_form.addRow("Textura", texture_row)
    window.sprite_color_button = QPushButton("Cor")
    sprite_form.addRow("Cor", window.sprite_color_button)
    window.sprite_layer_combo = QComboBox()
    window.sprite_layer_combo.addItems(["Background", "Default", "Foreground", "UI"])
    sprite_form.addRow("Camada", window.sprite_layer_combo)
    window.sprite_order_field = QDoubleSpinBox()
    window.sprite_order_field.setDecimals(0)
    window.sprite_order_field.setRange(-10000, 10000)
    window.sprite_order_field.setKeyboardTracking(False)
    sprite_form.addRow("Ordem", window.sprite_order_field)
    main_layout.addWidget(window.sprite_renderer_body)


def _build_audio_component(window, main_layout):
    # ------------------ COMPONENTE: AUDIO SOURCE ------------------
    window.audio_source_header = QWidget()
    window.audio_source_header.setObjectName("InspectorComponentHeader")
    window.audio_source_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
    audio_header_layout = QHBoxLayout(window.audio_source_header)
    audio_header_layout.setContentsMargins(6, 4, 6, 4)
    window.show_audio_chk = QCheckBox(component_title("audio", "Audio Source"))
    window.show_audio_chk.setObjectName("InspectorCheckBox")
    window.show_audio_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
    audio_header_layout.addWidget(window.show_audio_chk)
    audio_header_layout.addStretch(1)
    window.btn_collapse_audio = QToolButton()
    window.btn_collapse_audio.setText("▼")
    window.btn_collapse_audio.setFixedSize(18, 18)
    window.btn_collapse_audio.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")
    window.btn_delete_audio = QToolButton()
    window.btn_delete_audio.setText("✕")
    window.btn_delete_audio.setFixedSize(18, 18)
    window.btn_delete_audio.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")
    audio_header_layout.addWidget(window.btn_collapse_audio)
    audio_header_layout.addWidget(window.btn_delete_audio)
    main_layout.addWidget(window.audio_source_header)

    window.audio_source_body = QWidget()
    audio_form = QFormLayout(window.audio_source_body)
    audio_form.setContentsMargins(8, 0, 8, 0)
    window.audio_path_combo = QComboBox()
    window.audio_path_combo.setStyleSheet("background-color: #242424; color: #e0e0e0; font-size: 11px;")
    window.audio_path_combo.setFixedHeight(22)
    audio_form.addRow("Áudio", window.audio_path_combo)
    window.audio_volume_field = QDoubleSpinBox()
    window.audio_volume_field.setRange(0.0, 1.0)
    window.audio_volume_field.setSingleStep(0.05)
    window.audio_volume_field.setDecimals(2)
    window.audio_volume_field.setKeyboardTracking(False)
    audio_form.addRow("Volume", window.audio_volume_field)
    window.audio_loop_field = QCheckBox()
    window.audio_autoplay_field = QCheckBox()
    audio_form.addRow("Repetir", window.audio_loop_field)
    audio_form.addRow("Ao iniciar", window.audio_autoplay_field)
    audio_actions = QWidget()
    audio_actions_layout = QHBoxLayout(audio_actions)
    audio_actions_layout.setContentsMargins(0, 0, 0, 0)
    window.audio_test_button = QPushButton("▶ Testar")
    window.audio_stop_button = QPushButton("■ Parar")
    audio_actions_layout.addWidget(window.audio_test_button)
    audio_actions_layout.addWidget(window.audio_stop_button)
    audio_form.addRow("Controles", audio_actions)
    main_layout.addWidget(window.audio_source_body)

def _build_rigidbody_component(window, main_layout):
    # ------------------ COMPONENTE: RIGIDBODY 2D ------------------
    window.rigidbody_header = QWidget()
    window.rigidbody_header.setObjectName("InspectorComponentHeader")
    window.rigidbody_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
    rb_h_layout = QHBoxLayout(window.rigidbody_header)
    rb_h_layout.setContentsMargins(6, 4, 6, 4)

    window.show_rigidbody_chk = QCheckBox(component_title("rigidbody", "RigidBody 2D"))
    window.show_rigidbody_chk.setObjectName("InspectorCheckBox")
    window.show_rigidbody_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
    rb_h_layout.addWidget(window.show_rigidbody_chk)
    rb_h_layout.addStretch()

    window.btn_collapse_rigidbody = QToolButton()
    window.btn_collapse_rigidbody.setText("▼")
    window.btn_collapse_rigidbody.setFixedSize(18, 18)
    window.btn_collapse_rigidbody.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

    window.btn_del_rb = QToolButton()
    window.btn_del_rb.setText("✕")
    window.btn_del_rb.setFixedSize(18, 18)
    window.btn_del_rb.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")

    rb_h_layout.addWidget(window.btn_collapse_rigidbody)
    rb_h_layout.addWidget(window.btn_del_rb)
    main_layout.addWidget(window.rigidbody_header)

    # Widget container para física
    window.rigidbody_body = QWidget()
    rb_body_layout = QVBoxLayout(window.rigidbody_body)
    rb_body_layout.setContentsMargins(0, 0, 0, 0)


    window.physics_fields = {
        "use_gravity": QCheckBox(),
        "is_kinematic": QCheckBox(),
    }
    window.physics_fields["use_gravity"].setObjectName("InspectorCheckBox")
    window.physics_fields["is_kinematic"].setObjectName("InspectorCheckBox")

    physics_widget = QWidget()
    physics_lay = QFormLayout(physics_widget)
    physics_lay.setContentsMargins(8, 0, 8, 0)
    physics_lay.addRow("Usar gravidade", window.physics_fields["use_gravity"])
    physics_lay.addRow("Cinemático", window.physics_fields["is_kinematic"])
    rb_body_layout.addWidget(physics_widget)
    main_layout.addWidget(window.rigidbody_body)


def _build_collider_component(window, main_layout):
    # ------------------ COMPONENTE: COLLIDER 2D ------------------
    window.collider_header = QWidget()
    window.collider_header.setObjectName("InspectorComponentHeader")
    window.collider_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
    col_h_layout = QHBoxLayout(window.collider_header)
    col_h_layout.setContentsMargins(6, 4, 6, 4)

    window.show_collider_chk = QCheckBox(component_title("collider", "Box/Circle Collider"))
    window.show_collider_chk.setObjectName("InspectorCheckBox")
    window.show_collider_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
    col_h_layout.addWidget(window.show_collider_chk)
    col_h_layout.addStretch()

    window.btn_collapse_collider = QToolButton()
    window.btn_collapse_collider.setText("▼")
    window.btn_collapse_collider.setFixedSize(18, 18)
    window.btn_collapse_collider.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")

    window.btn_del_col = QToolButton()
    window.btn_del_col.setText("✕")
    window.btn_del_col.setFixedSize(18, 18)
    window.btn_del_col.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")

    col_h_layout.addWidget(window.btn_collapse_collider)
    col_h_layout.addWidget(window.btn_del_col)
    main_layout.addWidget(window.collider_header)

    # Widget container para collider
    window.collider_body = QWidget()
    col_body_layout = QVBoxLayout(window.collider_body)
    col_body_layout.setContentsMargins(0, 0, 0, 0)


    collider_widget = QWidget()
    collider_lay = QFormLayout(collider_widget)
    collider_lay.setContentsMargins(8, 0, 8, 0)

    window.collider_fields: dict[str, QDoubleSpinBox] = {}
    for label, key in (("Collider Largura", "width"), ("Collider Altura", "height"), ("Collider Raio", "radius"), ("Collider Offset X", "offset_x"), ("Collider Offset Y", "offset_y")):
        editor = QDoubleSpinBox()
        editor.setObjectName("InspectorNumberField")
        editor.setDecimals(2)
        editor.setRange(0.01 if key in ("width", "height", "radius") else -100000.0, 100000.0)
        editor.setKeyboardTracking(False)
        window.collider_fields[key] = editor
        collider_lay.addRow(label, editor)
    window.collider_trigger_field = QCheckBox()
    window.collider_trigger_field.setObjectName("InspectorCheckBox")
    collider_lay.addRow("Collider Trigger", window.collider_trigger_field)
    col_body_layout.addWidget(collider_widget)
    main_layout.addWidget(window.collider_body)


def _build_camera_component(window, main_layout):
    # ------------------ COMPONENTE: CAMERA 2D ------------------
    window.camera_header = QWidget()
    window.camera_header.setObjectName("InspectorComponentHeader")
    window.camera_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
    camera_header_layout = QHBoxLayout(window.camera_header)
    camera_header_layout.setContentsMargins(6, 4, 6, 4)
    window.show_camera_chk = QCheckBox(component_title("camera", "Camera 2D"))
    window.show_camera_chk.setObjectName("InspectorCheckBox")
    window.show_camera_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
    camera_header_layout.addWidget(window.show_camera_chk)
    camera_header_layout.addStretch(1)
    window.btn_collapse_camera = QToolButton()
    window.btn_collapse_camera.setText("▼")
    window.btn_collapse_camera.setFixedSize(18, 18)
    window.btn_collapse_camera.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; font-size: 11px; padding: 0px;")
    window.btn_delete_camera = QToolButton()
    window.btn_delete_camera.setText("✕")
    window.btn_delete_camera.setFixedSize(18, 18)
    window.btn_delete_camera.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold !important; border: none !important; padding: 0px;")
    camera_header_layout.addWidget(window.btn_collapse_camera)
    camera_header_layout.addWidget(window.btn_delete_camera)
    main_layout.addWidget(window.camera_header)

    window.camera_body = QWidget()
    camera_form = QFormLayout(window.camera_body)
    camera_form.setContentsMargins(8, 0, 8, 0)
    window.camera_active_field = QCheckBox()
    camera_form.addRow("Ativa", window.camera_active_field)
    window.camera_width_field = QDoubleSpinBox()
    window.camera_width_field.setRange(1, 16384)
    window.camera_width_field.setDecimals(0)
    window.camera_width_field.setKeyboardTracking(False)
    camera_form.addRow("Largura", window.camera_width_field)
    window.camera_height_field = QDoubleSpinBox()
    window.camera_height_field.setRange(1, 16384)
    window.camera_height_field.setDecimals(0)
    window.camera_height_field.setKeyboardTracking(False)
    camera_form.addRow("Altura", window.camera_height_field)
    window.camera_zoom_field = QDoubleSpinBox()
    window.camera_zoom_field.setRange(0.1, 20.0)
    window.camera_zoom_field.setSingleStep(0.1)
    window.camera_zoom_field.setKeyboardTracking(False)
    camera_form.addRow("Zoom", window.camera_zoom_field)
    window.camera_follow_combo = QComboBox()
    camera_form.addRow("Seguir", window.camera_follow_combo)
    window.camera_color_button = QPushButton("Cor de fundo")
    camera_form.addRow("Fundo", window.camera_color_button)
    main_layout.addWidget(window.camera_body)


def _build_native_ui_component(window, main_layout):
    # ------------------ COMPONENTE: UI NATIVA ------------------
    window.ui_component_header = QWidget()
    window.ui_component_header.setObjectName("InspectorComponentHeader")
    window.ui_component_header.setStyleSheet("background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;")
    ui_header_layout = QHBoxLayout(window.ui_component_header)
    ui_header_layout.setContentsMargins(6, 4, 6, 4)
    window.show_ui_chk = QCheckBox(component_title("ui", "UI"))
    window.show_ui_chk.setObjectName("InspectorCheckBox")
    window.show_ui_chk.setStyleSheet("font-weight: bold; color: #ffffff;")
    ui_header_layout.addWidget(window.show_ui_chk)
    ui_header_layout.addStretch(1)
    window.btn_collapse_ui = QToolButton()
    window.btn_collapse_ui.setText("▼")
    window.btn_collapse_ui.setFixedSize(18, 18)
    window.btn_collapse_ui.setStyleSheet("background: transparent !important; color: #aaaaaa !important; border: none !important; padding: 0px;")
    window.btn_delete_ui = QToolButton()
    window.btn_delete_ui.setText("✕")
    window.btn_delete_ui.setFixedSize(18, 18)
    window.btn_delete_ui.setStyleSheet("background: transparent !important; color: #ff5555 !important; font-weight: bold; border: none !important; padding: 0px;")
    ui_header_layout.addWidget(window.btn_collapse_ui)
    ui_header_layout.addWidget(window.btn_delete_ui)
    main_layout.addWidget(window.ui_component_header)

    window.ui_component_body = QWidget()
    window.ui_component_form = QFormLayout(window.ui_component_body)
    window.ui_component_form.setContentsMargins(8, 0, 8, 0)
    window.ui_type_field = QLineEdit()
    window.ui_type_field.setReadOnly(True)
    window.ui_component_form.addRow("Tipo", window.ui_type_field)
    window.ui_text_field = QLineEdit()
    window.ui_component_form.addRow("Texto", window.ui_text_field)
    window.ui_position_fields = {}
    for label, key in (("Posição X", "x"), ("Posição Y", "y"), ("Largura", "width"), ("Altura", "height"), ("Ordem", "z_order"), ("Fonte", "font_size"), ("Opacidade", "alpha")):
        field = QDoubleSpinBox()
        field.setDecimals(0)
        field.setRange(-100000.0 if key in {"x", "y", "z_order"} else 0.0, 100000.0 if key != "alpha" else 255.0)
        field.setKeyboardTracking(False)
        window.ui_position_fields[key] = field
        window.ui_component_form.addRow(label, field)
    window.ui_color_button = QPushButton("Cor")
    window.ui_component_form.addRow("Cor", window.ui_color_button)
    ui_image_row = QWidget()
    ui_image_layout = QHBoxLayout(ui_image_row)
    ui_image_layout.setContentsMargins(0, 0, 0, 0)
    window.ui_image_path_field = QLineEdit()
    window.ui_image_path_field.setReadOnly(True)
    window.ui_image_button = QPushButton("...")
    window.ui_image_button.setFixedWidth(28)
    ui_image_layout.addWidget(window.ui_image_path_field)
    ui_image_layout.addWidget(window.ui_image_button)
    window.ui_component_form.addRow("Imagem", ui_image_row)
    window.ui_interactable_field = QCheckBox()
    window.ui_component_form.addRow("Interativo", window.ui_interactable_field)
    window.ui_event_field = QLineEdit()
    window.ui_component_form.addRow("Evento", window.ui_event_field)
    window.ui_target_combo = QComboBox()
    window.ui_component_form.addRow("Alvo", window.ui_target_combo)
    main_layout.addWidget(window.ui_component_body)


def _build_logic_component(window, main_layout):
    # ------------------ COMPONENTE: LÓGICA VISUAL ------------------
    window.logic_component_header = QWidget()
    window.logic_component_header.setObjectName("InspectorComponentHeader")
    logic_header_layout = QHBoxLayout(window.logic_component_header)
    logic_header_layout.setContentsMargins(6, 4, 6, 4)
    logic_title = QLabel(component_title("logic", "Lógica Visual"))
    logic_title.setObjectName("InspectorComponentTitle")
    logic_header_layout.addWidget(logic_title)
    logic_header_layout.addStretch(1)
    window.btn_collapse_logic = QToolButton()
    window.btn_collapse_logic.setText("▶")
    window.btn_collapse_logic.setFixedSize(18, 18)
    window.btn_collapse_logic.setObjectName("InspectorFoldoutButton")
    window.btn_delete_logic = QToolButton()
    window.btn_delete_logic.setText("✕")
    window.btn_delete_logic.setFixedSize(18, 18)
    window.btn_delete_logic.setObjectName("InspectorDangerButton")
    window.btn_delete_logic.setToolTip("Desvincular todos os Logic Graphs deste objeto")
    logic_header_layout.addWidget(window.btn_collapse_logic)
    logic_header_layout.addWidget(window.btn_delete_logic)
    main_layout.addWidget(window.logic_component_header)

    window.logic_component_body = QWidget()
    logic_body_layout = QVBoxLayout(window.logic_component_body)
    logic_body_layout.setContentsMargins(8, 6, 8, 8)
    logic_body_layout.setSpacing(6)
    window.logic_status_label = QLabel("Nenhum Logic Graph vinculado")
    window.logic_status_label.setObjectName("WorkspaceContext")
    logic_body_layout.addWidget(window.logic_status_label)
    window.logic_graph_combo = QComboBox()
    window.logic_graph_combo.setToolTip("Logic Graphs que controlam o objeto selecionado")
    logic_body_layout.addWidget(window.logic_graph_combo)
    window.logic_summary_label = QLabel("Selecione um grafo para ver seus eventos e blocos.")
    window.logic_summary_label.setWordWrap(True)
    window.logic_summary_label.setObjectName("PanelHint")
    logic_body_layout.addWidget(window.logic_summary_label)
    logic_primary_actions = QHBoxLayout()
    window.logic_open_button = QPushButton("Editar / Receitas")
    window.logic_open_button.setToolTip("Abra o grafo e use receitas pesquisáveis para aprender novas lógicas")
    window.logic_open_button.setProperty("uiRole", "primary")
    window.logic_link_button = QPushButton("Vincular outro")
    logic_primary_actions.addWidget(window.logic_open_button)
    logic_primary_actions.addWidget(window.logic_link_button)
    logic_body_layout.addLayout(logic_primary_actions)
    logic_secondary_actions = QHBoxLayout()
    window.logic_new_button = QPushButton("Criar novo")
    window.logic_unlink_button = QPushButton("Desvincular")
    window.logic_unlink_button.setProperty("uiRole", "danger")
    logic_secondary_actions.addWidget(window.logic_new_button)
    logic_secondary_actions.addWidget(window.logic_unlink_button)
    logic_body_layout.addLayout(logic_secondary_actions)
    main_layout.addWidget(window.logic_component_body)


def _build_runtime_debug_component(window, main_layout):
    # ------------------ PLAY MODE: ORIGEM E MOVIMENTOS ------------------
    window.runtime_debug_header = QWidget()
    window.runtime_debug_header.setObjectName("InspectorComponentHeader")
    runtime_header_layout = QHBoxLayout(window.runtime_debug_header)
    runtime_header_layout.setContentsMargins(6, 4, 6, 4)
    runtime_title = QLabel("▶  Runtime / Logic Debug")
    runtime_title.setObjectName("InspectorComponentTitle")
    runtime_header_layout.addWidget(runtime_title)
    runtime_header_layout.addStretch(1)
    window.btn_collapse_runtime = QToolButton()
    window.btn_collapse_runtime.setText("▼")
    window.btn_collapse_runtime.setFixedSize(18, 18)
    window.btn_collapse_runtime.setObjectName("InspectorFoldoutButton")
    runtime_header_layout.addWidget(window.btn_collapse_runtime)
    main_layout.addWidget(window.runtime_debug_header)

    window.runtime_debug_body = QWidget()
    runtime_body_layout = QVBoxLayout(window.runtime_debug_body)
    runtime_body_layout.setContentsMargins(8, 6, 8, 8)
    window.runtime_debug_label = QLabel("Sem dados de execução")
    window.runtime_debug_label.setObjectName("InspectorRuntimeDetails")
    window.runtime_debug_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
    window.runtime_debug_label.setWordWrap(True)
    runtime_body_layout.addWidget(window.runtime_debug_label)
    main_layout.addWidget(window.runtime_debug_body)

    for component_body in (
        window.transform_body, window.sprite_renderer_body, window.audio_source_body,
        window.rigidbody_body, window.collider_body, window.camera_body,
        window.ui_component_body, window.logic_component_body,
        window.runtime_debug_body,
    ):
        component_body.setObjectName("InspectorComponentBody")


def _finalize_inspector(window, scroll, inspector, main_layout):
    # O cabeçalho e corpo de scripts/custom agora são inseridos de forma modular dinâmica para cada script ativo
    window.script_containers = []

    window.add_component_button = QPushButton("＋ Adicionar Componente")
    window.add_component_button.setObjectName("InspectorAddComponentButton")
    window.add_component_button.setMinimumHeight(30)
    main_layout.addWidget(window.add_component_button)

    main_layout.addStretch(1)

    # Inspector respirável e redimensionável; não trava mais toda a interface em 290 px.
    inspector.setMinimumWidth(310)
    window.inspector_dock.setMinimumWidth(325)
    window.inspector_dock.resize(350, window.inspector_dock.height())
    scroll.setWidget(inspector)
    window.inspector_dock.setWidget(scroll)

def build_inspector_dock(window):
    scroll, inspector, main_layout = _build_inspector_shell(window)
    _build_transform_component(window, main_layout)
    _build_sprite_component(window, main_layout)
    _build_audio_component(window, main_layout)
    _build_rigidbody_component(window, main_layout)
    _build_collider_component(window, main_layout)
    _build_camera_component(window, main_layout)
    _build_native_ui_component(window, main_layout)
    _build_logic_component(window, main_layout)
    _build_runtime_debug_component(window, main_layout)
    _finalize_inspector(window, scroll, inspector, main_layout)
