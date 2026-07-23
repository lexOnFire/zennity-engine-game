"""Composition root for Inspector cards.

The extracted builders populate the public card attributes expected by the
presenter: ``window.transform_header``, ``window.sprite_renderer_header``,
``window.audio_source_header``, ``window.rigidbody_header``,
``window.collider_header``, ``window.camera_header`` and
``window.ui_component_header``.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDockWidget, QDoubleSpinBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget
)
from editor.ui.icons import component_title

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
    trans_body_layout.addWidget(_build_position_fields(window))

    trans_body_layout.addWidget(_build_rotation_fields(window))

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


def _build_position_fields(window) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(4, 0, 4, 0)
    label = QLabel("Posição")
    label.setMinimumWidth(50)
    layout.addWidget(label)
    for axis in ("x", "y"):
        field = QDoubleSpinBox()
        field.setObjectName("InspectorNumberField")
        field.setButtonSymbols(QDoubleSpinBox.NoButtons)
        field.setDecimals(2)
        field.setRange(-100000.0, 100000.0)
        field.setKeyboardTracking(False)
        window.inspector_fields[axis] = field
        layout.addWidget(QLabel(axis.upper()))
        layout.addWidget(field)
    position_z = QDoubleSpinBox()
    position_z.setObjectName("InspectorNumberField")
    position_z.setButtonSymbols(QDoubleSpinBox.NoButtons)
    position_z.setDecimals(2)
    position_z.setValue(0.0)
    position_z.setEnabled(False)
    layout.addWidget(QLabel("Z"))
    layout.addWidget(position_z)
    return widget


def _build_rotation_fields(window) -> QWidget:
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(4, 0, 4, 0)
    label = QLabel("Rotação")
    label.setMinimumWidth(50)
    layout.addWidget(label)
    for axis in ("X", "Y"):
        field = QDoubleSpinBox()
        field.setObjectName("InspectorNumberField")
        field.setButtonSymbols(QDoubleSpinBox.NoButtons)
        field.setDecimals(2)
        field.setValue(0.0)
        field.setEnabled(False)
        layout.addWidget(QLabel(axis))
        layout.addWidget(field)
    rotation = QDoubleSpinBox()
    rotation.setObjectName("InspectorNumberField")
    rotation.setButtonSymbols(QDoubleSpinBox.NoButtons)
    rotation.setDecimals(2)
    rotation.setRange(-100000.0, 100000.0)
    rotation.setKeyboardTracking(False)
    window.inspector_fields["rotation"] = rotation
    layout.addWidget(QLabel("Z"))
    layout.addWidget(rotation)
    return widget


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
