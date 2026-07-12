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
QToolButton {
    background-color: #252525;
    border: 1px solid #353535;
    border-radius: 3px;
    color: #e2e2e2;
    padding: 6px 12px;
    font-size: 15px;
}
QPushButton {
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
QToolButton:checked {
    background-color: #1f5f38;
    border-color: #47d16c;
    color: #ffffff;
    font-weight: 600;
}
QToolButton:checked:hover {
    background-color: #267545;
    border-color: #65e582;
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
    background-color: #1d1d1d;
    border-bottom: 1px solid #262626;
    color: #ffffff;
    font-weight: bold;
    padding: 5px 7px;
}
QLabel#InspectorSection {
    background-color: #1a1a1a;
    border: 1px solid #2b2b2b;
    border-radius: 4px;
    margin: 6px;
    padding: 8px;
    color: #cfcfcf;
}
QWidget#InspectorObjectHeader {
    background-color: #202020;
    border-bottom: 1px solid #2c2c2c;
}
QWidget#InspectorComponentList {
    background-color: #171717;
}
QWidget#InspectorComponentCard {
    background-color: #1f1f1f;
    border: 1px solid #2b2b2b;
    border-radius: 2px;
}
QWidget#InspectorComponentHeader {
    background-color: #242424;
    border-bottom: 1px solid #303030;
}
QWidget#InspectorComponentBody {
    background-color: #1b1b1b;
}
QLabel#InspectorComponentTitle {
    color: #e3e3e3;
    font-weight: 600;
}
QLabel#InspectorFoldout {
    color: #a6a6a6;
    font-size: 10px;
}
QLabel#InspectorComponentIcon {
    color: #74c365;
    font-size: 10px;
}
QWidget#InspectorPropertyRow {
    min-height: 24px;
}
QLabel#InspectorPropertyLabel {
    color: #b9b9b9;
    min-width: 58px;
}
QLabel#InspectorAxisLabel {
    color: #9a9a9a;
    min-width: 10px;
}
QLineEdit#InspectorObjectName,
QLineEdit#InspectorTextField,
QDoubleSpinBox#InspectorNumberField,
QComboBox#InspectorCombo {
    background-color: #151515;
    border: 1px solid #282828;
    border-radius: 2px;
    color: #dcdcdc;
    padding: 3px 5px;
    min-height: 18px;
}
QDoubleSpinBox#InspectorNumberField {
    min-width: 54px;
}
QCheckBox#InspectorCheckBox {
    color: #cfcfcf;
    spacing: 5px;
}
QPushButton#InspectorAddComponentButton {
    background-color: #303030;
    border: 1px solid #3a3a3a;
    border-radius: 2px;
    margin: 6px 54px 8px 54px;
    padding: 5px 10px;
    color: #d6d6d6;
}
QPushButton#InspectorRemoveComponentButton {
    background-color: #242424;
    border: 1px solid #333333;
    border-radius: 2px;
    padding: 2px 6px;
    max-width: 24px;
}
QLabel#InspectorStatus {
    color: #c8a95a;
    padding: 2px 8px;
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
