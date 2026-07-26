"""Mixin de criação de menus e barra de ferramentas para MainWindow."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QComboBox, QLabel, QPushButton


class MainWindowMenusMixin:
    """Isola ações, menubar, toolbar e statusbar de MainWindow."""

    def create_actions(self) -> None:
        self.act_new = QAction("Novo", self)
        self.act_new.setShortcut(QKeySequence.New)
        self.act_new.triggered.connect(self.on_new_scene)

        self.act_open = QAction("Abrir Cena...", self)
        self.act_open.setShortcut(QKeySequence.Open)
        self.act_open.triggered.connect(self.on_open_scene)

        self.act_save = QAction("Salvar", self)
        self.act_save.setShortcut(QKeySequence.Save)
        self.act_save.triggered.connect(self.on_save_scene)

        self.act_export = QAction("Exportar Jogo...", self)
        self.act_export.setShortcut(QKeySequence("Ctrl+E"))
        self.act_export.triggered.connect(self.on_export_project)

        self.act_exit = QAction("Sair", self)
        self.act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_exit.triggered.connect(self.close)

        self.act_undo = QAction("Desfazer", self)
        self.act_undo.setShortcut(QKeySequence.Undo)
        self.act_undo.triggered.connect(self.on_undo_triggered)

        self.act_redo = QAction("Refazer", self)
        self.act_redo.setShortcut(QKeySequence.Redo)
        self.act_redo.triggered.connect(self.on_redo_triggered)

        self.act_duplicate = QAction("Duplicar", self)
        self.act_duplicate.setShortcut(QKeySequence("Ctrl+D"))
        self.act_duplicate.triggered.connect(self._on_duplicate_triggered)

        self.act_delete = QAction("Excluir", self)
        self.act_delete.setShortcut(QKeySequence.Delete)
        self.act_delete.triggered.connect(self._on_delete_triggered)

        self.act_preferences = QAction("Preferências...", self)
        self.act_preferences.triggered.connect(self.show_preferences_dialog)

        self.act_commands = QAction("Guia de Comandos", self)
        self.act_commands.setShortcut(QKeySequence("F1"))
        self.act_commands.triggered.connect(self.show_commands_guide)

        self.act_about = QAction("Sobre o Zennity Editor", self)
        self.act_about.triggered.connect(self.show_about_dialog)

    def create_menu_bar(self) -> None:
        menubar = self.menuBar()

        menu_file = menubar.addMenu("Arquivo")
        menu_file.addAction(self.act_new)
        menu_file.addAction(self.act_open)
        menu_file.addAction(self.act_save)
        menu_file.addAction(self.act_export)
        menu_file.addSeparator()
        menu_file.addAction(self.act_exit)

        menu_edit = menubar.addMenu("Editar")
        menu_edit.addAction(self.act_undo)
        menu_edit.addAction(self.act_redo)
        menu_edit.addSeparator()
        menu_edit.addAction(self.act_duplicate)
        menu_edit.addAction(self.act_delete)
        menu_edit.addSeparator()
        menu_edit.addAction(self.act_preferences)

        menu_window = menubar.addMenu("Janela")
        self.act_reset_layout = QAction("Restaurar Layout Padrão", self)
        self.act_reset_layout.triggered.connect(self.apply_default_layout)
        menu_window.addAction(self.act_reset_layout)
        menu_window.addSeparator()
        menu_window.addAction(self.dock_hierarchy.toggleViewAction())
        menu_window.addAction(self.dock_inspector.toggleViewAction())
        menu_window.addAction(self.dock_assets.toggleViewAction())
        menu_window.addAction(self.dock_console.toggleViewAction())
        menu_window.addAction(self.dock_profiler.toggleViewAction())
        menu_window.addAction(self.dock_code_editor.toggleViewAction())

        menu_tools = menubar.addMenu("Ferramentas & Editores")
        self.act_visual_logic = QAction("Editor de Lógica Visual", self)
        self.act_visual_logic.setShortcut(QKeySequence("Ctrl+Shift+L"))
        self.act_visual_logic.triggered.connect(
            lambda: self.dock_visual_scripting.open_graph_tool("visual_scripting")
        )
        menu_tools.addAction(self.act_visual_logic)
        menu_tools.addAction(self.dock_ui_builder.toggleViewAction())
        menu_tools.addSeparator()
        menu_tools.addAction(self.dock_extension_manager.toggleViewAction())
        menu_tools.addAction(self.dock_dependency_viewer.toggleViewAction())
        menu_tools.addAction(self.dock_build_report.toggleViewAction())
        menu_tools.addAction(self.dock_asset_auditor.toggleViewAction())
        menu_tools.addAction(self.dock_build_wizard.toggleViewAction())
        menu_tools.addAction(self.dock_project_settings.toggleViewAction())

        menu_create = menubar.addMenu("Criar")
        shapes = ["Quadrado", "Círculo", "Plataforma", "Player", "Inimigo", "Trigger", "Mola"]
        for s in shapes:
            act = QAction(s, self)
            act.triggered.connect(
                lambda checked=False, shape_type=s: self.viewport.create_object(shape_type)
            )
            menu_create.addAction(act)

        menu_help = menubar.addMenu("Ajuda")
        menu_help.addAction(self.act_commands)
        menu_help.addAction(self.act_about)

    def create_tool_bar(self) -> None:
        toolbar = self.addToolBar("Ferramentas")
        toolbar.setObjectName("MainToolBar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.btn_play = QPushButton(" ▶  PLAY ")
        self.btn_play.setStyleSheet(
            "background-color: #2e7d32; border: 1px solid #1b5e20; color: white;"
            "padding: 4px 12px; border-radius: 6px; font-weight: bold;"
        )
        self.btn_play.clicked.connect(self.on_play_clicked)

        self.btn_pause = QPushButton(" ⏸  PAUSE ")
        self.btn_pause.setStyleSheet(
            "background-color: #37474f; border: 1px solid #263238; color: #cfd4de;"
            "padding: 4px 12px; border-radius: 6px; font-weight: bold;"
        )
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.on_pause_clicked)

        self.btn_stop = QPushButton(" ■  STOP ")
        self.btn_stop.setStyleSheet(
            "background-color: #c62828; border: 1px solid #b71c1c; color: white;"
            "padding: 4px 12px; border-radius: 6px; font-weight: bold;"
        )
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.on_stop_clicked)

        toolbar.addWidget(self.btn_play)
        toolbar.addWidget(self.btn_pause)
        toolbar.addWidget(self.btn_stop)
        toolbar.addSeparator()

        self.act_tool_select = QAction("Select", self, checkable=True, checked=True)
        self.act_tool_select.triggered.connect(lambda: self.on_transform_tool_changed("select"))

        self.act_tool_move = QAction("Move", self, checkable=True)
        self.act_tool_move.triggered.connect(lambda: self.on_transform_tool_changed("move"))

        self.act_tool_rotate = QAction("Rotate", self, checkable=True)
        self.act_tool_rotate.triggered.connect(lambda: self.on_transform_tool_changed("rotate"))

        self.act_tool_scale = QAction("Scale", self, checkable=True)
        self.act_tool_scale.triggered.connect(lambda: self.on_transform_tool_changed("scale"))

        self.transform_actions = [
            self.act_tool_select,
            self.act_tool_move,
            self.act_tool_rotate,
            self.act_tool_scale,
        ]
        for act in self.transform_actions:
            toolbar.addAction(act)

        toolbar.addSeparator()

        self.act_toggle_grid = QAction("Grade: ON", self, checkable=True, checked=True)
        self.act_toggle_grid.triggered.connect(self.on_grid_toggled)
        toolbar.addAction(self.act_toggle_grid)
        toolbar.addSeparator()

        self.cb_camera_mode = QComboBox()
        self.cb_camera_mode.addItems(["Visualização 2D", "Visualização 3D"])
        self.cb_camera_mode.setStyleSheet(
            "background-color: #2b2e38; color: #e3e8f0; border: 1px solid #3c4050;"
            "padding: 2px 6px; border-radius: 3px;"
        )
        self.cb_camera_mode.currentTextChanged.connect(self.on_camera_mode_changed)
        toolbar.addWidget(self.cb_camera_mode)

    def create_status_bar(self) -> None:
        statusbar = self.statusBar()
        self.lbl_fps = QLabel("FPS: 60  ")
        self.lbl_mem = QLabel("Memória: 12.4 MB  ")
        self.lbl_obj = QLabel("Objetos: 0  ")
        _s = (
            "color: #cfd4de; font-family: 'JetBrains Mono', 'Cascadia Code', monospace;"
            "font-size: 11px; font-weight: 600; margin-right: 10px;"
        )
        for lbl in (self.lbl_fps, self.lbl_mem, self.lbl_obj):
            lbl.setStyleSheet(_s)
            statusbar.addPermanentWidget(lbl)
