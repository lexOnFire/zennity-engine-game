from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QCheckBox, QSpinBox, QPushButton, QLabel, QDialogButtonBox
)
from PySide6.QtCore import Qt, QSettings


class PreferencesDialog(QDialog):
    """
    Diálogo para configurar preferências globais do Zennity Editor.
    Componente 'View' na arquitetura MVVM do editor (Semana 11).
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferências do Editor")
        self.resize(360, 200)
        
        self.settings = QSettings("Zennity", "Preferences")
        
        # Layout vertical principal
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Painel de formulário
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setContentsMargins(4, 4, 4, 4)
        form_layout.setSpacing(8)
        
        # 1. Configuração de Grid Snap
        self.sb_grid_size = QSpinBox()
        self.sb_grid_size.setRange(4, 128)
        self.sb_grid_size.setSingleStep(4)
        # Lê valor salvo ou aplica 32 como padrão
        self.sb_grid_size.setValue(int(self.settings.value("grid_size", 32)))
        form_layout.addRow("Tamanho da Grade (px):", self.sb_grid_size)
        
        # 2. Grade ligada por padrão
        self.chk_grid_on = QCheckBox("Habilitar Grade na Inicialização")
        self.chk_grid_on.setChecked(
            self.settings.value("grid_on_init", "true") == "true"
        )
        form_layout.addRow("", self.chk_grid_on)
        
        # 3. Salvar Layout automaticamente
        self.chk_auto_layout = QCheckBox("Salvar/Restaurar Layout de Docks")
        self.chk_auto_layout.setChecked(
            self.settings.value("auto_layout", "true") == "true"
        )
        form_layout.addRow("", self.chk_auto_layout)
        
        layout.addWidget(form_widget)
        
        # Botões de confirmação nativos
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self) -> None:
        """Salva as configurações no QSettings ao confirmar."""
        self.settings.setValue("grid_size", self.sb_grid_size.value())
        self.settings.setValue("grid_on_init", "true" if self.chk_grid_on.isChecked() else "false")
        self.settings.setValue("auto_layout", "true" if self.chk_auto_layout.isChecked() else "false")
        
        # Notifica o barramento de eventos sobre a alteração de preferências
        try:
            from editor.core.event_bus import EventBus, EVENT_PROPERTY_CHANGED
            # Notifica que o tamanho da grade mudou
            EventBus.emit(
                EVENT_PROPERTY_CHANGED,
                component_name="Editor",
                property_name="grid_size",
                value=self.sb_grid_size.value()
            )
            # Notifica se a grade está ativa
            EventBus.emit(
                EVENT_PROPERTY_CHANGED,
                component_name="Editor",
                property_name="grid_state",
                value=self.chk_grid_on.isChecked()
            )
        except Exception:
            pass
            
        super().accept()
