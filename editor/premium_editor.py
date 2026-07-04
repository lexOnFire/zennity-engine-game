from __future__ import annotations

import sys
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextBrowser,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from editor.models.scene_model import SceneModel
from editor.runtime.editor_context import EditorContext
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.widgets.viewport_widget import ViewportWidget


class Panel(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("PremiumPanel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        header = QWidget()
        header.setObjectName("PanelHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(8, 4, 8, 4)
        label = QLabel(title)
        label.setObjectName("PanelHeaderTitle")
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(QLabel("gear x"))
        self.layout.addWidget(header)


class HierarchyPanel(Panel):
    selected = Signal(str)

    def __init__(self) -> None:
        super().__init__("Hierarchy")
        search = QLineEdit()
        search.setPlaceholderText("Filtrar...")
        search.setObjectName("SearchBox")
        self.layout.addWidget(search)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.layout.addWidget(self.tree)
        self.populate()
        self.tree.itemSelectionChanged.connect(self._selected)

    def populate(self) -> None:
        self.tree.clear()
        root = QTreeWidgetItem(self.tree, ["MainScene"])
        for name in ["Environment", "DirectionalLight", "Camera", "Player", "Enemies"]:
            item = QTreeWidgetItem(root, [name])
            item.setData(0, Qt.UserRole, name)
        root.setExpanded(True)

    def add_object(self, name: str) -> None:
        root = self.tree.topLevelItem(0)
        item = QTreeWidgetItem(root, [name])
        item.setData(0, Qt.UserRole, name)
        root.setExpanded(True)
        self.tree.setCurrentItem(item)

    def _selected(self) -> None:
        item = self.tree.currentItem()
        if item:
            self.selected.emit(item.data(0, Qt.UserRole) or item.text(0))


class ResourcesPanel(Panel):
    def __init__(self) -> None:
        super().__init__("Recursos")
        search = QLineEdit()
        search.setPlaceholderText("Filtrar assets...")
        search.setObjectName("SearchBox")
        self.layout.addWidget(search)
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        self.layout.addWidget(tree)
        root = QTreeWidgetItem(tree, ["Assets"])
        for folder, files in {
            "Animations": ["player_idle.anim", "enemy_walk.anim"],
            "Materials": ["default.mat", "brick.mat"],
            "Meshes": ["cube.mesh", "plane.mesh"],
            "Scenes": ["MainScene.zscene"],
            "Scripts": ["player_controller.py"],
            "Textures": ["brick_diffuse.png"],
            "Audio": ["jump.wav"],
        }.items():
            folder_item = QTreeWidgetItem(root, [folder])
            for file_name in files:
                QTreeWidgetItem(folder_item, [file_name])
        root.setExpanded(True)


class CreatePanel(Panel):
    create_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__("Criar")
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 8, 8, 8)
        groups = [
            ("2D", ["Player", "Plataforma", "Inimigo", "Sprite 2D", "Camera 2D"]),
            ("3D experimental", ["Cube 3D", "Plane 3D", "Camera 3D", "Light 3D"]),
            ("Templates", ["Plataforma 2D", "Top-down 2D"]),
        ]
        for title, items in groups:
            label = QLabel(title)
            label.setObjectName("SectionLabel")
            body_layout.addWidget(label)
            for item in items:
                button = QPushButton(item)
                button.setObjectName("CreatePresetButton")
                button.clicked.connect(lambda checked=False, value=item: self.create_requested.emit(value))
                body_layout.addWidget(button)
        body_layout.addStretch(1)
        self.layout.addWidget(body)


class InspectorPanel(Panel):
    def __init__(self) -> None:
        super().__init__("Inspector")
        self.name = QLabel("Nenhum objeto selecionado")
        self.name.setObjectName("InspectorTitle")
        self.layout.addWidget(self.name)
        for section in ["Transform", "Renderer", "Collider", "Scripts"]:
            label = QLabel(section + "\n  X: 0    Y: 0    Z: 0")
            label.setObjectName("InspectorSection")
            self.layout.addWidget(label)
        self.layout.addStretch(1)

    def load_object(self, name: str) -> None:
        self.name.setText(name)


class ConsolePanel(Panel):
    def __init__(self) -> None:
        super().__init__("Console")
        self.log = QTextBrowser()
        self.log.setObjectName("ConsoleLog")
        self.layout.addWidget(self.log)
        self.add("INFO", "Zennity Premium Editor iniciado.")

    def add(self, level: str, message: str) -> None:
        color = {"INFO": "#8bc34a", "WARN": "#ffc107", "ERROR": "#f44336"}.get(level, "#aaaaaa")
        self.log.append(f'<span style="color:{color}">[{level}]</span> {message}')


class SimplePanel(Panel):
    def __init__(self, title: str, text: str) -> None:
        super().__init__(title)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)


class ZennityPremiumEditor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ZennityPremiumEditor")
        self.setWindowTitle("Zennity Engine Editor - Premium")
        self.resize(1440, 900)
        self.object_count = 0
        if not hasattr(self, "editor_context"):
            self.editor_context = EditorContext()
        self.scene_model = SceneModel()
        self.scene_view_model = SceneViewModel(
            self.scene_model,
            selection_manager=self.editor_context.selection,
        )
        self._build_menu()
        self._build_toolbar()
        self._build_layout()
        self._build_status()
        self._connect()

    def _build_menu(self) -> None:
        bar = self.menuBar()
        for name in ["Arquivo", "Editar", "Janela", "Criar", "Ferramentas", "Build + Executar", "Ajuda"]:
            menu = bar.addMenu(name)
            if name == "Criar":
                for item in ["Player", "Plataforma", "Inimigo", "Camera 2D", "Cube 3D"]:
                    menu.addAction(item, lambda checked=False, value=item: self.create_object(value))
            elif name == "Build + Executar":
                menu.addAction("Play", self.play)
                menu.addAction("Stop", self.stop)

    def _build_toolbar(self) -> None:
        tb = QToolBar("MainToolBar")
        tb.setObjectName("CommandBar")
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)
        for text in ["Open", "Save", "Undo", "Redo"]:
            tb.addWidget(QToolButton(text=text))
        spacer = QWidget()
        spacer.setMinimumWidth(300)
        tb.addWidget(spacer)
        self.btn_play = QToolButton()
        self.btn_play.setText("Play")
        self.btn_play.clicked.connect(self.play)
        tb.addWidget(self.btn_play)
        btn_stop = QToolButton()
        btn_stop.setText("Stop")
        btn_stop.clicked.connect(self.stop)
        tb.addWidget(btn_stop)
        tb.addWidget(QComboBox())

    def _build_layout(self) -> None:
        self.hierarchy = HierarchyPanel()
        self.resources = ResourcesPanel()
        self.create_panel = CreatePanel()
        self.inspector = InspectorPanel()
        self.console = ConsolePanel()
        self.preview = SimplePanel("Asset Preview", "Preview de assets")
        self.profiler = SimplePanel("Profiler", "FPS, CPU, memoria")

        self.viewport = ViewportWidget(self)
        self.viewport.setObjectName("ViewportCanvas")
        self.viewport.set_viewmodel(self.scene_view_model)

        left = QSplitter(Qt.Vertical)
        left.addWidget(self.hierarchy)
        left.addWidget(self.resources)
        left.addWidget(self.create_panel)
        left.setSizes([320, 260, 220])

        center = QSplitter(Qt.Vertical)
        center.addWidget(self.viewport)
        bottom = QSplitter(Qt.Horizontal)
        bottom.addWidget(self.console)
        bottom.addWidget(self.preview)
        bottom.addWidget(self.profiler)
        bottom.setSizes([520, 260, 260])
        center.addWidget(bottom)
        center.setSizes([560, 240])

        main = QSplitter(Qt.Horizontal)
        main.addWidget(left)
        main.addWidget(center)
        main.addWidget(self.inspector)
        main.setSizes([260, 850, 300])
        self.setCentralWidget(main)

    def _build_status(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_msg = QLabel("Projeto salvo.")
        self.stats = QLabel("FPS: 60 | Memoria: 512 MB | Objetos: 0")
        status.addWidget(self.status_msg)
        status.addPermanentWidget(self.stats)

    def _connect(self) -> None:
        self.hierarchy.selected.connect(self.inspector.load_object)
        self.create_panel.create_requested.connect(self.create_object)

    def create_object(self, name: str) -> None:
        mapping = {"Sprite 2D": "Quadrado", "Cube 3D": "Cube", "Plane 3D": "Plane"}
        value = mapping.get(name, name)
        if hasattr(self.viewport, "create_object"):
            self.viewport.create_object(value)
        self.object_count += 1
        display_name = f"{name}_{self.object_count}"
        self.hierarchy.add_object(display_name)
        self.inspector.load_object(display_name)
        self.stats.setText(f"FPS: 60 | Memoria: 512 MB | Objetos: {self.object_count}")
        self.console.add("INFO", f"Objeto criado: {name}")

    def play(self) -> None:
        self.viewport._on_play_state_changed("play")
        self.status_msg.setText("Simulacao ativa.")
        self.console.add("INFO", "Play iniciado.")

    def stop(self) -> None:
        self.viewport._on_play_state_changed("stop")
        self.status_msg.setText("Simulacao parada.")
        self.console.add("INFO", "Play finalizado.")


def run() -> None:
    app = QApplication(sys.argv)
    from editor.premium_theme import PREMIUM_QSS
    app.setStyleSheet(PREMIUM_QSS)
    win = ZennityPremiumEditor()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
