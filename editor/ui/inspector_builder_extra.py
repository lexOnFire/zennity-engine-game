"""Módulos de UI, Lógica e Runtime Debug para o construtor do Inspector."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from editor.ui.icons import component_title


def build_native_ui_component(window, main_layout) -> None:
    window.ui_component_header = QWidget()
    window.ui_component_header.setObjectName("InspectorComponentHeader")
    window.ui_component_header.setStyleSheet(
        "background-color: #24272d; border-radius: 4px; border: 1px solid #30343c;"
    )
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
    window.btn_collapse_ui.setStyleSheet(
        "background: transparent !important; color: #aaaaaa !important; border: none !important; padding: 0px;"
    )
    window.btn_delete_ui = QToolButton()
    window.btn_delete_ui.setText("✕")
    window.btn_delete_ui.setFixedSize(18, 18)
    window.btn_delete_ui.setStyleSheet(
        "background: transparent !important; color: #ff5555 !important; font-weight: bold; border: none !important; padding: 0px;"
    )
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
    for label, key in (
        ("Posição X", "x"),
        ("Posição Y", "y"),
        ("Largura", "width"),
        ("Altura", "height"),
        ("Ordem", "z_order"),
        ("Fonte", "font_size"),
        ("Opacidade", "alpha"),
    ):
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


def build_logic_component(window, main_layout) -> None:
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


def build_runtime_debug_component(window, main_layout) -> None:
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
        window.transform_body,
        window.sprite_renderer_body,
        window.audio_source_body,
        window.rigidbody_body,
        window.collider_body,
        window.camera_body,
        window.ui_component_body,
        window.logic_component_body,
        window.runtime_debug_body,
    ):
        component_body.setObjectName("InspectorComponentBody")
