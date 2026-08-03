"""Modern visual-scripting workspace theme."""
from __future__ import annotations


VISUAL_SCRIPTING_QSS = """
            QMainWindow#VisualScriptingEditorDock,
            QWidget#VisualScriptingSurface {
                background: #0b0d14;
                color: #f1f5f9;
                font-family: "Segoe UI", sans-serif;
                font-size: 12px;
            }
            QWidget#VisualCommandBar {
                background: #0d0f17;
                border-bottom: 1px solid #1c2230;
            }
            QLabel#VisualBrandTitle {
                color: #38bdf8;
                font-size: 13px;
                font-weight: bold;
            }
            QLabel#VisualDocumentLabel {
                color: #f8fafc;
                font-size: 12px;
                font-weight: bold;
            }
            QLabel#VisualObjectContext {
                color: #94a3b8;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton {
                min-height: 28px;
                padding: 0 14px;
                color: #cbd5e1;
                background: #1a202c;
                border: 1px solid #2d3748;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                color: #f8fafc;
                background: #2d3748;
            }
            QPushButton:pressed { background: #0f1520; }
            QPushButton:disabled {
                color: #475569;
                background: #121722;
                border-color: #1e293b;
            }
            QPushButton#VisualPlayButton {
                color: #0f172a;
                background: #06b6d4;
                border: none;
                font-weight: bold;
            }
            QPushButton#VisualPlayButton:hover { background: #22d3ee; }
            QPushButton#VisualStopButton {
                color: #f8fafc;
                background: #1a202c;
                border: 1px solid #2d3748;
            }
            QLineEdit {
                min-height: 28px;
                padding: 0 10px;
                color: #f1f5f9;
                selection-background-color: #38bdf8;
                background: #181b24;
                border: 1px solid #282e3e;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
            QSplitter::handle {
                background: #1e2430;
            }
            QSplitter::handle:vertical { height: 2px; }
            QSplitter::handle:horizontal { width: 2px; }
            QTabWidget::pane {
                background: #0b0d14;
                border: none;
            }
            QTabBar::tab {
                min-height: 26px;
                padding: 0 14px;
                color: #94a3b8;
                background: #141824;
                border: 1px solid transparent;
                border-bottom: 2px solid transparent;
                font-size: 11px;
                font-weight: bold;
            }
            QTabBar::tab:hover { color: #f8fafc; background: #1a202c; }
            QTabBar::tab:selected {
                color: #f8fafc;
                background: #1e2536;
                border-bottom: 2px solid #38bdf8;
            }
            QListWidget, QTreeWidget, QTextEdit {
                color: #cbd5e1;
                background: #141720;
                border: 1px solid #1e2430;
                border-radius: 6px;
                outline: none;
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
