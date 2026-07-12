"""Teste isolado da interface do Zennity Editor, sem Pygame ou Viewport.

Execute a partir da raiz do projeto:
    python -m editor.interface_smoke_test
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QSplitter,
    QTabWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class InterfaceSmokeTest(QMainWindow):
    """Shell do editor para validar dock, splitter, menu e resize do Qt."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Zennity — Teste de Interface (sem Viewport)")
        self.resize(1440, 900)
        self.setMinimumSize(1000, 650)
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        self._build_menu()
        self._build_toolbar()
        self._build_center()
        self._build_docks()
        self.statusBar().showMessage("Teste isolado: não há Pygame nem renderização de cena.")

    def _build_menu(self) -> None:
        self.editor_menus = {}
        for name in ("Arquivo", "Editar", "Janela", "Criar", "Ferramentas", "Build", "Executar", "Ajuda"):
            menu = self.menuBar().addMenu(name)
            self.editor_menus[name] = menu

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Ferramentas")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.toolbar_actions = {}
        for label in ("Novo", "Abrir", "Salvar", "Select", "Move", "Rotate", "Scale", "Play", "Pause", "Stop"):
            action = QAction(label, self)
            self.toolbar_actions[label] = action
            toolbar.addAction(action)
        toolbar.addSeparator()
        mode = QComboBox()
        mode.addItems(["2D", "3D (experimental)"])
        toolbar.addWidget(mode)

    def _build_center(self) -> None:
        tabs = QTabWidget()
        self.viewport_host = QFrame()
        self.viewport_host.setObjectName("IsolatedViewportHost")
        self.viewport_host.setFrameShape(QFrame.StyledPanel)
        self.viewport_host.setAttribute(Qt.WA_NativeWindow, True)
        self.viewport_host.setStyleSheet("#IsolatedViewportHost { background: #16181f; }")
        tabs.addTab(self.viewport_host, "Scene")
        tabs.addTab(self._placeholder("Game View desativada para este teste."), "Game")
        self.setCentralWidget(tabs)

    def _build_docks(self) -> None:
        hierarchy = QTreeWidget()
        self.hierarchy_tree = hierarchy
        hierarchy.setHeaderHidden(True)
        root = QTreeWidgetItem(["MainScene"])
        environment = QTreeWidgetItem(["Environment"])
        environment.addChildren([QTreeWidgetItem(["DirectionalLight"]), QTreeWidgetItem(["Terrain"])])
        root.addChildren([environment, QTreeWidgetItem(["Chao"]), QTreeWidgetItem(["Player"]), QTreeWidgetItem(["Enemies"])])
        hierarchy.addTopLevelItem(root)
        hierarchy.expandAll()

        assets = QTreeWidget()
        self.assets_tree = assets
        assets.setHeaderHidden(True)
        asset_root = QTreeWidgetItem(["Assets"])
        asset_root.addChildren([QTreeWidgetItem(["Scenes"]), QTreeWidgetItem(["Scripts"]), QTreeWidgetItem(["Textures"])])
        assets.addTopLevelItem(asset_root)
        assets.expandAll()

        left = QSplitter(Qt.Vertical)
        left.addWidget(hierarchy)
        left.addWidget(assets)
        left.setSizes([330, 300])
        self._dock("Hierarchy / Assets", left, Qt.LeftDockWidgetArea, 260)

        inspector = QWidget()
        form = QFormLayout(inspector)
        self.inspector_name_label = QLabel("Player")
        self.inspector_fields: dict[str, QDoubleSpinBox] = {}
        form.addRow("Objeto", self.inspector_name_label)
        for field, value in (("Posição X", "400.00"), ("Posição Y", "200.00"), ("Escala X", "36.00"), ("Escala Y", "48.00")):
            key = {
                "Posição X": "x",
                "Posição Y": "y",
                "Escala X": "w",
                "Escala Y": "h",
            }[field]
            editor = QDoubleSpinBox()
            editor.setDecimals(2)
            editor.setRange(1.0 if key in ("w", "h") else -100000.0, 100000.0)
            editor.setValue(float(value))
            editor.setKeyboardTracking(False)
            self.inspector_fields[key] = editor
            form.addRow(field, editor)
        self.physics_fields = {
            "use_gravity": QCheckBox(),
            "is_kinematic": QCheckBox(),
        }
        form.addRow("Usar gravidade", self.physics_fields["use_gravity"])
        form.addRow("Cinemático", self.physics_fields["is_kinematic"])
        self.component_summary_label = QLabel("Transform")
        self.component_summary_label.setWordWrap(True)
        form.addRow("Componentes", self.component_summary_label)
        self._dock("Inspector", inspector, Qt.RightDockWidgetArea, 300)

        console = QPlainTextEdit()
        self.console_output = console
        console.setReadOnly(True)
        console.setPlainText("[INFO] Interface isolada iniciada.\n[INFO] Nenhuma cena foi carregada.\n[INFO] Nenhum frame Pygame será renderizado.")
        self._dock("Console", console, Qt.BottomDockWidgetArea, 600)

    def _dock(self, title: str, widget: QWidget, area: Qt.DockWidgetArea, width: int) -> None:
        dock = QDockWidget(title, self)
        dock.setObjectName(f"SmokeTest_{title}")
        dock.setWidget(widget)
        dock.setMinimumWidth(width if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea) else 200)
        self.addDockWidget(area, dock)

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16px; color: #aeb6c2;")
        layout.addWidget(label)
        return frame


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = InterfaceSmokeTest()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
