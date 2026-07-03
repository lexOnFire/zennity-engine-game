import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QMenuBar, QMenu, QToolBar, QStatusBar,
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QDockWidget, QFileDialog
)
from PySide6.QtGui import QAction, QKeySequence, QIcon, QCloseEvent
from PySide6.QtCore import Qt, Slot, QSettings

# Barramento de Eventos do Editor
from editor.core.event_bus import (
    EventBus, EVENT_PLAY_STATE_CHANGED, EVENT_SELECTION_CHANGED,
    EVENT_HIERARCHY_UPDATED, EVENT_ASSET_SELECTED, EVENT_PROPERTY_CHANGED
)

# Modelos e ViewModels MVVM
from editor.models.scene_model import SceneModel
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.models.asset_model import AssetModel
from editor.viewmodels.asset_viewmodel import AssetViewModel

# Serialização
from editor.core.serializer import save_scene_to_file, load_scene_from_file

# Widgets do Editor
from editor.widgets.hierarchy_dock import HierarchyDock
from editor.widgets.asset_browser_dock import AssetBrowserDock
from editor.widgets.console_dock import ConsoleDock
from editor.widgets.inspector_dock import InspectorDock
from editor.widgets.viewport_widget import ViewportWidget
from editor.widgets.code_editor_dock import CodeEditorDock

# Diálogos
from editor.windows.preferences_dialog import PreferencesDialog


class MainWindow(QMainWindow):
    """
    Janela Principal do Zennity Editor construída sobre o PySide6.
    
    Implementação da Semana 11:
      - Gerenciamento de projetos e cenas (.zscene JSON)
      - Diálogo de preferências persistente com QSettings
    """
    
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle("Zennity Engine Editor - NovoProjeto.zscene*")
        self.resize(1280, 800)
        
        # Configura as opções de Docking
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        
        # Inicializa o Model e o ViewModel de Cena (Semana 3)
        self.scene_model = SceneModel()
        self.scene_view_model = SceneViewModel(self.scene_model)
        
        # Inicializa o Model e o ViewModel de Assets (Semana 4)
        self.asset_model = AssetModel(self)
        self.asset_view_model = AssetViewModel(self.asset_model)
        
        # Viewport gráfica baseada em OpenGL (Semana 6)
        self.setup_central_widget()
        
        # Inicializa docks do editor
        self.create_docks()
        
        # Conecta os ViewModels aos docks e viewport
        self.dock_hierarchy.set_viewmodel(self.scene_view_model)
        self.dock_inspector.set_viewmodel(self.scene_view_model)
        self.dock_assets.set_models(self.asset_model, self.asset_view_model)
        self.viewport.set_viewmodel(self.scene_view_model)
        
        # ── Inscrições no EventBus (Desacoplado) ──────────────────────────────
        EventBus.subscribe(EVENT_HIERARCHY_UPDATED, self.update_object_count_status)
        EventBus.subscribe(EVENT_ASSET_SELECTED, self.on_bus_asset_selected)
        EventBus.subscribe(EVENT_PROPERTY_CHANGED, self.on_bus_property_changed)
        
        # Inicializa ações e menus
        self.create_actions()
        self.create_menu_bar()
        self.create_tool_bar()
        self.create_status_bar()
        
        # Sincroniza contagem inicial
        self.update_object_count_status()
        
        # Tenta carregar o layout anterior e preferências do usuário
        self.settings = QSettings("Zennity", "EditorLayout")
        self.prefs = QSettings("Zennity", "Preferences")
        
        # Aplica preferências iniciais do QSettings
        self.apply_preferences_on_init()
        
        # Auto-restauração do Layout de Docks se ativado
        if self.prefs.value("auto_layout", "true") == "true":
            if not self.restore_layout_state():
                self.apply_default_layout()
        else:
            self.apply_default_layout()
            
        self.statusBar().showMessage("Zennity Editor pronto.", 5000)

    def setup_central_widget(self) -> None:
        """Configura a área central gráfica OpenGL (Viewport)."""
        self.viewport = ViewportWidget(self)
        self.setCentralWidget(self.viewport)

    def create_docks(self) -> None:
        """Instancia os painéis acopláveis."""
        self.dock_hierarchy = HierarchyDock(self)
        self.dock_assets    = AssetBrowserDock(self)
        self.dock_console   = ConsoleDock(self)
        self.dock_inspector = InspectorDock(self)
        self.dock_code_editor = CodeEditorDock(self)
        self.dock_code_editor.hide()  # Inicializa fechado
        
        # Adiciona à janela principal
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_hierarchy)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_assets)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_inspector)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_code_editor)

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
        self.dock_code_editor.hide()
        
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

    def apply_preferences_on_init(self) -> None:
        """Aplica preferências salvas de grade e auto-layout."""
        grid_on = self.prefs.value("grid_on_init", "true") == "true"
        self.act_toggle_grid.setChecked(grid_on)
        self.act_toggle_grid.setText("Grade: ON" if grid_on else "Grade: OFF")
        
        grid_size = int(self.prefs.value("grid_size", 32))
        self.log_action(f"Preferências carregadas: Grade={grid_size}px (Ativa={grid_on})")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Evento de fechamento: salva layout se auto_layout estiver habilitado."""
        if self.prefs.value("auto_layout", "true") == "true":
            self.save_layout_state()
        event.accept()

    def create_actions(self) -> None:
        """Cria as ações reutilizáveis para menus e toolbars."""
        # ── Arquivo ──────────────────────────────────────────
        self.act_new = QAction("Novo", self)
        self.act_new.setShortcut(QKeySequence.New)
        self.act_new.triggered.connect(self.on_new_scene)
        
        self.act_open = QAction("Abrir Cena...", self)
        self.act_open.setShortcut(QKeySequence.Open)
        self.act_open.triggered.connect(self.on_open_scene)
        
        self.act_save = QAction("Salvar", self)
        self.act_save.setShortcut(QKeySequence.Save)
        self.act_save.triggered.connect(self.on_save_scene)
        
        self.act_exit = QAction("Sair", self)
        self.act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_exit.triggered.connect(self.close)

        # ── Editar ──────────────────────────────────────────
        self.act_undo = QAction("Desfazer", self)
        self.act_undo.setShortcut(QKeySequence.Undo)
        self.act_undo.triggered.connect(self.on_undo_triggered)
        
        self.act_redo = QAction("Refazer", self)
        self.act_redo.setShortcut(QKeySequence.Redo)
        self.act_redo.triggered.connect(self.on_redo_triggered)
        
        self.act_duplicate = QAction("Duplicar", self)
        self.act_duplicate.setShortcut(QKeySequence("Ctrl+D"))
        self.act_duplicate.triggered.connect(self.scene_view_model.duplicate_selected)
        
        self.act_delete = QAction("Excluir", self)
        self.act_delete.setShortcut(QKeySequence.Delete)
        self.act_delete.triggered.connect(self.scene_view_model.delete_selected)
        
        self.act_preferences = QAction("Preferências...", self)
        self.act_preferences.triggered.connect(self.show_preferences_dialog)

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
        menu_edit.addSeparator()
        menu_edit.addAction(self.act_preferences)
        
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
        menu_window.addAction(self.dock_code_editor.toggleViewAction())
        
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
        self.setWindowTitle("Zennity Engine Editor - NovoProjeto.zscene*")
        
        if hasattr(self.viewport, "active_scene") and self.viewport.active_scene:
            if hasattr(self.viewport.active_scene, "editable_objects"):
                self.viewport.active_scene.editable_objects.clear()
                self.viewport.active_scene.game_objects.clear()
                self.viewport.active_scene.selected_index = -1
                self.viewport.active_scene.spawn_default_scene()
                
                for obj in self.viewport.active_scene.editable_objects:
                    self.scene_model.add_object(obj)
                if self.viewport.active_scene.selected_index >= 0:
                    self.scene_view_model.selected_object = self.viewport.active_scene.editable_objects[self.viewport.active_scene.selected_index]

    @Slot()
    def on_save_scene(self) -> None:
        """Salva a cena física ativa e o outliner em um arquivo .zscene JSON."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Cena Zennity", "", "Cena Zennity (*.zscene);;Todos os arquivos (*.*)"
        )
        if not filepath:
            return
            
        try:
            root_objs = self.scene_view_model.get_root_objects()
            save_scene_to_file(filepath, root_objs)
            self.setWindowTitle(f"Zennity Engine Editor - {os.path.basename(filepath)}")
            self.statusBar().showMessage(f"Cena salva em: {os.path.basename(filepath)}", 4000)
            self.log_action(f"Cena gravada em disco: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Persistência", f"Falha ao salvar cena:\n{str(e)}")

    @Slot()
    def on_open_scene(self) -> None:
        """Carrega e desserializa um arquivo .zscene JSON na viewport e outliner."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Abrir Cena Zennity", "", "Cena Zennity (*.zscene);;Todos os arquivos (*.*)"
        )
        if not filepath:
            return
            
        try:
            loaded_objs = load_scene_from_file(filepath)
            
            # Limpa o estado atual
            self.scene_model.clear()
            self.scene_view_model.selected_object = None
            
            # Repopula a viewport
            if hasattr(self.viewport, "active_scene") and self.viewport.active_scene:
                self.viewport.active_scene.editable_objects.clear()
                self.viewport.active_scene.game_objects.clear()
                
                for obj in loaded_objs:
                    self.viewport.active_scene.add_game_object(obj)
                    if hasattr(self.viewport.active_scene, "editable_objects"):
                        self.viewport.active_scene.editable_objects.append(obj)
                    self.scene_model.add_object(obj)
                    
                self.viewport.active_scene.selected_index = -1
                self.scene_view_model.on_model_hierarchy_changed()
                
            self.setWindowTitle(f"Zennity Engine Editor - {os.path.basename(filepath)}")
            self.statusBar().showMessage(f"Cena carregada: {os.path.basename(filepath)}", 4000)
            self.log_action(f"Cena carregada do disco: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Leitura", f"Falha ao carregar cena:\n{str(e)}")

    @Slot()
    def show_preferences_dialog(self) -> None:
        """Abre a janela de preferências do usuário."""
        dialog = PreferencesDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.log_action("Preferências salvas e aplicadas.")

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
    def on_bus_asset_selected(self, filepath: str) -> None:
        """Slot ouvinte de eventos do EventBus para seleção de recursos."""
        self.statusBar().showMessage(f"Asset selecionado: {os.path.basename(filepath)}", 3000)
        self.log_action(f"Recurso selecionado via EventBus: {filepath}")

    @Slot(str, str, object)
    def on_bus_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        """Ouvinte do EventBus para mudanças nas preferências ou configurações."""
        if component_name == "Editor":
            if property_name == "grid_size" and value is not None:
                # Se alterou o tamanho da grade nas preferências, atualiza a grade da cena se necessário
                grid_sz = int(value)
                if hasattr(self.viewport, "active_scene") and self.viewport.active_scene:
                    if hasattr(self.viewport.active_scene, "grid_size"):
                        self.viewport.active_scene.grid_size = grid_sz
            elif property_name == "grid_state" and value is not None:
                grid_on = bool(value)
                self.act_toggle_grid.setChecked(grid_on)
                self.act_toggle_grid.setText("Grade: ON" if grid_on else "Grade: OFF")

    @Slot()
    def on_play_clicked(self) -> None:
        self.log_action("PLAY - Iniciando simulação física")
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.statusBar().showMessage("Simulação em execução...")
        
        EventBus.emit(EVENT_PLAY_STATE_CHANGED, state="play")

    @Slot()
    def on_pause_clicked(self) -> None:
        self.log_action("PAUSE - Pausando simulação")
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        
        EventBus.emit(EVENT_PLAY_STATE_CHANGED, state="pause")

    @Slot()
    def on_stop_clicked(self) -> None:
        self.log_action("STOP - Encerrando simulação")
        self.btn_play.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.statusBar().showMessage("Simulação finalizada.")
        
        EventBus.emit(EVENT_PLAY_STATE_CHANGED, state="stop")

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
        
        # Publica no EventBus para a Viewport atualizar seus Gizmos
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Editor", property_name="tool_mode", value=tool_name)

    @Slot(bool)
    def on_grid_toggled(self, enabled: bool) -> None:
        self.act_toggle_grid.setText("Grade: ON" if enabled else "Grade: OFF")
        self.log_action(f"Exibição da grade: {'Habilitada' if enabled else 'Desabilitada'}")
        
        # Se a grade foi ligada/desligada na barra, repassa para as preferências e o EventBus
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Editor", property_name="grid_state", value=enabled)

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

    @Slot()
    def on_undo_triggered(self) -> None:
        """Slot para o comando Undo global."""
        if hasattr(self.viewport, "active_scene") and self.viewport.active_scene:
            if hasattr(self.viewport.active_scene, "undo"):
                self.viewport.active_scene.undo()
                self.log_action("Undo executado")
                
                # Sincroniza a árvore de objetos do modelo após a reversão
                self.scene_model.clear()
                for obj in self.viewport.active_scene.editable_objects:
                    self.scene_model.add_object(obj)
                self.scene_view_model.on_model_hierarchy_changed()

    @Slot()
    def on_redo_triggered(self) -> None:
        """Slot para o comando Redo global."""
        if hasattr(self.viewport, "active_scene") and self.viewport.active_scene:
            if hasattr(self.viewport.active_scene, "redo"):
                self.viewport.active_scene.redo()
                self.log_action("Redo executado")
                
                # Sincroniza a árvore de objetos do modelo após o redo
                self.scene_model.clear()
                for obj in self.viewport.active_scene.editable_objects:
                    self.scene_model.add_object(obj)
                self.scene_view_model.on_model_hierarchy_changed()
