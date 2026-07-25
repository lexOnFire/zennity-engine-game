"""Teste isolado da interface do Zennity Editor, sem Pygame ou Viewport.

Execute a partir da raiz do projeto:
    python -m editor.interface_smoke_test
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from editor.ui.icons import TOOLBAR_ICONS, component_title, editor_icon
from editor.ui.empty_state import EmptyStateWidget
from editor.widgets.logic_graph_editor import LogicGraphEditor
from editor.ui.detached_workspace import DetachedWorkspaceWindow


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
        from editor.ui import polish_editor_widgets
        polish_editor_widgets(self)
        self.statusBar().showMessage("Teste isolado: não há Pygame nem renderização de cena.")

    def _build_menu(self) -> None:
        self.editor_menus = {}
        for name in ("Arquivo", "Editar", "Janela", "Criar", "Ferramentas", "Build", "Executar", "Ajuda"):
            menu = self.menuBar().addMenu(name)
            self.editor_menus[name] = menu

        # Popula o menu Ferramentas e Janela com todos os editores visuais e ferramentas de produção
        tool_items = [
            ("Editor de Lógica Visual (Logic Graph)", "visual_scripting", "editor.visual_scripting.visual_scripting_dock", "VisualScriptingEditorDock"),
            ("Animation Studio Visual", "animation_studio", "editor.animation_studio.animation_studio_dock", "AnimationStudioDock"),
            ("Behavior Tree Editor", "behavior_tree", "editor.behavior_tree.behavior_tree_dock", "BehaviorTreeEditorDock"),
            ("Dialogue Graph Editor", "dialogue", "editor.dialogue.dialogue_dock", "DialogueGraphEditorDock"),
            ("Material Graph Editor", "material", "editor.material_graph.material_dock", "MaterialGraphEditorDock"),
            ("UI Builder", "ui_builder", "editor.ui_builder.ui_builder_dock", "UIBuilderDock"),
            ("Ecossistema de Extensões / Plugins", "extension_manager", "editor.extension_manager.extension_dock", "ExtensionManagerDock"),
            ("Grafo de Dependências de Assets", "dependency_viewer", "editor.tools.dependency_viewer_dock", "DependencyViewerDock"),
            ("Build Pipeline & Export", "build_report", "editor.tools.build_report_dock", "BuildReportDock"),
            ("Auditor de Capacidades de Assets", "asset_auditor", "editor.tools.asset_auditor_dock", "AssetAuditorDock"),
            ("Assistente de Build & Export Wizard", "build_wizard", "editor.wizards.build_wizard_dock", "BuildWizardDock"),
            ("Configurações do Projeto", "project_settings", "editor.wizards.project_settings_dock", "ProjectSettingsDock"),
        ]

        tools_menu = self.editor_menus["Ferramentas"]
        janela_menu = self.editor_menus["Janela"]

        for label, attr_name, mod_path, class_name in tool_items:
            act = QAction(label, self)
            act.triggered.connect(
                lambda checked=False, m=mod_path, c=class_name, a=attr_name: self._show_visual_tool_dock(m, c, a)
            )
            tools_menu.addAction(act)
            janela_menu.addAction(act)

    def _show_visual_tool_dock(self, module_path: str, class_name: str, attr_name: str) -> None:
        """Instancia e exibe a dock do editor visual dinamicamente ao ser clicada no menu."""
        dock_attr = f"_dock_{attr_name}"
        dock_widget = getattr(self, dock_attr, None)
        if dock_widget is None:
            import importlib
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            dock_widget = cls(self)
            setattr(self, dock_attr, dock_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, dock_widget)

        dock_widget.show()
        dock_widget.raise_()
        dock_widget.activateWindow()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Ferramentas")
        toolbar.setObjectName("CommandBar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(17, 17))
        self.addToolBar(toolbar)
        self.toolbar_actions = {}
        for label, icon_name in TOOLBAR_ICONS.items():
            action = QAction(editor_icon(icon_name), label, self)
            action.setStatusTip(label)
            action.setToolTip(label)
            self.toolbar_actions[label] = action
            toolbar.addAction(action)
        toolbar.addSeparator()
        mode = QComboBox()
        mode.setObjectName("ModeSwitch")
        mode.addItems(["2D", "3D (experimental)"])
        toolbar.addWidget(mode)

    def _build_center(self) -> None:
        from editor.ui.workspace_builder import build_center_workspace
        build_center_workspace(self)

    def _build_docks(self) -> None:
        from editor.ui.docks_builder import build_docks_layout
        build_docks_layout(self)
    def _dock(self, title: str, widget: QWidget, area: Qt.DockWidgetArea, width: int) -> None:
        dock = QDockWidget(title, self)
        dock.setObjectName(f"SmokeTest_{title}")
        dock.setWidget(widget)
        dock.setMinimumWidth(width if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea) else 200)
        self.addDockWidget(area, dock)

    @staticmethod
    def _placeholder(text: str) -> QWidget:
        return EmptyStateWidget(text or "Nenhum conteúdo", "Este painel ainda não possui dados.")


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    from editor.ui import apply_editor_theme
    apply_editor_theme(app)
    window = InterfaceSmokeTest()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
