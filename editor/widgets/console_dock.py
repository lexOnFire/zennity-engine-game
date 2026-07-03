import io
import sys
import traceback
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QComboBox, QLabel
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor, QFont

# Barramento de Eventos do Editor
from editor.core.event_bus import EventBus, EVENT_LOG_ADDED


class ConsoleDock(QDockWidget):
    """
    Painel acoplável do Console de Logs e Terminal Interativo Python.
    Componente 'View' na arquitetura MVVM do editor (Semana 8).
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Console", parent)
        self.setObjectName("ConsoleDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)
        
        self.log_history = []  # Guarda tuplas de (mensagem, tipo) para filtragem
        self.command_history = []  # Histórico de comandos Python digitados
        self.history_index = -1
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 1. Barra de Controles Superior
        controls = QWidget()
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(0, 0, 0, 2)
        
        self.cb_filter = QComboBox()
        self.cb_filter.addItems(["Todos os Níveis", "Informações", "Avisos", "Erros", "Depuração"])
        self.cb_filter.currentIndexChanged.connect(self.apply_filter)
        self.cb_filter.setFixedWidth(140)
        
        self.btn_clear = QPushButton("Limpar Console")
        self.btn_clear.clicked.connect(self.clear_console)
        self.btn_clear.setFixedWidth(110)
        
        ctrl_layout.addWidget(QLabel("Logs do Sistema:"))
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.cb_filter)
        ctrl_layout.addWidget(self.btn_clear)
        layout.addWidget(controls)
        
        # 2. Área de Exibição de Texto Rico
        self.txt_display = QTextEdit()
        self.txt_display.setReadOnly(True)
        self.txt_display.setFont(QFont("Consolas", 10))
        self.txt_display.setStyleSheet(
            "background-color: #111217; border: 1px solid #2d313f; border-radius: 4px;"
            "padding: 6px; color: #e3e8f0;"
        )
        layout.addWidget(self.txt_display)
        
        # 3. Terminal Interativo (Linha de Comando)
        cmd_panel = QWidget()
        cmd_layout = QHBoxLayout(cmd_panel)
        cmd_layout.setContentsMargins(0, 2, 0, 0)
        
        self.txt_input = QLineEdit()
        self.txt_input.setPlaceholderText("Inserir comando Python (ex: print(viewmodel.selected_object))")
        self.txt_input.returnPressed.connect(self.execute_command)
        
        self.btn_run = QPushButton("Executar")
        self.btn_run.clicked.connect(self.execute_command)
        self.btn_run.setFixedWidth(80)
        
        cmd_layout.addWidget(self.txt_input)
        cmd_layout.addWidget(self.btn_run)
        layout.addWidget(cmd_panel)
        
        self.setWidget(content)
        
        # Filtro de eventos para capturar Up/Down e navegar no histórico
        self.txt_input.installEventFilter(self)
        
        # Inscreve-se no EventBus para receber logs em tempo real
        EventBus.subscribe(EVENT_LOG_ADDED, self.on_bus_log_received)

    @Slot(str, str)
    def on_bus_log_received(self, message: str, type: str) -> None:
        """Recebe log bruto e o adiciona ao histórico."""
        self.log_history.append((message, type))
        self.render_log(message, type)

    def render_log(self, message: str, type: str) -> None:
        """Renderiza um único log aplicando formatação HTML e cores do tema."""
        # Filtra na hora com base na seleção do combo box
        active_filter = self.cb_filter.currentText()
        if active_filter == "Informações" and type != "info":     return
        if active_filter == "Avisos" and type != "warning":       return
        if active_filter == "Erros" and type != "error":          return
        if active_filter == "Depuração" and type != "debug":      return
        
        color_map = {
            "info": "#a3be8c",     # Verde pastel
            "warning": "#ebcb8b",  # Amarelo mostarda
            "error": "#bf616a",    # Vermelho escuro/terracota
            "debug": "#88c0d0"     # Azul claro/ciano
        }
        color = color_map.get(type, "#e3e8f0")
        
        # Limpa caracteres ANSI extras do Pygame nos logs
        clean_msg = message.replace("\033[32m", "").replace("\033[33m", "").replace("\033[31m", "").replace("\033[36m", "").replace("\033[0m", "")
        
        html_msg = f"<span style='color: {color};'>{clean_msg}</span>"
        self.txt_display.append(html_msg)
        
        # Rola o console para a base automática
        self.txt_display.moveCursor(QTextCursor.End)

    @Slot()
    def apply_filter(self) -> None:
        """Refaz o desenho completo com base no filtro selecionado."""
        self.txt_display.clear()
        for msg, t in self.log_history:
            self.render_log(msg, t)

    @Slot()
    def clear_console(self) -> None:
        """Limpa todo o console."""
        self.log_history.clear()
        self.txt_display.clear()

    @Slot()
    def execute_command(self) -> None:
        """Executa comandos em Python de forma interativa no escopo do editor."""
        cmd_str = self.txt_input.text().strip()
        if not cmd_str:
            return
            
        self.txt_input.clear()
        
        # Adiciona ao histórico de comandos digitados
        if cmd_str:
            if not self.command_history or self.command_history[-1] != cmd_str:
                self.command_history.append(cmd_str)
            self.history_index = -1
        
        # Mostra o comando digitado no console
        self.on_bus_log_received(f">>> {cmd_str}", "debug")
        
        # Redirecionamento da saída padrão
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirected_output = sys.stdout = io.StringIO()
        redirected_error = sys.stderr = io.StringIO()
        
        # Contexto de execução exposto para scripts
        win = self.window()
        loc_env = {
            "editor": win,
            "viewmodel": win.scene_view_model if hasattr(win, "scene_view_model") else None,
            "model": win.scene_model if hasattr(win, "scene_model") else None,
            "viewport": win.viewport if hasattr(win, "viewport") else None,
            "scene": win.viewport.active_scene if hasattr(win, "viewport") and hasattr(win.viewport, "active_scene") else None
        }
        
        try:
            # Tenta rodar como expressão (ex: 1+1)
            try:
                code = compile(cmd_str, "<string>", "eval")
                res = eval(code, globals(), loc_env)
                if res is not None:
                    print(res)
            except SyntaxError:
                # Se falhar a sintaxe de expressão, roda como bloco executável (ex: import math)
                code = compile(cmd_str, "<string>", "exec")
                exec(code, globals(), loc_env)
        except Exception:
            traceback.print_exc(file=sys.stderr)
            
        # Restaura a saída padrão
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Captura saídas geradas
        stdout_res = redirected_output.getvalue().strip()
        stderr_res = redirected_error.getvalue().strip()
        
        if stdout_res:
            self.on_bus_log_received(stdout_res, "info")
        if stderr_res:
            self.on_bus_log_received(stderr_res, "error")

    def eventFilter(self, watched, event) -> bool:
        """Filtra eventos para permitir navegação no histórico de comandos com as setas Up/Down."""
        from PySide6.QtCore import QEvent
        if watched == self.txt_input and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                if self.command_history:
                    if self.history_index == -1:
                        self.history_index = len(self.command_history) - 1
                    else:
                        self.history_index = max(0, self.history_index - 1)
                    self.txt_input.setText(self.command_history[self.history_index])
                    # Move o cursor para o fim da linha
                    self.txt_input.setCursorPosition(len(self.txt_input.text()))
                return True
            elif key == Qt.Key_Down:
                if self.command_history:
                    if self.history_index != -1:
                        self.history_index += 1
                        if self.history_index >= len(self.command_history):
                            self.history_index = -1
                            self.txt_input.clear()
                        else:
                            self.txt_input.setText(self.command_history[self.history_index])
                            self.txt_input.setCursorPosition(len(self.txt_input.text()))
                return True
        return super().eventFilter(watched, event)
