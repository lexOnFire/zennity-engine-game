from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot
from engine.game_object import GameObject
from editor.models.scene_model import SceneModel
from editor.core.event_bus import (
    EventBus, EVENT_SELECTION_CHANGED, EVENT_HIERARCHY_UPDATED, EVENT_PROPERTY_CHANGED
)


class SceneViewModel(QObject):
    """
    ViewModel que expõe a estrutura da cena, gerencia a seleção
    e publica alterações no barramento global de eventos (EventBus).
    Componente 'ViewModel' na arquitetura MVVM do editor.

    Regra de identidade:
        A seleção é comparada por UUID (go.id), nunca por igualdade de instância.
        Painéis externos (Hierarchy, Inspector, Viewport) devem usar selected_id
        e resolver a instância via SceneModel.find_object_by_id() quando necessário.
        Isso evita instâncias duplicadas do mesmo objeto circulando pelos painéis.
    """
    
    # Sinais locais mantidos para compatibilidade com ligações Qt tradicionais
    selection_changed = Signal(object)
    hierarchy_updated = Signal()
    property_changed = Signal(str, str, object)

    def __init__(self, model: SceneModel) -> None:
        super().__init__()
        self._model = model
        self._selected_object: Optional[GameObject] = None
        
        # Conecta sinais do modelo
        self._model.object_structure_changed.connect(self.on_model_hierarchy_changed)

    # ------------------------------------------------------------------ #
    # Seleção — baseada em UUID para evitar instâncias duplicadas         #
    # ------------------------------------------------------------------ #

    @property
    def selected_object(self) -> Optional[GameObject]:
        """Instância canônica atual selecionada no editor."""
        return self._selected_object

    @selected_object.setter
    def selected_object(self, obj: Optional[GameObject]) -> None:
        """
        Define o objeto selecionado comparando por UUID.
        Painéis externos nunca devem armazenar cópias independentes;
        use selected_id + find_object_by_id() para resolver a instância.
        """
        current_id = self._selected_object.id if self._selected_object else None
        new_id     = obj.id if obj else None
        if current_id != new_id:
            self._selected_object = obj
            self.selection_changed.emit(obj)
            EventBus.emit(EVENT_SELECTION_CHANGED, obj=obj)

    @property
    def selected_id(self) -> Optional[str]:
        """
        UUID do objeto atualmente selecionado, ou None.
        Prefira usar este valor em painéis que não precisam da instância completa.
        Para resolver a instância: scene_model.find_object_by_id(selected_id).
        """
        return self._selected_object.id if self._selected_object else None

    @Slot()
    def on_model_hierarchy_changed(self) -> None:
        """Chamado quando a árvore de dados é alterada no modelo."""
        self.hierarchy_updated.emit()
        EventBus.emit(EVENT_HIERARCHY_UPDATED)

    def get_root_objects(self):
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
        go.transform.scale    = np.array([40.0, 40.0, 1.0], dtype=np.float32) if shape_type != "Plataforma" else np.array([120.0, 24.0, 1.0], dtype=np.float32)
        go.transform.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        
        if shape_type == "Quadrado":
            go.add_component(BoxCollider(width=40, height=40))
            go.add_component(RigidBody(mass=1.0))
        elif shape_type == "Círculo":
            go.add_component(CircleCollider(radius=20))
            go.add_component(RigidBody(mass=1.0))
        elif shape_type == "Plataforma":
            go.add_component(BoxCollider(width=120, height=24))
            rb = go.add_component(RigidBody())
            rb.is_kinematic = True
        elif shape_type == "Player":
            go.transform.scale = np.array([36.0, 48.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=36, height=48))
            go.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        elif shape_type == "Inimigo":
            go.transform.scale = np.array([36.0, 36.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=36, height=36))
            go.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        elif shape_type == "Trigger":
            go.transform.scale = np.array([80.0, 80.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=80, height=80, is_trigger=True))
        elif shape_type == "Mola":
            go.transform.scale = np.array([40.0, 20.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=40, height=20))
            rb = go.add_component(RigidBody())
            rb.is_kinematic = True
            
        self._model.add_object(go)
        self.selected_object = go

    @Slot()
    def delete_selected(self) -> None:
        if self._selected_object:
            obj_to_remove = self._selected_object
            self.selected_object = None
            self._model.remove_object(obj_to_remove)

    @Slot()
    def duplicate_selected(self) -> None:
        if not self._selected_object:
            return
            
        src = self._selected_object
        name = f"{src.name}_cópia"
        go = GameObject(name)
        go.mesh_type = src.mesh_type
        
        go.transform.position = src.transform.position.copy()
        go.transform.position[0] += 50.0
        go.transform.position[1] += 50.0
        go.transform.scale    = src.transform.scale.copy()
        go.transform.rotation = src.transform.rotation.copy()
        
        for comp in src.components:
            from engine.component import Transform
            if isinstance(comp, Transform):
                continue
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
        if obj and new_name.strip():
            obj.name = new_name.strip()
            self.on_model_hierarchy_changed()

    # ── Métodos de Atualização de Propriedades ─────────────────────────────────

    def set_transform_property(self, prop_name: str, index: int, value: float) -> None:
        if not self._selected_object:
            return
            
        transform = self._selected_object.transform
        if prop_name == "position":
            transform.position[index] = value
        elif prop_name == "scale":
            transform.scale[index] = value
            self._sync_collider_dimensions(self._selected_object)
        elif prop_name == "rotation":
            transform.rotation[index] = value
            
        prop_id = f"{prop_name}_{index}"
        self.property_changed.emit("Transform", prop_id, value)
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Transform", property_name=prop_id, value=value)

    def set_rigidbody_property(self, prop_name: str, value) -> None:
        if not self._selected_object:
            return
            
        from engine.physics.rigidbody import RigidBody
        rb = self._selected_object.get_component(RigidBody)
        if not rb:
            return
            
        if prop_name == "mass":
            rb.mass = float(value)
        elif prop_name == "gravity_scale":
            rb.gravity_scale = float(value)
        elif prop_name == "is_kinematic":
            rb.is_kinematic = bool(value)
            
        self.property_changed.emit("RigidBody", prop_name, value)
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="RigidBody", property_name=prop_name, value=value)

    def set_collider_property(self, prop_name: str, value) -> None:
        if not self._selected_object:
            return
            
        from engine.physics.collider import BoxCollider, CircleCollider
        bc = self._selected_object.get_component(BoxCollider)
        cc = self._selected_object.get_component(CircleCollider)
        
        if bc:
            if prop_name == "width":
                bc.width = int(value)
                self._selected_object.transform.scale[0] = float(value)
            elif prop_name == "height":
                bc.height = int(value)
                self._selected_object.transform.scale[1] = float(value)
            elif prop_name == "is_trigger":
                bc.is_trigger = bool(value)
        elif cc:
            if prop_name == "radius":
                cc.radius = int(value)
                self._selected_object.transform.scale[0] = float(value * 2)
                self._selected_object.transform.scale[1] = float(value * 2)
            elif prop_name == "is_trigger":
                cc.is_trigger = bool(value)
                
        self.property_changed.emit("Collider", prop_name, value)
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Collider", property_name=prop_name, value=value)
        
        self.property_changed.emit("Transform", "scale", None)
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Transform", property_name="scale", value=None)

    def _sync_collider_dimensions(self, obj: GameObject) -> None:
        from engine.physics.collider import BoxCollider, CircleCollider
        scale = obj.transform.scale
        bc = obj.get_component(BoxCollider)
        cc = obj.get_component(CircleCollider)
        
        if bc:
            bc.width  = max(1, int(scale[0]))
            bc.height = max(1, int(scale[1]))
        elif cc:
            cc.radius = max(1, int(scale[0] / 2))
