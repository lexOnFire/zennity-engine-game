PREMIUM_QSS = """
QMainWindow { background-color: #151515; }
QWidget {
    color: #e2e2e2;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 11px;
}
QMenuBar {
    background-color: #151515;
    border-bottom: 1px solid #2d2d2d;
    padding: 2px 5px;
}
QMenuBar::item { padding: 4px 10px; border-radius: 3px; }
QMenuBar::item:selected { background-color: #2b2b2b; }
QMenu {
    background-color: #1c1c1c;
    border: 1px solid #2d2d2d;
    padding: 4px 0px;
}
QMenu::item { padding: 6px 20px 6px 25px; }
QMenu::item:selected { background-color: #2b2b2b; color: #ffffff; }
QToolBar#CommandBar {
    background-color: #1a1a1a;
    border-bottom: 1px solid #252525;
    spacing: 5px;
    padding: 3px 5px;
}
QToolButton, QPushButton {
    background-color: #252525;
    border: 1px solid #353535;
    border-radius: 3px;
    color: #e2e2e2;
    padding: 4px 10px;
}
QToolButton:hover, QPushButton:hover {
    background-color: #303030;
    border-color: #4caf50;
}
QToolButton:pressed, QPushButton:pressed {
    background-color: #2e3b2e;
    border-color: #4caf50;
}
QSplitter::handle {
    background-color: #151515;
}
QSplitter::handle:horizontal { width: 4px; }
QSplitter::handle:vertical { height: 4px; }
QFrame#PremiumPanel, QWidget#CreateDockRoot {
    background-color: #1c1c1c;
    border: 1px solid #252525;
}
QWidget#PanelHeader {
    background-color: #222222;
    border-bottom: 1px solid #2b2b2b;
}
QLabel#PanelHeaderTitle {
    color: #aaaaaa;
    font-weight: bold;
    font-size: 11px;
}
QLabel#SectionLabel {
    color: #4caf50;
    font-weight: bold;
    padding: 6px 2px 2px 2px;
}
QLineEdit#SearchBox, QLineEdit {
    background-color: #252525;
    border: 1px solid #353535;
    border-radius: 3px;
    padding: 5px;
    color: #e2e2e2;
}
QTreeWidget, QTextBrowser, QTextEdit {
    background-color: #121212;
    border: 1px solid #252525;
    color: #d8d8d8;
    selection-background-color: #2b4a63;
}
QTreeWidget::item {
    padding: 3px;
    height: 20px;
}
QTreeWidget::item:hover { background-color: #252525; }
QTreeWidget::item:selected { background-color: #007acc; color: #ffffff; }
QLabel#InspectorTitle {
    background-color: #252525;
    border-bottom: 1px solid #353535;
    color: #ffffff;
    font-weight: bold;
    padding: 8px;
}
QLabel#InspectorSection {
    background-color: #1a1a1a;
    border: 1px solid #2b2b2b;
    border-radius: 4px;
    margin: 6px;
    padding: 8px;
    color: #cfcfcf;
}
QPushButton#CreatePresetButton {
    text-align: left;
    min-height: 28px;
    margin: 1px 0px;
}
QWidget#ViewportCanvas {
    background-color: #1c1e20;
    border: 1px solid #252525;
}
QStatusBar {
    background-color: #151515;
    border-top: 1px solid #2d2d2d;
    color: #8c8c8c;
}
QComboBox {
    background-color: #252525;
    border: 1px solid #353535;
    padding: 3px 10px;
}
"""
