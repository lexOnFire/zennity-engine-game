from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from engine.game_object import GameObject
from editor.models.scene_model import SceneModel


class SceneViewModel(QObject):
    """
    ViewModel que expõe a estrutura da cena e gerencia o estado da seleção.
    Componente 'ViewModel' na arquitetura MVVM do editor.
    """
    
    # Sinais para comunicação com a View (Widgets)
    selection_changed = Signal(object)  # Emite o GameObject selecionado (ou None)
    hierarchy_updated = Signal()        # Notifica que a hierarquia precisa ser redesenhada

    def __init__(self, model: SceneModel) -> None:
        super().__init__()
        self._model = model
        self._selected_object: Optional[GameObject] = None
        
        # Conecta sinais do modelo
        self._model.object_structure_changed.connect(self.hierarchy_updated.emit)

    @property
    def selected_object(self) -> Optional[GameObject]:
        return self._selected_object

    @selected_object.setter
    def selected_object(self, obj: Optional[GameObject]) -> None:
        if self._selected_object != obj:
            self._selected_object = obj
            self.selection_changed.emit(obj)

    def get_root_objects(self):
        """Repassa a lista de objetos raiz do modelo."""
        return self._model.get_root_objects()

    @Slot(str)
    def create_object(self, shape_type: str) -> None:
        """Cria e adiciona um novo objeto com componentes padrão na cena."""
        import numpy as np
        from engine.physics.rigidbody import RigidBody
        from engine.physics.collider import BoxCollider, CircleCollider
        
        name = f"{shape_type}_{len(self._model.get_root_objects())}"
        go = GameObject(name)
        go.mesh_type = shape_type
        
        # Componentes padrão básicos
        go.transform.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        go.transform.scale    = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        
        if shape_type == "Quadrado":
            go.add_component(BoxCollider(width=1, height=1))
            go.add_component(RigidBody(mass=1.0))
        elif shape_type == "Círculo":
            go.add_component(CircleCollider(radius=1))
            go.add_component(RigidBody(mass=1.0))
        elif shape_type == "Plataforma":
            go.add_component(BoxCollider(width=3, height=1))
            rb = go.add_component(RigidBody())
            rb.is_kinematic = True
            
        self._model.add_object(go)
        self.selected_object = go  # Seleciona o novo objeto automaticamente

    @Slot()
    def delete_selected(self) -> None:
        """Exclui o objeto atualmente selecionado."""
        if self._selected_object:
            obj_to_remove = self._selected_object
            self.selected_object = None  # Limpa a seleção
            self._model.remove_object(obj_to_remove)

    @Slot()
    def duplicate_selected(self) -> None:
        """Duplica o objeto selecionado."""
        if not self._selected_object:
            return
            
        src = self._selected_object
        name = f"{src.name}_cópia"
        go = GameObject(name)
        go.mesh_type = src.mesh_type
        
        # Clona dados do Transform com pequeno offset
        go.transform.position = src.transform.position.copy()
        go.transform.position[0] += 0.5
        go.transform.position[1] += 0.5
        go.transform.scale    = src.transform.scale.copy()
        go.transform.rotation = src.transform.rotation.copy()
        
        # Clona componentes básicos
        for comp in src.components:
            # Evita duplicar o Transform que já é criado por padrão no GameObject
            from engine.component import Transform
            if isinstance(comp, Transform):
                continue
            # Clona de forma simples dependendo do tipo
            from engine.physics.rigidbody import RigidBody
            from engine.physics.collider import BoxCollider, CircleCollider
            if isinstance(comp, BoxCollider):
                go.add_component(BoxCollider(width=comp.width, height=comp.height, is_trigger=comp.is_trigger))
            elif isinstance(comp, CircleCollider):
                go.add_component(CircleCollider(radius=comp.radius, is_trigger=comp.is_trigger))
            elif isinstance(comp, RigidBody):
                go.add_component(RigidBody(mass=comp.mass, gravity_scale=comp.gravity_scale))
                
        self._model.add_object(go)
        self.selected_object = go

    def rename_object(self, obj: GameObject, new_name: str) -> None:
        """Renomeia um objeto da cena."""
        if obj and new_name.strip():
            obj.name = new_name.strip()
            self.hierarchy_updated.emit()
