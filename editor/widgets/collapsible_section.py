from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, Slot


class CollapsibleSection(QWidget):
    """
    Seção colapsável/expansível usada no Inspector para agrupar propriedades de componentes.
    """
    
    toggled = Signal(bool)  # Emite True se expandido, False se colapsado

    def __init__(self, title: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        
        self._is_expanded = True
        
        # Layout principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 4)
        self.main_layout.setSpacing(0)
        
        # Cabeçalho da seção
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet(
            "background-color: #242730; border: 1px solid #2d313f; border-radius: 4px;"
        )
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(8, 4, 8, 4)
        
        # Botão/Indicador de seta
        self.btn_toggle = QPushButton("▼")
        self.btn_toggle.setFixedWidth(20)
        self.btn_toggle.setStyleSheet("background: transparent; border: none; font-weight: bold; color: #828a9b;")
        self.btn_toggle.clicked.connect(self.toggle_collapse)
        
        # Título do componente
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-weight: bold; color: #e3e8f0; border: none;")
        
        self.header_layout.addWidget(self.btn_toggle)
        self.header_layout.addWidget(self.lbl_title)
        self.header_layout.addStretch()
        
        self.main_layout.addWidget(self.header_widget)
        
        # Área de conteúdo (onde ficam as propriedades)
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #1a1c23; border: none;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 8, 12, 8)
        self.content_layout.setSpacing(6)
        
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
