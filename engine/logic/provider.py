from engine.core.provider import EngineProvider
from engine.core.context import EngineContext

class LogicProvider(EngineProvider):
    """Provides Logic Runtime services and syncs metadata."""
    
    def register_services(self, context: EngineContext) -> None:
        pass
        
    def boot(self, context: EngineContext) -> None:
        print("LogicProvider.boot EXECUTADO!")
        # Força o carregamento dos decorators
        import engine.logic.runtime.nodes.actions_nodes
        import engine.logic.runtime.nodes.components_nodes
        import engine.logic.runtime.nodes.event_nodes
        import engine.logic.runtime.nodes.flow_nodes
        import engine.logic.runtime.nodes.math_nodes
        import engine.logic.runtime.nodes.misc_nodes
        import engine.logic.runtime.nodes.movement_nodes
        import engine.logic.runtime.nodes.prefab_nodes
        import engine.logic.runtime.nodes.scene_nodes
        import engine.logic.runtime.nodes.string_nodes
        import engine.logic.runtime.nodes.dynamic_ui_nodes
        import engine.logic.runtime.nodes.animation_nodes
        import engine.logic.runtime.nodes.physics_nodes
        import engine.logic.runtime.nodes.dialog_nodes
        import engine.logic.runtime.nodes.audio_advanced_nodes
        import engine.logic.runtime.nodes.particle_nodes
        import engine.logic.runtime.nodes.camera_nodes
        import engine.logic.runtime.nodes.state_machine_nodes
        import engine.logic.runtime.nodes.save_load_nodes
        import engine.logic.runtime.nodes.pathfinding_nodes
        import engine.logic.runtime.nodes.input_advanced_nodes

        from engine.logic.runtime.registry import sync_logic_registry_to_metadata
        from engine.metadata.manager import MetadataManager
        from engine.logic.node_definitions.dynamic_ui_nodes import (
            CreateUILabelNode, CreateUIProgressBarNode, CreateUIButtonNode,
            CreateUIImageNode, DestroyUIWidgetNode, UpdateUIWidgetPropertyNode,
            GetUIWidgetPropertyNode
        )
        from engine.logic.node_definitions.animation_nodes import (
            AnimateValueNode, WaitUntilConditionNode
        )
        from engine.logic.node_definitions.physics_nodes import (
            ModifyRigidbodyNode, ModifyColliderNode, ApplyForceNode
        )
        from engine.logic.node_definitions.dialog_nodes import (
            ShowDialogNode, WaitDialogChoiceNode, SetDialogChoiceNode, CloseDialogNode
        )
        from engine.logic.node_definitions.audio_advanced_nodes import (
            PlaySoundFadeNode, SetVolumeNode, SetPitchNode, StopAllSoundsNode
        )
        from engine.logic.node_definitions.particle_nodes import (
            CreateParticleSystemNode, EmitParticlesNode, StopParticlesNode
        )
        from engine.logic.node_definitions.camera_nodes import (
            CameraShakeNode, CameraFollowNode, CameraStopFollowNode,
            CameraLookAtNode, CameraSetZoomNode
        )
        from engine.logic.node_definitions.state_machine_nodes import (
            CreateStateMachineNode, AddTransitionNode, ChangeStateNode,
            GetStateNode, IsInStateNode
        )
        from engine.logic.node_definitions.save_load_nodes import (
            SaveGameNode, LoadGameNode, DeleteSaveNode, HasSaveNode
        )
        from engine.logic.node_definitions.pathfinding_nodes import (
            FindPathNode, FollowPathNode, StopPathNode, DistanceToPointNode
        )
        from engine.logic.node_definitions.input_advanced_nodes import (
            DetectTouchNode, DetectSwipeNode, DetectPinchNode,
            IsKeyPressedNode, WaitKeyReleaseNode
        )

        # Registra as definições dos nós
        manager = context.services.get_optional(MetadataManager)
        if manager:
            # UI Dinâmica
            manager.register(CreateUILabelNode.__node_definition__)
            manager.register(CreateUIProgressBarNode.__node_definition__)
            manager.register(CreateUIButtonNode.__node_definition__)
            manager.register(CreateUIImageNode.__node_definition__)
            manager.register(DestroyUIWidgetNode.__node_definition__)
            manager.register(UpdateUIWidgetPropertyNode.__node_definition__)
            manager.register(GetUIWidgetPropertyNode.__node_definition__)

            # Animação
            manager.register(AnimateValueNode.__node_definition__)
            manager.register(WaitUntilConditionNode.__node_definition__)

            # Física
            manager.register(ModifyRigidbodyNode.__node_definition__)
            manager.register(ModifyColliderNode.__node_definition__)
            manager.register(ApplyForceNode.__node_definition__)

            # Diálogo
            manager.register(ShowDialogNode.__node_definition__)
            manager.register(WaitDialogChoiceNode.__node_definition__)
            manager.register(SetDialogChoiceNode.__node_definition__)
            manager.register(CloseDialogNode.__node_definition__)

            # Audio Avançado
            manager.register(PlaySoundFadeNode.__node_definition__)
            manager.register(SetVolumeNode.__node_definition__)
            manager.register(SetPitchNode.__node_definition__)
            manager.register(StopAllSoundsNode.__node_definition__)

            # Partículas
            manager.register(CreateParticleSystemNode.__node_definition__)
            manager.register(EmitParticlesNode.__node_definition__)
            manager.register(StopParticlesNode.__node_definition__)

            # Câmera Avançada
            manager.register(CameraShakeNode.__node_definition__)
            manager.register(CameraFollowNode.__node_definition__)
            manager.register(CameraStopFollowNode.__node_definition__)
            manager.register(CameraLookAtNode.__node_definition__)
            manager.register(CameraSetZoomNode.__node_definition__)

            # State Machine
            manager.register(CreateStateMachineNode.__node_definition__)
            manager.register(AddTransitionNode.__node_definition__)
            manager.register(ChangeStateNode.__node_definition__)
            manager.register(GetStateNode.__node_definition__)
            manager.register(IsInStateNode.__node_definition__)

            # Save/Load
            manager.register(SaveGameNode.__node_definition__)
            manager.register(LoadGameNode.__node_definition__)
            manager.register(DeleteSaveNode.__node_definition__)
            manager.register(HasSaveNode.__node_definition__)

            # Pathfinding
            manager.register(FindPathNode.__node_definition__)
            manager.register(FollowPathNode.__node_definition__)
            manager.register(StopPathNode.__node_definition__)
            manager.register(DistanceToPointNode.__node_definition__)

            # Input Avançado
            manager.register(DetectTouchNode.__node_definition__)
            manager.register(DetectSwipeNode.__node_definition__)
            manager.register(DetectPinchNode.__node_definition__)
            manager.register(IsKeyPressedNode.__node_definition__)
            manager.register(WaitKeyReleaseNode.__node_definition__)

        sync_logic_registry_to_metadata(context)
