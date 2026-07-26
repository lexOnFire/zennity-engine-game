"""Modern visual theme for the detached 2D Animation Studio."""

from __future__ import annotations

from typing import Any


def apply_animation_workspace_theme(workspace: Any) -> None:
    workspace.setStyleSheet("""
        QWidget#AnimationWorkspace {
            background:#080b11; color:#d8e0ef;
            font-family:"Segoe UI"; font-size:12px;
        }
        QWidget#AnimationHeader {
            background:#101622; border:1px solid #253044; border-radius:10px;
        }
        QLabel#WorkspaceTitle {
            color:#f5f8ff; font-size:14px; font-weight:700; letter-spacing:1px;
        }
        QLabel#WorkspaceStatus { color:#66e0ff; font-size:10px; font-weight:600; }
        QLabel#WorkspaceContext {
            color:#c7b9ff; background:#211a3b; border:1px solid #554487;
            border-radius:11px; padding:4px 10px; font-weight:600;
        }
        QWidget#AnimationToolbar {
            background:#0f1520; border:1px solid #222d3d; border-radius:9px;
        }
        QPushButton, QToolButton {
            min-height:30px; padding:0 11px; color:#bcc7d9;
            background:#171f2d; border:1px solid #2b374a;
            border-radius:7px; font-weight:600;
        }
        QToolButton { min-width:32px; max-width:32px; padding:0; }
        QPushButton:hover, QToolButton:hover {
            color:#fff; background:#222d3e; border-color:#52647f;
        }
        QPushButton:pressed, QToolButton:pressed { background:#0d131d; }
        QPushButton#AnimationApplyButton {
            color:#061711; background:#4ee5a0; border-color:#7af0bb;
        }
        QPushButton#AnimationDemoButton {
            color:#fff; background:#6b4bda; border-color:#9075f1;
        }
        QPushButton#AnimationDangerButton {
            color:#ffe8ec; background:#8e3043; border-color:#bd4259;
        }
        QFrame#AnimationLibraryPanel, QWidget#AnimationPreviewPanel,
        QWidget#AnimationPropertiesPanel, QFrame#AnimationTimelinePanel {
            background:#0d121b; border:1px solid #222d3d; border-radius:9px;
        }
        QLabel#AnimationPreview {
            color:#74839b; background:#070a0f;
            border:1px solid #273246; border-radius:9px;
        }
        QLabel#AnimationPreview[uiState="content"] {
            color:#fff; border:1px solid #7159dc;
        }
        QLabel#PanelSectionTitle {
            color:#95a6c1; font-size:10px; font-weight:700; letter-spacing:1px;
        }
        QLabel#PanelHint { color:#687891; font-size:10px; }
        QLabel#AnimationFrameCounter {
            color:#62ddff; background:#10212a; border:1px solid #25566a;
            border-radius:10px; padding:3px 9px;
            font-family:"Consolas"; font-weight:700;
        }
        QTreeWidget {
            color:#cbd5e6; background:#090e16;
            border:1px solid #222d3d; border-radius:6px; outline:none;
        }
        QTreeWidget::item { min-height:26px; padding:3px 5px; border-radius:4px; }
        QTreeWidget::item:hover { background:#1c2737; color:#fff; }
        QTreeWidget::item:selected { background:#503ca8; color:#fff; }
        QHeaderView::section {
            color:#8291aa; background:#151d29; border:none;
            border-bottom:1px solid #2b3749; padding:6px; font-weight:600;
        }
        QLineEdit, QComboBox, QDoubleSpinBox {
            min-height:30px; padding:0 9px; color:#e1e7f2;
            background:#0a0f17; border:1px solid #2a3649; border-radius:6px;
            selection-background-color:#6f53dd;
        }
        QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
            border-color:#8268ef; background:#101722;
        }
        QComboBox QAbstractItemView {
            color:#dce4f1; background:#111824; selection-background-color:#503ca8;
        }
        QCheckBox { color:#c7d0df; spacing:7px; }
        QCheckBox::indicator {
            width:15px; height:15px; background:#0a0f17;
            border:1px solid #35435a; border-radius:4px;
        }
        QCheckBox::indicator:checked { background:#7458e8; border-color:#9a83f5; }
        QSlider::groove:horizontal {
            height:5px; background:#1b2533; border-radius:2px;
        }
        QSlider::sub-page:horizontal { background:#7159e6; border-radius:2px; }
        QSlider::handle:horizontal {
            width:14px; height:14px; margin:-5px 0;
            background:#70e1ff; border:2px solid #d9f8ff; border-radius:7px;
        }
        QScrollArea { background:transparent; border:none; }
        QScrollBar:vertical { width:9px; background:#090e15; margin:2px; }
        QScrollBar::handle:vertical {
            min-height:28px; background:#334157; border-radius:4px;
        }
        QSplitter::handle { background:#171f2b; }
        QSplitter::handle:horizontal { width:6px; }
        QScrollBar::add-line, QScrollBar::sub-line { width:0; height:0; }
    """)
