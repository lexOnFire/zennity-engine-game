import os
from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QKeySequence, QAction


class CodeEditorDock(QDockWidget):
    """
    Painel acoplável do Editor de Código.
    Permite codificar os scripts de comportamento dos objetos diretamente no Qt.
    Componente 'View' na arquitetura MVVM do editor (Semana 12).
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Editor de Código", parent)
        self.setObjectName("CodeEditorDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        
        self.filepath = ""
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 1. Barra de ferramentas superior
        tools = QWidget()
        t_layout = QHBoxLayout(tools)
        t_layout.setContentsMargins(2, 2, 2, 2)
        
        self.lbl_filename = QLabel("Nenhum arquivo aberto")
        self.lbl_filename.setStyleSheet("color: #a3be8c; font-weight: bold;")
        
        self.btn_save = QPushButton("Salvar Script")
        self.btn_save.setFixedWidth(100)
        self.btn_save.clicked.connect(self.save_file)
        self.btn_save.setEnabled(False)
        
        t_layout.addWidget(self.lbl_filename)
        t_layout.addStretch()
        t_layout.addWidget(self.btn_save)
        layout.addWidget(tools)
        
        # 2. Área de Edição
        self.txt_editor = QPlainTextEdit()
        self.txt_editor.setFont(QFont("Consolas", 10))
        self.txt_editor.setStyleSheet(
            "background-color: #1a1c23; color: #f8f8f2; border: 1px solid #2d313f;"
            "padding: 6px; border-radius: 4px;"
        )
        self.txt_editor.setTabStopDistance(32)  # Configura indentação
        self.txt_editor.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.txt_editor)
        
        self.setWidget(content)
        
        # Atalho de teclado para salvar (Ctrl+S)
        self.act_save_shortcut = QAction(self)
        self.act_save_shortcut.setShortcut(QKeySequence.Save)
        self.act_save_shortcut.triggered.connect(self.save_file)
        self.addAction(self.act_save_shortcut)

    def open_file(self, filepath: str) -> None:
        """Carrega o conteúdo do arquivo de script no editor."""
        if not os.path.exists(filepath):
            return
            
        self.filepath = filepath
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
                
            # Temporariamente desconecta o sinal para evitar marcar como modificado ao carregar
            self.txt_editor.textChanged.disconnect(self.on_text_changed)
            self.txt_editor.setPlainText(code)
            self.txt_editor.textChanged.connect(self.on_text_changed)
            
            self.lbl_filename.setText(os.path.basename(filepath))
            self.btn_save.setEnabled(False)
            self.show()
            self.raise_()
        except Exception as e:
            QMessageBox.critical(self, "Erro de Leitura", f"Não foi possível abrir o script:\n{str(e)}")

    @Slot()
    def save_file(self) -> None:
        """Salva as alterações de código de volta ao arquivo no disco."""
        if not self.filepath:
            return
            
        try:
            code = self.txt_editor.toPlainText()
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write(code)
                
            self.btn_save.setEnabled(False)
            self.lbl_filename.setText(os.path.basename(self.filepath))
            
            # Mostra mensagem rápida na barra de status se disponível
            win = self.window()
            if win and hasattr(win, "statusBar"):
                win.statusBar().showMessage(f"Script salvo com sucesso: {os.path.basename(self.filepath)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Erro de Salvamento", f"Falha ao salvar script:\n{str(e)}")

    @Slot()
    def on_text_changed(self) -> None:
        """Marca o arquivo como contendo alterações não salvas."""
        if self.filepath:
            self.lbl_filename.setText(os.path.basename(self.filepath) + "*")
            self.btn_save.setEnabled(True)
