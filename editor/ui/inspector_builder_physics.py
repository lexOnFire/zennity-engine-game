"""Módulos de Física e Câmera para o construtor do Inspector."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QPushButton,
    QToolButton,
    QWidget,
)

from editor.ui.icons import component_title


def build_rigidbody_component(window, main_layout) -> None:
    window.rigidbody_header = QWidget()
    window.rigidbody_header.setObjectName("InspectorComponentHeader")
    rb_header_layout = QHBoxLayout(window.rigidbody_header)
    rb_header_layout.setContentsMargins(6, 4, 6, 4)
    window.show_rigidbody_chk = QCheckBox(component_title("rigidbody", "RigidBody"))
    window.show_rigidbody_chk.setObjectName("InspectorCheckBox")
    rb_header_layout.addWidget(window.show_rigidbody_chk)
    rb_header_layout.addStretch(1)
    window.btn_collapse_rigidbody = QToolButton()
    window.btn_collapse_rigidbody.setText("▼")
    window.btn_collapse_rigidbody.setFixedSize(18, 18)
    window.btn_collapse_rigidbody.setObjectName("InspectorFoldoutButton")
    window.btn_del_rb = QToolButton()
    window.btn_del_rb.setText("✕")
    window.btn_del_rb.setFixedSize(18, 18)
    window.btn_del_rb.setObjectName("InspectorDangerButton")
    rb_header_layout.addWidget(window.btn_collapse_rigidbody)
    rb_header_layout.addWidget(window.btn_del_rb)
    main_layout.addWidget(window.rigidbody_header)

    window.rigidbody_body = QWidget()
    rb_form = QFormLayout(window.rigidbody_body)
    rb_form.setContentsMargins(8, 0, 8, 0)
    window.physics_fields = {}
    for label, key in (
        ("Gravidade", "use_gravity"),
        ("Cinemático", "is_kinematic"),
        ("Travar Rotação Z", "freeze_rotation_z"),
    ):
        chk = QCheckBox()
        chk.setObjectName("InspectorCheckBox")
        window.physics_fields[key] = chk
        rb_form.addRow(label, chk)
    main_layout.addWidget(window.rigidbody_body)


def build_collider_component(window, main_layout) -> None:
    window.collider_header = QWidget()
    window.collider_header.setObjectName("InspectorComponentHeader")
    col_header_layout = QHBoxLayout(window.collider_header)
    col_header_layout.setContentsMargins(6, 4, 6, 4)
    window.show_collider_chk = QCheckBox(component_title("collider", "Box Collider"))
    window.show_collider_chk.setObjectName("InspectorCheckBox")
    col_header_layout.addWidget(window.show_collider_chk)
    col_header_layout.addStretch(1)
    window.btn_collapse_collider = QToolButton()
    window.btn_collapse_collider.setText("▼")
    window.btn_collapse_collider.setFixedSize(18, 18)
    window.btn_collapse_collider.setObjectName("InspectorFoldoutButton")
    window.btn_del_col = QToolButton()
    window.btn_del_col.setText("✕")
    window.btn_del_col.setFixedSize(18, 18)
    window.btn_del_col.setObjectName("InspectorDangerButton")
    col_header_layout.addWidget(window.btn_collapse_collider)
    col_header_layout.addWidget(window.btn_del_col)
    main_layout.addWidget(window.collider_header)

    window.collider_body = QWidget()
    col_form = QFormLayout(window.collider_body)
    col_form.setContentsMargins(8, 0, 8, 0)
    window.collider_fields = {}
    for label, key in (
        ("Largura", "width"),
        ("Altura", "height"),
        ("Offset X", "offset_x"),
        ("Offset Y", "offset_y"),
    ):
        spn = QDoubleSpinBox()
        spn.setDecimals(1)
        spn.setRange(-10000.0, 10000.0)
        spn.setSingleStep(1.0)
        spn.setKeyboardTracking(False)
        window.collider_fields[key] = spn
        col_form.addRow(label, spn)

    window.collider_trigger_field = QCheckBox()
    window.collider_trigger_field.setObjectName("InspectorCheckBox")
    col_form.addRow("Trigger", window.collider_trigger_field)
    main_layout.addWidget(window.collider_body)


def build_camera_component(window, main_layout) -> None:
    window.camera_header = QWidget()
    window.camera_header.setObjectName("InspectorComponentHeader")
    cam_header_layout = QHBoxLayout(window.camera_header)
    cam_header_layout.setContentsMargins(6, 4, 6, 4)
    window.show_camera_chk = QCheckBox(component_title("camera", "Camera 2D"))
    window.show_camera_chk.setObjectName("InspectorCheckBox")
    cam_header_layout.addWidget(window.show_camera_chk)
    cam_header_layout.addStretch(1)
    window.btn_collapse_camera = QToolButton()
    window.btn_collapse_camera.setText("▼")
    window.btn_collapse_camera.setFixedSize(18, 18)
    window.btn_collapse_camera.setObjectName("InspectorFoldoutButton")
    window.btn_delete_camera = QToolButton()
    window.btn_delete_camera.setText("✕")
    window.btn_delete_camera.setFixedSize(18, 18)
    window.btn_delete_camera.setObjectName("InspectorDangerButton")
    cam_header_layout.addWidget(window.btn_collapse_camera)
    cam_header_layout.addWidget(window.btn_delete_camera)
    main_layout.addWidget(window.camera_header)

    window.camera_body = QWidget()
    cam_form = QFormLayout(window.camera_body)
    cam_form.setContentsMargins(8, 0, 8, 0)
    window.camera_active_field = QCheckBox()
    window.camera_active_field.setObjectName("InspectorCheckBox")
    cam_form.addRow("Ativa", window.camera_active_field)
    window.camera_zoom_field = QDoubleSpinBox()
    window.camera_zoom_field.setDecimals(2)
    window.camera_zoom_field.setRange(0.05, 100.0)
    window.camera_zoom_field.setSingleStep(0.1)
    window.camera_zoom_field.setKeyboardTracking(False)
    cam_form.addRow("Zoom", window.camera_zoom_field)
    window.camera_viewport_w = QDoubleSpinBox()
    window.camera_viewport_w.setDecimals(0)
    window.camera_viewport_w.setRange(1.0, 10000.0)
    window.camera_viewport_w.setKeyboardTracking(False)
    cam_form.addRow("Largura Viewport", window.camera_viewport_w)
    window.camera_viewport_h = QDoubleSpinBox()
    window.camera_viewport_h.setDecimals(0)
    window.camera_viewport_h.setRange(1.0, 10000.0)
    window.camera_viewport_h.setKeyboardTracking(False)
    cam_form.addRow("Altura Viewport", window.camera_viewport_h)
    window.camera_follow_combo = QComboBox()
    cam_form.addRow("Seguir Alvo", window.camera_follow_combo)
    window.camera_color_button = QPushButton("Cor do Fundo")
    cam_form.addRow("Fundo", window.camera_color_button)
    main_layout.addWidget(window.camera_body)
