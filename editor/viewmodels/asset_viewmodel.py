import os
from PySide6.QtCore import QObject, Signal, Slot
from editor.models.asset_model import AssetModel


class AssetViewModel(QObject):
    """
    ViewModel que controla o estado de navegação do Asset Browser.
    Componente 'ViewModel' na arquitetura MVVM do editor.
    """
    
    current_folder_changed = Signal(str)           # Emite o caminho absoluto do diretório ativo
    navigation_state_changed = Signal(bool, bool)  # Emite (can_go_back, can_go_forward)
    asset_selected = Signal(str)                   # Emite o caminho absoluto do asset selecionado

    def __init__(self, model: AssetModel) -> None:
        super().__init__()
        self._model = model
        
        self._root_path = self._model.get_assets_root_path()
        self._current_path = self._root_path
        
        # Histórico de navegação para botões Voltar/Avançar
        self._back_stack = []
        self._forward_stack = []
        
        self._selected_asset_path = ""

    @property
    def current_path(self) -> str:
        return self._current_path

    @property
    def root_path(self) -> str:
        return self._root_path

    def select_asset(self, path: str) -> None:
        """Seleciona um arquivo e notifica."""
        if os.path.isfile(path):
            self._selected_asset_path = path
            self.asset_selected.emit(path)

    def go_to_folder(self, path: str) -> None:
        """Navega para a pasta especificada e gerencia o histórico."""
        if not os.path.isdir(path):
            return
            
        # Garante que não ultrapasse a raiz de Assets para cima
        if not path.startswith(self._root_path):
            path = self._root_path
            
        if self._current_path != path:
            self._back_stack.append(self._current_path)
            self._forward_stack.clear()
            self._current_path = path
            
            self.current_folder_changed.emit(self._current_path)
            self.navigation_state_changed.emit(self.can_go_back(), self.can_go_forward())

    def go_back(self) -> None:
        """Retorna no histórico de navegação."""
        if self.can_go_back():
            prev = self._back_stack.pop()
            self._forward_stack.append(self._current_path)
            self._current_path = prev
            
            self.current_folder_changed.emit(self._current_path)
            self.navigation_state_changed.emit(self.can_go_back(), self.can_go_forward())

    def go_forward(self) -> None:
        """Avança no histórico de navegação."""
        if self.can_go_forward():
            nxt = self._forward_stack.pop()
            self._back_stack.append(self._current_path)
            self._current_path = nxt
            
            self.current_folder_changed.emit(self._current_path)
            self.navigation_state_changed.emit(self.can_go_back(), self.can_go_forward())

    def can_go_back(self) -> bool:
        return len(self._back_stack) > 0

    def can_go_forward(self) -> bool:
        return len(self._forward_stack) > 0

    def get_parent_directory(self) -> str:
        """Retorna o caminho da pasta pai (se estiver abaixo de Assets)."""
        parent = os.path.dirname(self._current_path)
        if parent.startswith(self._root_path):
            return parent
        return self._root_path
