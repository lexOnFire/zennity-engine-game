"""Modern visual-scripting workspace theme."""
from __future__ import annotations


VISUAL_SCRIPTING_QSS = """
            QMainWindow#VisualScriptingEditorDock,
            QWidget#VisualScriptingSurface {
                background: #080b11;
                color: #d9e0ee;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QWidget#VisualCommandBar {
                background: #101622;
                border: 1px solid #232d3d;
                border-radius: 10px;
            }
            QLabel#VisualBrandTitle {
                color: #f4f7ff;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#VisualDocumentLabel {
                color: #7c8ba5;
                font-size: 9px;
                font-weight: 600;
            }
            QLabel#VisualObjectContext {
                color: #69f0ae;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.6px;
            }
            QPushButton {
                min-height: 30px;
                padding: 0 11px;
                color: #b9c4d6;
                background: #171e2b;
                border: 1px solid #2a3547;
                border-radius: 7px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #ffffff;
                background: #222c3d;
                border-color: #4a5a75;
            }
            QPushButton:pressed { background: #0f1520; }
            QPushButton:disabled {
                color: #596579;
                background: #101621;
                border-color: #202938;
            }
            QPushButton#VisualPlayButton {
                color: #07140d;
                background: #4ee59a;
                border-color: #79f2b5;
            }
            QPushButton#VisualPlayButton:hover { background: #69f0ac; }
            QPushButton#VisualStopButton {
                color: #ffecef;
                background: #a9364b;
                border-color: #d34b64;
            }
            QPushButton#VisualExplainButton {
                color: #ffffff;
                background: #6847d9;
                border-color: #8f73f2;
            }
            QLineEdit {
                min-height: 32px;
                padding: 0 12px;
                color: #e8edfa;
                selection-background-color: #7658e8;
                background: #0b1019;
                border: 1px solid #2a3547;
                border-radius: 16px;
            }
            QLineEdit:focus {
                border: 1px solid #8a6cff;
                background: #101622;
            }
            QSplitter::handle {
                background: #171e2a;
                border-radius: 2px;
            }
            QSplitter::handle:vertical { height: 5px; }
            QSplitter::handle:horizontal { width: 5px; }
            QTabWidget::pane {
                background: #0d121b;
                border: 1px solid #232c3b;
                border-radius: 7px;
                top: -1px;
            }
            QTabBar::tab {
                min-height: 28px;
                padding: 0 13px;
                color: #78869e;
                background: #101620;
                border: 1px solid transparent;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:hover { color: #dce4f2; background: #171f2d; }
            QTabBar::tab:selected {
                color: #ffffff;
                background: #171f2d;
                border-bottom: 2px solid #8a6cff;
            }
            QListWidget, QTreeWidget, QTextEdit {
                color: #c9d2e3;
                background: #0b1018;
                border: 1px solid #222c3b;
                border-radius: 6px;
                outline: none;
                alternate-background-color: #101722;
            }
            QListWidget::item, QTreeWidget::item {
                min-height: 25px;
                padding: 2px 5px;
                border-radius: 4px;
            }
            QListWidget::item:hover, QTreeWidget::item:hover {
                color: #ffffff;
                background: #202a3a;
            }
            QListWidget::item:selected, QTreeWidget::item:selected {
                color: #ffffff;
                background: #4e3aa3;
            }
            QHeaderView::section {
                color: #8390a7;
                background: #151c28;
                border: none;
                border-bottom: 1px solid #293447;
                padding: 6px;
                font-weight: 600;
            }
            QComboBox {
                min-height: 28px;
                padding: 0 9px;
                color: #d8dfec;
                background: #151c28;
                border: 1px solid #2b3648;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView {
                color: #d8dfec;
                background: #111722;
                selection-background-color: #4e3aa3;
            }
            QFrame#LogicPalettePanel, QFrame#LogicPropertiesPanel {
                background: #0d121b;
                border: 1px solid #222c3b;
                border-radius: 8px;
            }
            QLabel#PanelSectionTitle {
                color: #91a0ba;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
            }
            QLabel#PanelHint { color: #69778f; font-size: 10px; }
            QLabel#WorkspaceContext { color: #8a6cff; font-weight: 600; }
            QScrollBar:vertical {
                width: 9px;
                background: #0b1018;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                min-height: 28px;
                background: #334056;
                border-radius: 4px;
            }
            QScrollBar:horizontal {
                height: 9px;
                background: #0b1018;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                min-width: 28px;
                background: #334056;
                border-radius: 4px;
            }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
        """


def apply_visual_scripting_theme(widget) -> None:
    widget.setStyleSheet(VISUAL_SCRIPTING_QSS)
