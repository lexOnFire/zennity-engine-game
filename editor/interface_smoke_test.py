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
    QPushButton,
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
        self.viewport_tabs = QTabWidget()
        self.viewport_tabs.setObjectName("SceneGameTabs")
        self.viewport_host = QFrame()
        self.viewport_host.setObjectName("IsolatedViewportHost")
        self.viewport_host.setFrameShape(QFrame.StyledPanel)
        self.viewport_host.setAttribute(Qt.WA_NativeWindow, True)
        self.viewport_host.setStyleSheet("#IsolatedViewportHost { background: #16181f; }")
        self.viewport_tabs.addTab(self.viewport_host, "Scene")
        self.viewport_tabs.addTab(self._placeholder("Game View — use Play para executar a cena."), "Game")

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

        create_panel = QWidget()
        create_layout = QVBoxLayout(create_panel)
        create_layout.setContentsMargins(6, 6, 6, 6)
        self.create_buttons = {}
        for label, kind in (
            ("Empty Object", "Empty"), ("Sprite 2D", "Sprite"),
            ("Player 2D", "Player"), ("Platform 2D", "Platform"),
            ("Enemy 2D", "Enemy"), ("Trigger 2D", "Trigger"),
            ("Camera 2D", "Camera"),
        ):
            button = QPushButton(label)
            button.setObjectName("CreatePresetButton")
            self.create_buttons[kind] = button
            create_layout.addWidget(button)
        create_layout.addStretch(1)

        hierarchy_tabs = QTabWidget()
        hierarchy_tabs.addTab(hierarchy, "Hierarchy")
        hierarchy_tabs.addTab(create_panel, "Criar")

        prefab_tree = QTreeWidget()
        prefab_tree.setHeaderHidden(True)
        prefab_tree.addTopLevelItem(QTreeWidgetItem(["Prefabs disponíveis no projeto"] ))
        asset_tabs = QTabWidget()
        asset_tabs.addTab(assets, "Assets")
        asset_tabs.addTab(prefab_tree, "Adicionar Prefabs")

        left = QSplitter(Qt.Vertical)
        left.setChildrenCollapsible(False)
        left.addWidget(hierarchy_tabs)
        left.addWidget(asset_tabs)
        left.setSizes([300, 420])
        left.setMinimumWidth(240)

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
        self.add_component_button = QPushButton("Adicionar Componente")
        self.add_component_button.setObjectName("InspectorAddComponentButton")
        form.addRow(self.add_component_button)
        inspector.setMinimumWidth(300)

        console = QPlainTextEdit()
        self.console_output = console
        console.setReadOnly(True)
        console.setPlainText("[INFO] Interface isolada iniciada.\n[INFO] Nenhuma cena foi carregada.\n[INFO] Nenhum frame Pygame será renderizado.")
        self.profiler_label = QLabel("FPS: --\nObjetos: 0\nModo: EDIT")
        self.profiler_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        profiler = self._placeholder("")
        profiler.layout().addWidget(self.profiler_label)

        console_tabs = QTabWidget()
        console_tabs.addTab(console, "Console")
        console_tabs.addTab(self._placeholder("Saída da engine"), "Saída")
        console_tabs.addTab(self._placeholder("Depurador"), "Depurador")

        self.preview_label = QLabel("Selecione um asset para visualizar")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview = self._placeholder("")
        preview.layout().addWidget(self.preview_label)

        console_row = QSplitter(Qt.Horizontal)
        console_row.addWidget(console_tabs)
        console_row.addWidget(profiler)
        console_row.setSizes([650, 240])

        center = QSplitter(Qt.Vertical)
        center.setChildrenCollapsible(False)
        center.addWidget(self.viewport_tabs)
        center.addWidget(console_row)
        center.addWidget(preview)
        center.setSizes([560, 150, 150])

        main = QSplitter(Qt.Horizontal)
        main.setChildrenCollapsible(False)
        main.addWidget(left)
        main.addWidget(center)
        main.addWidget(inspector)
        main.setStretchFactor(1, 1)
        main.setSizes([270, 850, 320])
        self.main_splitter = main
        self.setCentralWidget(main)

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
