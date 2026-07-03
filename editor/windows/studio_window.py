from __future__ import annotations

from PySide6.QtCore import Qt

from editor.core.editor_mvp import install_editor_mvp
from editor.windows.main_window import MainWindow


class StudioWindow(MainWindow):
    """Janela alternativa com layout mais próximo de uma engine profissional."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ZennityStudioWindow")
        self.setWindowTitle("Zennity Engine Editor - Studio")
        self.menuBar().show()
        install_editor_mvp(self)
        self.apply_studio_layout()
        self.statusBar().showMessage("Studio Editor pronto", 5000)

    def apply_studio_layout(self) -> None:
        """Organiza os docks no estilo Hierarchy / Viewport / Inspector / Console."""
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_hierarchy)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_create)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_assets)
        self.splitDockWidget(self.dock_hierarchy, self.dock_create, Qt.Vertical)
        self.splitDockWidget(self.dock_create, self.dock_assets, Qt.Vertical)

        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_inspector)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_profiler)
        self.tabifyDockWidget(self.dock_console, self.dock_profiler)
        self.dock_console.raise_()

        self.dock_hierarchy.show()
        self.dock_create.show()
        self.dock_assets.show()
        self.dock_inspector.show()
        self.dock_console.show()
        self.dock_profiler.show()
