import os
from PySide6.QtWidgets import (
    QMainWindow, QMessageBox,
    QFileDialog, QDialog
)
from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import Qt, Slot, QSettings

# Barramento de Eventos do Editor
from editor.core.event_bus import (
    EventBus, EVENT_PLAY_STATE_CHANGED, EVENT_HIERARCHY_UPDATED, EVENT_ASSET_SELECTED, EVENT_PROPERTY_CHANGED
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
from editor.widgets.code_editor_dock import CodeEditorDock
from editor.widgets.profiler_dock import ProfilerDock

# ── NOVO: Container com abas Scene / Game ─────────────────────────────────────
from editor.widgets.viewport_tab_bar import ViewportContainer

# Diálogos
from editor.windows.main_window_menus import MainWindowMenusMixin
from editor.windows.preferences_dialog import PreferencesDialog


class MainWindow(MainWindowMenusMixin, QMainWindow):
    """
    Janela Principal do Zennity Editor construída sobre o PySide6.

    A viewport agora está embrulhada dentro de um ViewportContainer que expõe
    as abas Scene (edição + grid) e Game (play mode + câmera ativa, sem grid).
    O atributo `self.viewport` continua apontando para o ViewportWidget interno,
    garantindo compatibilidade com todo o código existente.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Zennity Engine Editor - NovoProjeto.zscene*")
        self.resize(1280, 800)

        # Configura as opções de Docking
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)

        # Inicializa o Model e o ViewModel de Cena
        self.scene_model = SceneModel()
        self.scene_view_model = SceneViewModel(self.scene_model)

        # Inicializa o Model e o ViewModel de Assets
        self.asset_model = AssetModel(self)
        self.asset_view_model = AssetViewModel(self.asset_model)

        # Viewport gráfica: agora dentro do container com abas Scene/Game
        self.setup_central_widget()

        # Inicializa docks do editor
        self.create_docks()

        # Conecta os ViewModels aos docks e viewport
        self.dock_hierarchy.set_viewmodel(self.scene_view_model)
        self.dock_inspector.set_viewmodel(self.scene_view_model)
        self.dock_assets.set_models(self.asset_model, self.asset_view_model)
        # set_viewmodel é chamado via container — propaga para o viewport interno
        self.vp_container.set_viewmodel(self.scene_view_model)

        # ── Inscrições no EventBus ────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────────────────────────
    # Widget central
    # ──────────────────────────────────────────────────────────────────────────

    def setup_central_widget(self) -> None:
        """
        Cria o ViewportContainer (abas Scene/Game + viewport OpenGL) e o define
        como widget central.

        O atributo `self.viewport` aponta para o ViewportWidget *interno* do
        container para manter compatibilidade com todo o código existente.
        """
        self.vp_container = ViewportContainer(parent=self)
        # Atalho de compatibilidade — todo código que usa self.viewport continua funcionando
        self.viewport = self.vp_container.viewport
        self.setCentralWidget(self.vp_container)

    # ──────────────────────────────────────────────────────────────────────────
    # Docks
    # ──────────────────────────────────────────────────────────────────────────

    def create_docks(self) -> None:
        """Instancia os painéis acopláveis."""
        self.dock_hierarchy = HierarchyDock(self)
        self.dock_assets    = AssetBrowserDock(self)
        self.dock_console   = ConsoleDock(self)
        self.dock_inspector = InspectorDock(self)
        self.dock_code_editor = CodeEditorDock(self)
        self.dock_code_editor.hide()
        self.dock_profiler  = ProfilerDock(self)

        self.addDockWidget(Qt.LeftDockWidgetArea,   self.dock_hierarchy)
        self.addDockWidget(Qt.RightDockWidgetArea,  self.dock_inspector)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_assets)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_profiler)
        self.addDockWidget(Qt.RightDockWidgetArea,  self.dock_code_editor)

        self.tabifyDockWidget(self.dock_console, self.dock_profiler)
        self.splitDockWidget(self.dock_assets, self.dock_console, Qt.Horizontal)

    def apply_default_layout(self) -> None:
        """Posiciona os docks na disposição padrão."""
        self.addDockWidget(Qt.LeftDockWidgetArea,   self.dock_hierarchy)
        self.addDockWidget(Qt.RightDockWidgetArea,  self.dock_inspector)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_assets)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_profiler)
        self.addDockWidget(Qt.RightDockWidgetArea,  self.dock_code_editor)

        self.tabifyDockWidget(self.dock_console, self.dock_profiler)
        self.splitDockWidget(self.dock_assets, self.dock_console, Qt.Horizontal)

        self.dock_hierarchy.show()
        self.dock_inspector.show()
        self.dock_assets.show()
        self.dock_console.show()
        self.dock_profiler.show()
        self.dock_code_editor.hide()

        self.log_action("Layout padrão em grade horizontal restaurado")

    def save_layout_state(self) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.log_action("Layout do editor salvo com sucesso")

    def restore_layout_state(self) -> bool:
        geom  = self.settings.value("geometry")
        state = self.settings.value("windowState")
        if geom is not None and state is not None:
            self.restoreGeometry(geom)
            self.restoreState(state)
            self.log_action("Layout anterior restaurado")
            return True
        return False

    def apply_preferences_on_init(self) -> None:
        grid_on = self.prefs.value("grid_on_init", "true") == "true"
        self.act_toggle_grid.setChecked(grid_on)
        self.act_toggle_grid.setText("Grade: ON" if grid_on else "Grade: OFF")
        grid_size = int(self.prefs.value("grid_size", 32))
        self.log_action(f"Preferências carregadas: Grade={grid_size}px (Ativa={grid_on})")

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.prefs.value("auto_layout", "true") == "true":
            self.save_layout_state()
        event.accept()

    # ──────────────────────────────────────────────────────────────────────────
    # Ações
    # ──────────────────────────────────────────────────────────────────────────



    # ──────────────────────────────────────────────────────────────────────────
    # Slots de Ação
    # ──────────────────────────────────────────────────────────────────────────

    def log_action(self, action_name: str) -> None:
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
                    self.scene_view_model.selected_object = (
                        self.viewport.active_scene.editable_objects[
                            self.viewport.active_scene.selected_index
                        ]
                    )

    @Slot()
    def on_save_scene(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Cena Zennity", "",
            "Cena Zennity (*.zscene);;Todos os arquivos (*.*)"
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
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Abrir Cena Zennity", "",
            "Cena Zennity (*.zscene);;Todos os arquivos (*.*)"
        )
        if not filepath:
            return
        try:
            loaded_objs = load_scene_from_file(filepath)
            self.scene_model.clear()
            self.scene_view_model.selected_object = None

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
        dialog = PreferencesDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.log_action("Preferências salvas e aplicadas.")

    @Slot()
    def update_object_count_status(self) -> None:
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
        self.statusBar().showMessage(f"Asset selecionado: {os.path.basename(filepath)}", 3000)
        self.log_action(f"Recurso selecionado via EventBus: {filepath}")

    @Slot(str, str, object)
    def on_bus_property_changed(self, component_name: str, property_name: str, value: object) -> None:
        if component_name == "Editor":
            if property_name == "grid_size" and value is not None:
                grid_sz = int(value)
                if hasattr(self.viewport, "active_scene") and self.viewport.active_scene:
                    if hasattr(self.viewport.active_scene, "grid_size"):
                        self.viewport.active_scene.grid_size = grid_sz
            elif property_name == "grid_state" and value is not None:
                grid_on = bool(value)
                self.act_toggle_grid.setChecked(grid_on)
                self.act_toggle_grid.setText("Grade: ON" if grid_on else "Grade: OFF")

    # ── Play / Pause / Stop ──────────────────────────────────────────────────

    @Slot()
    def on_play_clicked(self) -> None:
        self.log_action("PLAY - Iniciando simulação física")
        self.btn_play.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.statusBar().showMessage("Simulação em execução...")
        # Sincroniza a aba visualmente sem acionar o callback _on_tab_changed
        # (force_switch evita o double-emit de EVENT_PLAY_STATE_CHANGED)
        self.vp_container.tab_bar.force_switch("game")
        self.vp_container.viewport.set_game_mode(True)
        self.vp_container.viewport.update()
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
        # Sincroniza a aba visualmente sem acionar o callback _on_tab_changed
        self.vp_container.tab_bar.force_switch("scene")
        self.vp_container.viewport.set_game_mode(False)
        self.vp_container.viewport.update()
        EventBus.emit(EVENT_PLAY_STATE_CHANGED, state="stop")

    # ── Ferramentas e grade ──────────────────────────────────────────────────

    def on_transform_tool_changed(self, tool_name: str) -> None:
        action_map = {
            "select": self.act_tool_select,
            "move":   self.act_tool_move,
            "rotate": self.act_tool_rotate,
            "scale":  self.act_tool_scale,
        }
        target = action_map.get(tool_name)
        for act in self.transform_actions:
            act.setChecked(act is target)
        self.log_action(f"Ferramenta alterada para: {tool_name.upper()}")
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Editor",
                      property_name="tool_mode", value=tool_name)

    @Slot(bool)
    def on_grid_toggled(self, enabled: bool) -> None:
        self.act_toggle_grid.setText("Grade: ON" if enabled else "Grade: OFF")
        self.log_action(f"Exibição da grade: {'Habilitada' if enabled else 'Desabilitada'}")
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Editor",
                      property_name="grid_state", value=enabled)

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
    def _on_duplicate_triggered(self) -> None:
        self.viewport.duplicate_selected_object()
        self.log_action("Ctrl+D — objeto duplicado")

    @Slot()
    def _on_delete_triggered(self) -> None:
        self.viewport.delete_selected_object()
        self.log_action("Delete — objeto excluído")

    @Slot()
    def on_undo_triggered(self) -> None:
        scene = getattr(self.viewport, "active_scene", None)
        if scene and hasattr(scene, "undo"):
            scene.undo()
            self.log_action("Undo executado")
            self.viewport._sync_model_from_scene()

    @Slot()
    def on_redo_triggered(self) -> None:
        scene = getattr(self.viewport, "active_scene", None)
        if scene and hasattr(scene, "redo"):
            scene.redo()
            self.log_action("Redo executado")
            self.viewport._sync_model_from_scene()

    @Slot(str)
    def on_camera_mode_changed(self, text: str) -> None:
        mode = "2D" if "2D" in text else "3D"
        self.log_action(f"Alterando modo de câmera para: {mode}")
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Editor",
                      property_name="camera_mode", value=mode)

    @Slot()
    def on_export_project(self) -> None:
        dest_dir = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta para Exportar o Jogo"
        )
        if not dest_dir:
            return
        try:
            root_objs = self.scene_view_model.get_root_objects()
            from editor.core.exporter import export_project
            export_project(dest_dir, root_objs)
            QMessageBox.information(
                self, "Exportação Concluída",
                f"Jogo exportado com sucesso para:\n{dest_dir}\n\n"
                "Para jogar, execute o arquivo 'jogar.bat' (Windows) ou 'jogar.sh' (Linux/macOS)."
            )
            self.log_action(f"Build exportado com sucesso para: {dest_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Exportação", f"Falha ao empacotar jogo:\n{str(e)}")
