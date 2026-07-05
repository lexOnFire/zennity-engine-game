from typing import Optional, Any
from PySide6.QtCore import QObject, Signal, Slot
from engine.game_object import GameObject
from editor.models.scene_model import SceneModel
from editor.core.event_bus import (
    EventBus, EVENT_SELECTION_CHANGED, EVENT_HIERARCHY_UPDATED, EVENT_PROPERTY_CHANGED
)
from editor.runtime.selection_manager import SelectionManager


class SceneViewModel(QObject):
    """
    ViewModel que expõe a estrutura da cena, gerencia a seleção
    e publica alterações no barramento global de eventos (EventBus).
    Componente 'ViewModel' na arquitetura MVVM do editor.
    """
    
    # Sinais locais mantidos para compatibilidade com ligações Qt tradicionais
    selection_changed = Signal(object)
    hierarchy_updated = Signal()
    property_changed = Signal(str, str, object)

    def __init__(
        self,
        model: SceneModel,
        selection_manager: Optional[SelectionManager] = None,
        command_manager: Optional[Any] = None
    ) -> None:
        super().__init__()
        self._model = model
        self.selection_manager = selection_manager or SelectionManager()
        self.command_manager = command_manager
        self._selected_object: Optional[GameObject] = None
        
        # Conecta sinais do modelo
        self._model.object_structure_changed.connect(self.on_model_hierarchy_changed)
        self.selection_manager.subscribe(self._on_runtime_selection_changed)

    @property
    def selected_object(self) -> Optional[GameObject]:
        return self.selection_manager.selected

    @selected_object.setter
    def selected_object(self, obj: Optional[GameObject]) -> None:
        self.selection_manager.set_selected(obj)

    def _on_runtime_selection_changed(self, obj: Optional[GameObject]) -> None:
        if self._selected_object is obj:
            return
        self._selected_object = obj
        self.selection_changed.emit(obj)
        EventBus.emit(EVENT_SELECTION_CHANGED, obj=obj)

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
        selected = self.selected_object
        if selected:
            obj_to_remove = selected
            self.selected_object = None
            self._model.remove_object(obj_to_remove)

    @Slot()
    def duplicate_selected(self) -> None:
        src = self.selected_object
        if not src:
            return

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
        selected = self.selected_object
        if not selected:
            return
            
        transform = selected.transform
        if prop_name == "position":
            transform.position[index] = value
        elif prop_name == "scale":
            transform.scale[index] = value
            self._sync_collider_dimensions(selected)
        elif prop_name == "rotation":
            transform.rotation[index] = value
            
        # Emite sinal local e publica no EventBus
        prop_id = f"{prop_name}_{index}"
        self.property_changed.emit("Transform", prop_id, value)
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Transform", property_name=prop_id, value=value)

    def commit_transform_property(self, prop_name: str, index: int, old_value: float, new_value: float) -> None:
        selected = self.selected_object
        if not selected:
            return
        if old_value == new_value:
            return

        from editor.runtime.property_commands import SetTransformPropertyCommand

        # Callback para atualizar a propriedade e acionar as notificações MVVM/EventBus
        def update_fn(val: float) -> None:
            self.set_transform_property(prop_name, index, val)

        cmd = SetTransformPropertyCommand(
            target_transform=selected.transform,
            prop_name=prop_name,
            index=index,
            old_value=old_value,
            new_value=new_value,
            on_changed=update_fn
        )

        if getattr(self, "command_manager", None) is not None:
            self.command_manager.execute(cmd)

    def set_rigidbody_property(self, prop_name: str, value) -> None:
        selected = self.selected_object
        if not selected:
            return
            
        from engine.physics.rigidbody import RigidBody
        rb = selected.get_component(RigidBody)
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
        selected = self.selected_object
        if not selected:
            return
            
        from engine.physics.collider import BoxCollider, CircleCollider
        bc = selected.get_component(BoxCollider)
        cc = selected.get_component(CircleCollider)
        
        if bc:
            if prop_name == "width":
                bc.width = int(value)
                selected.transform.scale[0] = float(value)
            elif prop_name == "height":
                bc.height = int(value)
                selected.transform.scale[1] = float(value)
            elif prop_name == "is_trigger":
                bc.is_trigger = bool(value)
        elif cc:
            if prop_name == "radius":
                cc.radius = int(value)
                selected.transform.scale[0] = float(value * 2)
                selected.transform.scale[1] = float(value * 2)
            elif prop_name == "is_trigger":
                cc.is_trigger = bool(value)
                
        self.property_changed.emit("Collider", prop_name, value)
        EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Collider", property_name=prop_name, value=value)
        
        # Emite sinal extra para atualizar escala
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

    def commit_rigidbody_property(self, prop_name: str, old_value: Any, new_value: Any) -> None:
        selected = self.selected_object
        if not selected:
            return
        if old_value == new_value:
            return
            
        from engine.physics.rigidbody import RigidBody
        rb = selected.get_component(RigidBody)
        if not rb:
            return

        from editor.runtime.property_commands import SetPropertyCommand

        # Callback para disparar notificações MVVM ao executar/desfazer
        def update_fn(val: Any) -> None:
            if prop_name in ("mass", "gravity_scale"):
                val = float(val)
            elif prop_name == "is_kinematic":
                val = bool(val)
            setattr(rb, prop_name, val)
            self.property_changed.emit("RigidBody", prop_name, val)
            EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="RigidBody", property_name=prop_name, value=val)

        cmd = SetPropertyCommand(
            target=rb,
            property_name=prop_name,
            old_value=old_value,
            new_value=new_value,
            on_changed=update_fn
        )

        if getattr(self, "command_manager", None) is not None:
            self.command_manager.execute(cmd)

    def commit_collider_property(self, prop_name: str, old_value: Any, new_value: Any) -> None:
        selected = self.selected_object
        if not selected:
            return
        if old_value == new_value:
            return

        from engine.physics.collider import BoxCollider, CircleCollider
        bc = selected.get_component(BoxCollider)
        cc = selected.get_component(CircleCollider)
        col = bc if bc else cc
        if not col:
            return

        from editor.runtime.property_commands import SetPropertyCommand

        def update_fn(val: Any) -> None:
            if prop_name in ("width", "height", "radius"):
                val = int(val)
            elif prop_name == "is_trigger":
                val = bool(val)
            setattr(col, prop_name, val)

            # Lógica de sincronização com o Transform do GameObject
            if bc:
                if prop_name == "width":
                    selected.transform.scale[0] = float(val)
                elif prop_name == "height":
                    selected.transform.scale[1] = float(val)
            elif cc:
                if prop_name == "radius":
                    selected.transform.scale[0] = float(val * 2)
                    selected.transform.scale[1] = float(val * 2)

            self.property_changed.emit("Collider", prop_name, val)
            EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Collider", property_name=prop_name, value=val)
            
            # Sincroniza escala do Transform correspondente
            self.property_changed.emit("Transform", "scale", None)
            EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Transform", property_name="scale", value=None)

        cmd = SetPropertyCommand(
            target=col,
            property_name=prop_name,
            old_value=old_value,
            new_value=new_value,
            on_changed=update_fn
        )

        if getattr(self, "command_manager", None) is not None:
            self.command_manager.execute(cmd)

    def commit_script_property(self, old_value: str, new_value: str) -> None:
        selected = self.selected_object
        if not selected:
            return
        if old_value == new_value:
            return

        from editor.runtime.property_commands import SetPropertyCommand

        def update_fn(val: str) -> None:
            selected.script_path = val
            self.property_changed.emit("Script", "script_path", val)
            EventBus.emit(EVENT_PROPERTY_CHANGED, component_name="Script", property_name="script_path", value=val)

        cmd = SetPropertyCommand(
            target=selected,
            property_name="script_path",
            old_value=old_value,
            new_value=new_value,
            on_changed=update_fn
        )

        if getattr(self, "command_manager", None) is not None:
            self.command_manager.execute(cmd)
