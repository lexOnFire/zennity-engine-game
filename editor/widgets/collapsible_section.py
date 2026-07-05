from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, Slot


class CollapsibleSection(QWidget):
    """
    Seção colapsável/expansível usada no Inspector para agrupar propriedades de componentes.
    Suporta ícones, botão de reset e menu de ações estilo Unity/Godot.
    """
    
    toggled = Signal(bool)  # Emite True se expandido, False se colapsado

    def __init__(self, title: str, icon_str: str = "", parent: QWidget = None) -> None:
        super().__init__(parent)
        
        self._is_expanded = True
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 4)
        self.main_layout.setSpacing(0)
        
        # Cabeçalho da seção
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet(
            "background-color: #2b2b2b; border: 1px solid #202020; border-radius: 4px;"
        )
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(6, 2, 6, 2)
        self.header_layout.setSpacing(4)
        
        # Botão/Indicador de seta
        self.btn_toggle = QPushButton("▼")
        self.btn_toggle.setFixedWidth(16)
        self.btn_toggle.setStyleSheet(
            "background: transparent; border: none; font-weight: bold; color: #a0a0a0; font-size: 10px;"
        )
        self.btn_toggle.clicked.connect(self.toggle_collapse)
        
        # Ícone do Componente
        self.lbl_icon = QLabel(icon_str)
        self.lbl_icon.setStyleSheet("font-size: 11px; border: none;")
        self.lbl_icon.setVisible(bool(icon_str))
        
        # Título do componente
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(
            "font-weight: bold; color: #e0e0e0; border: none; font-size: 11px;"
        )
        
        # Botões de Ação à direita: Reset (↺) e Menu (⋮)
        self.btn_reset = QPushButton("↺")
        self.btn_reset.setFixedWidth(16)
        self.btn_reset.setToolTip("Resetar Componente")
        self.btn_reset.setStyleSheet(
            "background: transparent; border: none; color: #8c8c8c; font-size: 11px; font-weight: bold;"
        )
        
        self.btn_menu = QPushButton("⋮")
        self.btn_menu.setFixedWidth(12)
        self.btn_menu.setStyleSheet(
            "background: transparent; border: none; color: #8c8c8c; font-size: 11px; font-weight: bold;"
        )
        
        self.header_layout.addWidget(self.btn_toggle)
        self.header_layout.addWidget(self.lbl_icon)
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_reset)
        self.header_layout.addWidget(self.btn_menu)
        
        self.main_layout.addWidget(self.header_widget)
        
        # Área de conteúdo (onde ficam as propriedades)
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(
            "background-color: #1f1f1f; border: none;"
        )
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 6, 10, 6)
        self.content_layout.setSpacing(4)
        
        self.main_layout.addWidget(self.content_widget)

    def set_content_widget(self, widget: QWidget) -> None:
        """Define o widget interno com as propriedades."""
        # Limpa layout antigo
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        self.content_layout.addWidget(widget)

    @Slot()
    def toggle_collapse(self) -> None:
        """Alterna a visibilidade da área de conteúdo."""
        self._is_expanded = not self._is_expanded
        self.content_widget.setVisible(self._is_expanded)
        self.btn_toggle.setText("▼" if self._is_expanded else "▶")
        self.toggled.emit(self._is_expanded)
