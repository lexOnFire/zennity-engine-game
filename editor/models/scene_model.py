from typing import List, Optional
from PySide6.QtCore import QObject, Signal
from engine.game_object import GameObject


class SceneModel(QObject):
    """
    Modelo de dados que gerencia a coleção de GameObjects da cena ativa.
    Componente 'Model' na arquitetura MVVM do editor.
    """
    
    # Sinais para notificar o ViewModel sobre mudanças na estrutura da cena
    object_added = Signal(GameObject)
    object_removed = Signal(GameObject)
    object_structure_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._root_objects: List[GameObject] = []

    def get_root_objects(self) -> List[GameObject]:
        """Retorna os objetos raiz da cena."""
        return self._root_objects

    def add_object(self, obj: GameObject, parent: Optional[GameObject] = None) -> None:
        """Adiciona um GameObject à cena."""
        if parent:
            parent.add_child(obj)
        else:
            self._root_objects.append(obj)
            
        self.object_added.emit(obj)
        self.object_structure_changed.emit()

    def remove_object(self, obj: GameObject) -> None:
        """Remove um GameObject da cena."""
        if obj.parent:
            obj.parent.remove_child(obj)
        else:
            if obj in self._root_objects:
                self._root_objects.remove(obj)
                
        self.object_removed.emit(obj)
        self.object_structure_changed.emit()

    def clear(self) -> None:
        """Limpa toda a cena."""
        self._root_objects.clear()
        self.object_structure_changed.emit()

    # ------------------------------------------------------------------ #
    # Busca por identidade (UUID)                                         #
    # ------------------------------------------------------------------ #

    def find_object_by_id(self, object_id: str) -> Optional[GameObject]:
        """
        Localiza um GameObject pelo seu UUID único.
        Percorre raízes e filhos recursivamente.
        Retorna None se não encontrado.
        """
        for obj in self._root_objects:
            found = self._find_recursive(obj, object_id)
            if found is not None:
                return found
        return None

    def _find_recursive(self, obj: GameObject, object_id: str) -> Optional[GameObject]:
        """Percurso recursivo em profundidade para localizar objeto pelo ID."""
        if obj.id == object_id:
            return obj
        for child in obj.children:
            found = self._find_recursive(child, object_id)
            if found is not None:
                return found
        return None
