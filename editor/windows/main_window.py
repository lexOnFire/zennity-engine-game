import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QMenuBar, QMenu, QToolBar, QStatusBar,
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
)
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtCore import Qt, Slot


class MainWindow(QMainWindow):
    """
    Janela Principal do Zennity Editor construída sobre o PySide6.
    
    Implementação da Semana 1:
      - Estrutura base de janela
      - Barra de menus (Menu Bar)
      - Barra de ferramentas (Tool Bar) com controles de simulação e transformação
      - Barra de status (Status Bar) com estatísticas da engine
    """
    
    def __init__(self) -> None:
        super().__init__()
        
        self.setWindowTitle("Zennity Engine Editor - NovoProjeto.zproj*")
        self.resize(1280, 800)
        
        # Central widget temporário (espaço reservado para a Viewport na Semana 6)
        self.setup_central_widget()
        
        # Inicializa componentes da interface
        self.create_actions()
        self.create_menu_bar()
        self.create_tool_bar()
        self.create_status_bar()
        
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

    def create_actions(self) -> None:
        """Cria as ações reutilizáveis para menus e toolbars."""
        # ── Arquivo ──────────────────────────────────────────
        self.act_new = QAction("Novo", self)
        self.act_new.setShortcut(QKeySequence.New)
        self.act_new.triggered.connect(lambda: self.log_action("Novo Projeto"))
        
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
        self.act_duplicate.triggered.connect(lambda: self.log_action("Duplicar Entidade"))
        
        self.act_delete = QAction("Excluir", self)
        self.act_delete.setShortcut(QKeySequence.Delete)
        self.act_delete.triggered.connect(lambda: self.log_action("Excluir Entidade"))

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
        
        # Menu Janela
        menu_window = menubar.addMenu("Janela")
        self.act_reset_layout = QAction("Restaurar Layout Padrão", self)
        self.act_reset_layout.triggered.connect(lambda: self.log_action("Restaurar Layout"))
        menu_window.addAction(self.act_reset_layout)
        menu_window.addSeparator()
        # Futuras docas (semana 2)
        menu_window.addAction(QAction("Hierarchy", self, checkable=True, checked=True))
        menu_window.addAction(QAction("Inspector", self, checkable=True, checked=True))
        menu_window.addAction(QAction("Recursos (Asset Browser)", self, checkable=True, checked=True))
        menu_window.addAction(QAction("Console", self, checkable=True, checked=True))
        
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
        
        # Agrupa as ações para que apenas uma fique selecionada por vez (estilo rádio)
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
        self.lbl_obj = QLabel("Objetos: 2  ")
        
        # Aplica estilo muted sutil
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
