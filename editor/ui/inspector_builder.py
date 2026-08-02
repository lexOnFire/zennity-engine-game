"""Composition root for Inspector cards.

The extracted builders populate the public card attributes expected by the
presenter: ``window.transform_header``, ``window.sprite_renderer_header``,
``window.audio_source_header``, ``window.rigidbody_header``,
``window.collider_header``, ``window.camera_header`` and
``window.ui_component_header``.
"""

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
from editor.ui.detached_workspace import DetachedWorkspaceWindow

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

    # Cabeçalho do Objeto (Player, Estático, etc.)
    obj_header = QWidget()
    obj_header.setObjectName("InspectorToolbar")
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
    window.tag_combo.setEditable(True)
    window.tag_combo.setInsertPolicy(QComboBox.InsertAtBottom)
    window.tag_combo.addItems(["Untagged", "Player", "Enemy", "Food", "Item", "Collectible", "MainCamera"])
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
    window.audio_output_combo = QComboBox()
    window.audio_output_combo.setStyleSheet("background-color: #242424; color: #e0e0e0; font-size: 11px;")
    window.audio_output_combo.setFixedHeight(22)
    audio_form.addRow("Saída", window.audio_output_combo)
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

def _build_rigidbody_component(window, main_layout):
    from editor.ui.inspector_builder_physics import build_rigidbody_component
    build_rigidbody_component(window, main_layout)


def _build_collider_component(window, main_layout):
    from editor.ui.inspector_builder_physics import build_collider_component
    build_collider_component(window, main_layout)


def _build_camera_component(window, main_layout):
    from editor.ui.inspector_builder_physics import build_camera_component
    build_camera_component(window, main_layout)


def _build_native_ui_component(window, main_layout):
    from editor.ui.inspector_builder_extra import build_native_ui_component
    build_native_ui_component(window, main_layout)


def _build_logic_component(window, main_layout):
    from editor.ui.inspector_builder_extra import build_logic_component
    build_logic_component(window, main_layout)


def _build_runtime_debug_component(window, main_layout):
    from editor.ui.inspector_builder_extra import build_runtime_debug_component
    build_runtime_debug_component(window, main_layout)


def _finalize_inspector(window, scroll, inspector, main_layout):

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
