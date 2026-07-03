import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QMenuBar, QMenu, QToolBar, QStatusBar,
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QDockWidget
)
from PySide6.QtGui import QAction, QKeySequence, QIcon, QCloseEvent
from PySide6.QtCore import Qt, Slot, QSettings

# Modelos e ViewModels MVVM
from editor.models.scene_model import SceneModel
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.models.asset_model import AssetModel
from editor.viewmodels.asset_viewmodel import AssetViewModel

# Widgets do Editor
from editor.widgets.hierarchy_dock import HierarchyDock
from editor.widgets.asset_browser_dock import AssetBrowserDock
from editor.widgets.console_dock import ConsoleDock
from editor.widgets.inspector_dock import InspectorDock


class MainWindow(QMainWindow):
    """
    Janela Principal do Zennity Editor construída sobre o PySide6.
    
    Implementação da Semana 4:
      - Sistema de Asset Browser (MVVM) com navegação de diretórios e grid
      - Sincronização e filtros de pesquisa de assets
      - Integração com a barra de status ao selecionar recursos
    """
    
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle("Zennity Engine Editor - NovoProjeto.zproj*")
        self.resize(1280, 800)
        
        # Configura as opções de Docking
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        
        # Inicializa o Model e o ViewModel de Cena (Semana 3)
        self.scene_model = SceneModel()
        self.scene_view_model = SceneViewModel(self.scene_model)
        
        # Inicializa o Model e o ViewModel de Assets (Semana 4)
        self.asset_model = AssetModel(self)
        self.asset_view_model = AssetViewModel(self.asset_model)
        
        # Central widget temporário (Viewport)
        self.setup_central_widget()
        
        # Inicializa docks do editor
        self.create_docks()
        
        # Conecta os ViewModels aos docks
        self.dock_hierarchy.set_viewmodel(self.scene_view_model)
        self.dock_inspector.set_viewmodel(self.scene_view_model)
        self.dock_assets.set_models(self.asset_model, self.asset_view_model)
        
        # Conecta sinais
        self.scene_view_model.hierarchy_updated.connect(self.update_object_count_status)
        self.asset_view_model.asset_selected.connect(self.on_asset_selected)
        
        # Inicializa ações e menus
        self.create_actions()
        self.create_menu_bar()
        self.create_tool_bar()
        self.create_status_bar()
        
        # Tenta carregar o layout anterior, senão aplica o layout padrão (Unreal)
        self.settings = QSettings("Zennity", "EditorLayout")
        if not self.restore_layout_state():
            self.apply_default_layout()
            
        self.statusBar().showMessage("Zennity Editor pronto.", 5000)

    def setup_central_widget(self) -> None:
        """Configura a área central provisória do editor."""
        central = QWidget()
        central.setStyleSheet("background-color: #12141a;")
        
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("Zennity Viewport (PySide6)\n[OpenGL/Viewport Central - Semana 6]")
        label.setStyleSheet("color: #484e5f; font-size: 16px; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(label)
        self.setCentralWidget(central)

    def create_docks(self) -> None:
        """Instancia os painéis acopláveis."""
        self.dock_hierarchy = HierarchyDock(self)
        self.dock_assets    = AssetBrowserDock(self)
        self.dock_console   = ConsoleDock(self)
        self.dock_inspector = InspectorDock(self)
        
        # Adiciona à janela principal
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_hierarchy)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_assets)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_inspector)

    def apply_default_layout(self) -> None:
        """Posiciona os docks na disposição padrão inspirada na Unreal Engine."""
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_hierarchy)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_assets)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_inspector)
        
        # Empilha Hierarchy sobre AssetBrowser na esquerda
        self.splitDockWidget(self.dock_hierarchy, self.dock_assets, Qt.Vertical)
        
        # Garante que todos estejam visíveis
        self.dock_hierarchy.show()
        self.dock_assets.show()
        self.dock_console.show()
        self.dock_inspector.show()
        
        self.log_action("Layout padrão da Unreal restaurado")

    def save_layout_state(self) -> None:
        """Salva a geometria e o estado dos painéis acopláveis."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.log_action("Layout do editor salvo com sucesso")

    def restore_layout_state(self) -> bool:
        """Restaura o estado salvo dos painéis. Retorna True se restaurado."""
        geom = self.settings.value("geometry")
        state = self.settings.value("windowState")
        
        if geom is not None and state is not None:
            self.restoreGeometry(geom)
            self.restoreState(state)
            self.log_action("Layout anterior restaurado")
            return True
        return False

    def closeEvent(self, event: QCloseEvent) -> None:
        """Evento de fechamento: salva automaticamente o layout antes de sair."""
        self.save_layout_state()
        event.accept()

    def create_actions(self) -> None:
        """Cria as ações reutilizáveis para menus e toolbars."""
        # ── Arquivo ──────────────────────────────────────────
        self.act_new = QAction("Novo", self)
        self.act_new.setShortcut(QKeySequence.New)
        self.act_new.triggered.connect(self.on_new_scene)
        
        self.act_open = QAction("Abrir...", self)
        self.act_open.setShortcut(QKeySequence.Open)
        self.act_open.triggered.connect(lambda: self.log_action("Abrir Projeto"))
        
        self.act_save = QAction("Salvar", self)
        self.act_save.setShortcut(QKeySequence.Save)
        self.act_save.triggered.connect(lambda: self.log_action("Salvar Projeto"))
        
        self.act_exit = QAction("Sair", self)
        self.act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_exit.triggered.connect(self.close)

        # ── Editar ──────────────────────────────────────────
        self.act_undo = QAction("Desfazer", self)
        self.act_undo.setShortcut(QKeySequence.Undo)
        self.act_undo.triggered.connect(lambda: self.log_action("Undo"))
        
        self.act_redo = QAction("Refazer", self)
        self.act_redo.setShortcut(QKeySequence.Redo)
        self.act_redo.triggered.connect(lambda: self.log_action("Redo"))
        
        self.act_duplicate = QAction("Duplicar", self)
        self.act_duplicate.setShortcut(QKeySequence("Ctrl+D"))
        self.act_duplicate.triggered.connect(self.scene_view_model.duplicate_selected)
        
        self.act_delete = QAction("Excluir", self)
        self.act_delete.setShortcut(QKeySequence.Delete)
        self.act_delete.triggered.connect(self.scene_view_model.delete_selected)

        # ── Ajuda ──────────────────────────────────────────
        self.act_commands = QAction("Guia de Comandos", self)
        self.act_commands.setShortcut(QKeySequence("F1"))
        self.act_commands.triggered.connect(self.show_commands_guide)
        
        self.act_about = QAction("Sobre o Zennity Editor", self)
        self.act_about.triggered.connect(self.show_about_dialog)

    def create_menu_bar(self) -> None:
        """Monta a barra de menus superior."""
        menubar = self.menuBar()
        
        # Menu Arquivo
        menu_file = menubar.addMenu("Arquivo")
        menu_file.addAction(self.act_new)
        menu_file.addAction(self.act_open)
        menu_file.addAction(self.act_save)
        menu_file.addSeparator()
        menu_file.addAction(self.act_exit)
        
        # Menu Editar
        menu_edit = menubar.addMenu("Editar")
        menu_edit.addAction(self.act_undo)
        menu_edit.addAction(self.act_redo)
        menu_edit.addSeparator()
        menu_edit.addAction(self.act_duplicate)
        menu_edit.addAction(self.act_delete)
        
        # Menu Janela (Dock Widgets Toggles)
        menu_window = menubar.addMenu("Janela")
        self.act_reset_layout = QAction("Restaurar Layout Padrão", self)
        self.act_reset_layout.triggered.connect(self.apply_default_layout)
        menu_window.addAction(self.act_reset_layout)
        menu_window.addSeparator()
        
        menu_window.addAction(self.dock_hierarchy.toggleViewAction())
        menu_window.addAction(self.dock_inspector.toggleViewAction())
        menu_window.addAction(self.dock_assets.toggleViewAction())
        menu_window.addAction(self.dock_console.toggleViewAction())
        
        # Menu Criar (Create - novos GameObjects na cena)
        menu_create = menubar.addMenu("Criar")
        shapes = ["Quadrado", "Círculo", "Plataforma", "Player", "Inimigo", "Trigger", "Mola"]
        for s in shapes:
            act = QAction(s, self)
            act.triggered.connect(lambda checked=False, shape_type=s: self.scene_view_model.create_object(shape_type))
            menu_create.addAction(act)
        
        # Menu Ajuda
        menu_help = menubar.addMenu("Ajuda")
        menu_help.addAction(self.act_commands)
        menu_help.addAction(self.act_about)

    def create_tool_bar(self) -> None:
        """Cria e organiza a barra de ferramentas (Toolbar) principal."""
        toolbar = self.addToolBar("Ferramentas")
        toolbar.setObjectName("MainToolBar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # ── Controles de Simulação ──────────────────────────
        self.btn_play = QPushButton(" ▶  PLAY ")
        self.btn_play.setStyleSheet("background-color: #306430; border-color: #204c20;")
        self.btn_play.clicked.connect(self.on_play_clicked)
        
        self.btn_pause = QPushButton(" ⏸  PAUSE ")
        self.btn_pause.setStyleSheet("background-color: #2b303f;")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.on_pause_clicked)
        
        self.btn_stop = QPushButton(" ■  STOP ")
        self.btn_stop.setStyleSheet("background-color: #8c2424; border-color: #601818;")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.on_stop_clicked)
        
        toolbar.addWidget(self.btn_play)
        toolbar.addWidget(self.btn_pause)
        toolbar.addWidget(self.btn_stop)
        
        toolbar.addSeparator()
        
        # ── Controles de Ferramentas (Transformação) ────────
        self.act_tool_select = QAction("Select", self, checkable=True, checked=True)
        self.act_tool_select.triggered.connect(lambda: self.on_transform_tool_changed("select"))
        
        self.act_tool_move = QAction("Move", self, checkable=True)
        self.act_tool_move.triggered.connect(lambda: self.on_transform_tool_changed("move"))
        
        self.act_tool_rotate = QAction("Rotate", self, checkable=True)
        self.act_tool_rotate.triggered.connect(lambda: self.on_transform_tool_changed("rotate"))
        
        self.act_tool_scale = QAction("Scale", self, checkable=True)
        self.act_tool_scale.triggered.connect(lambda: self.on_transform_tool_changed("scale"))
        
        self.transform_actions = [self.act_tool_select, self.act_tool_move, 
                                  self.act_tool_rotate, self.act_tool_scale]
        
        for act in self.transform_actions:
            toolbar.addAction(act)
            
        toolbar.addSeparator()
        
        # ── Toggle de Grade ────────────────────────────────
        self.act_toggle_grid = QAction("Grade: ON", self, checkable=True, checked=True)
        self.act_toggle_grid.triggered.connect(self.on_grid_toggled)
        toolbar.addAction(self.act_toggle_grid)

    def create_status_bar(self) -> None:
        """Configura a barra de status inferior e seus widgets permanentes."""
        statusbar = self.statusBar()
        
        # Widgets permanentes à direita (estatísticas)
        self.lbl_fps = QLabel("FPS: 60  ")
        self.lbl_mem = QLabel("Memória: 12.4 MB  ")
        self.lbl_obj = QLabel("Objetos: 0  ")
        
        for lbl in (self.lbl_fps, self.lbl_mem, self.lbl_obj):
            lbl.setStyleSheet("color: #828a9b; font-family: monospace; font-size: 11px;")
            statusbar.addPermanentWidget(lbl)

    # ──────────────────────────────────────────────────────────────────────────
    # Slots de Ação e Lógica
    # ──────────────────────────────────────────────────────────────────────────
    
    def log_action(self, action_name: str) -> None:
        """Imprime log informativo da ação no console do desenvolvedor."""
        print(f"[ACTION] Disparado: {action_name}")
        self.statusBar().showMessage(f"Executando: {action_name}", 3000)

    @Slot()
    def on_new_scene(self) -> None:
        self.log_action("Novo Projeto/Cena")
        self.scene_model.clear()
        self.scene_view_model.selected_object = None

    @Slot()
    def update_object_count_status(self) -> None:
        """Atualiza dinamicamente a contagem de objetos na barra de status."""
        count = 0
        def count_rec(objs):
            nonlocal count
            for o in objs:
                count += 1
                count_rec(o.children)
                
        count_rec(self.scene_view_model.get_root_objects())
        self.lbl_obj.setText(f"Objetos: {count}  ")

    @Slot(str)
    def on_asset_selected(self, filepath: str) -> None:
        """Chamado quando um recurso é selecionado no Asset Browser."""
        self.statusBar().showMessage(f"Asset selecionado: {os.path.basename(filepath)}", 3000)
        self.log_action(f"Recurso selecionado: {filepath}")

    @Slot()
    def on_play_clicked(self) -> None:
        self.log_action("PLAY - Iniciando simulação física")
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.statusBar().showMessage("Simulação em execução...")

    @Slot()
    def on_pause_clicked(self) -> None:
        self.log_action("PAUSE - Pausando simulação")
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.statusBar().showMessage("Simulação pausada.")

    @Slot()
    def on_stop_clicked(self) -> None:
        self.log_action("STOP - Encerrando simulação")
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.statusBar().showMessage("Simulação finalizada.")

    def on_transform_tool_changed(self, tool_name: str) -> None:
        """Garante seleção exclusiva entre as ferramentas de transformação."""
        action_map = {
            "select": self.act_tool_select,
            "move": self.act_tool_move,
            "rotate": self.act_tool_rotate,
            "scale": self.act_tool_scale
        }
        
        target = action_map.get(tool_name)
        for act in self.transform_actions:
            act.setChecked(act is target)
            
        self.log_action(f"Ferramenta alterada para: {tool_name.upper()}")

    @Slot(bool)
    def on_grid_toggled(self, enabled: bool) -> None:
        self.act_toggle_grid.setText("Grade: ON" if enabled else "Grade: OFF")
        self.log_action(f"Exibição da grade: {'Habilitada' if enabled else 'Desabilitada'}")

    @Slot()
    def show_commands_guide(self) -> None:
        QMessageBox.information(
            self, "Guia de Comandos",
            "Atalhos Rápidos:\n\n"
            "- Ctrl+N: Novo Projeto\n"
            "- Ctrl+O: Abrir Projeto\n"
            "- Ctrl+S: Salvar Projeto\n"
            "- Ctrl+D: Duplicar Entidade\n"
            "- Delete: Excluir Entidade\n"
            "- F1: Guia de Comandos"
        )

    @Slot()
    def show_about_dialog(self) -> None:
        QMessageBox.about(
            self, "Sobre o Zennity Editor",
            "<h3>Zennity Engine Editor v0.1.0</h3>"
            "<p>Um editor de jogos modular escrito em Python e PySide6.</p>"
            "<p>Inspirado no visual profissional e moderno da Unreal Engine.</p>"
        )
