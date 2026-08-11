from engine.core.provider import EngineProvider
from engine.core.context import EngineContext

class LogicProvider(EngineProvider):
    """Provides Logic Runtime services and syncs metadata."""
    
    def register_services(self, context: EngineContext) -> None:
        pass
        
    def boot(self, context: EngineContext) -> None:
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
        import engine.logic.runtime.nodes.ui_binding_nodes

        from engine.logic.runtime.registry import sync_logic_registry_to_metadata
        from engine.metadata.manager import MetadataManager

        # Actions
        from engine.logic.node_definitions.actions_nodes import (
            PlayAnimationAssetNode,
            PlaySoundNode, SetSpriteNode, StartTextureScrollNode,
            StopTextureScrollNode, SetPositionNode, RotateNode,
            SetActiveNode, DestroyObjectNode, DestroyAfterTimeNode,
            LogMessageNode, StartBehaviorTreeNode
        )

        # Animation
        from engine.logic.node_definitions.animation_nodes import (
            AnimateValueNode, WaitUntilConditionNode,
            # Phase 9.5B Stage 1: canonical home of play/stop animation.  These
            # used to be defined twice, with incompatible port contracts.
            PlayAnimationNode, StopAnimationNode,
        )

        # Audio Advanced
        from engine.logic.node_definitions.audio_advanced_nodes import (
            PlaySoundFadeNode, SetVolumeNode, SetPitchNode, StopAllSoundsNode
        )

        # Camera
        from engine.logic.node_definitions.camera_nodes import (
            CameraShakeNode, CameraFollowNode, CameraStopFollowNode,
            CameraLookAtNode, CameraSetZoomNode
        )

        # Components
        from engine.logic.node_definitions.components_nodes import (
            AddComponentNode, RemoveComponentNode
        )

        # Dialog
        from engine.logic.node_definitions.dialog_nodes import (
            ShowDialogNode, WaitDialogChoiceNode, SetDialogChoiceNode, CloseDialogNode
        )

        # Dynamic UI
        from engine.logic.node_definitions.dynamic_ui_nodes import (
            CreateUILabelNode, CreateUIProgressBarNode, CreateUIButtonNode,
            CreateUIImageNode, DestroyUIWidgetNode, UpdateUIWidgetPropertyNode,
            GetUIWidgetPropertyNode, GetProgressBarValueNode
        )

        # Events
        from engine.logic.node_definitions.event_nodes import (
            CompareNumberNode, CompareTextNode, KeyPressedNode, KeyHeldNode,
            IsGroundedNode, InputAxisNode, ReadKeyAxisNode
        )

        # Flow
        from engine.logic.node_definitions.flow_nodes import (
            IfElseNode, RestartSceneNode, OnceNode, CooldownNode
        )

        # Input Advanced
        from engine.logic.node_definitions.input_advanced_nodes import (
            DetectTouchNode, DetectSwipeNode, DetectPinchNode,
            IsKeyPressedNode, WaitKeyReleaseNode
        )

        # Misc
        from engine.logic.node_definitions.misc_nodes import (
            SetVariableNode, GetVariableNode, CallSubgraphNode,
            SubgraphReturnNode, SequenceNode, SetHudNode, EmitEventNode
        )

        # Movement
        from engine.logic.node_definitions.movement_nodes import (
            MoveNode, MoveByNode, JumpNode, PatrolAxisNode,
            StartContinuousMotionNode, StopContinuousMotionNode,
            UpdateContinuousMotionNode, GetContinuousMotionNode,
            PauseContinuousMotionNode, ResumeContinuousMotionNode
        )

        # Particles
        from engine.logic.node_definitions.particle_nodes import (
            CreateParticleSystemNode, EmitParticlesNode, StopParticlesNode
        )

        # Pathfinding
        from engine.logic.node_definitions.pathfinding_nodes import (
            FindPathNode, FollowPathNode, StopPathNode, DistanceToPointNode
        )

        # Physics
        from engine.logic.node_definitions.physics_nodes import (
            ModifyRigidbodyNode, ModifyColliderNode, ApplyForceNode
        )

        # Prefabs
        from engine.logic.node_definitions.prefab_nodes import (
            CreateObjectNode, CreatePrefabNode, CloneObjectNode
        )

        # Save/Load
        from engine.logic.node_definitions.save_load_nodes import (
            SaveGameNode, LoadGameNode, DeleteSaveNode, HasSaveNode
        )

        # State Machine
        from engine.logic.node_definitions.state_machine_nodes import (
            CreateStateMachineNode, AddTransitionNode, ChangeStateNode,
            GetStateNode, IsInStateNode
        )

        # UI
        from engine.logic.node_definitions.ui_nodes import (
            BindUIToBlackboardNode, SetUIProgressBarNode, SetUITextNode,
            SetUIVisibleNode
        )

        # UI Binding
        from engine.logic.node_definitions.ui_binding_nodes import (
            BindUIToVariableNode_def, UpdateUIBindingNode_def
        )

        # Registra as definições dos nós
        manager = context.services.get_optional(MetadataManager)
        if manager:
            # Actions
            manager.register(PlayAnimationAssetNode.__node_definition__)
            manager.register(PlaySoundNode.__node_definition__)
            manager.register(SetSpriteNode.__node_definition__)
            manager.register(StartTextureScrollNode.__node_definition__)
            manager.register(StopTextureScrollNode.__node_definition__)
            manager.register(SetPositionNode.__node_definition__)
            manager.register(RotateNode.__node_definition__)
            manager.register(SetActiveNode.__node_definition__)
            manager.register(DestroyObjectNode.__node_definition__)
            manager.register(DestroyAfterTimeNode.__node_definition__)
            manager.register(LogMessageNode.__node_definition__)
            manager.register(StartBehaviorTreeNode.__node_definition__)

            # Animation
            manager.register(PlayAnimationNode.__node_definition__)
            manager.register(StopAnimationNode.__node_definition__)
            manager.register(AnimateValueNode.__node_definition__)
            manager.register(WaitUntilConditionNode.__node_definition__)

            # Audio Advanced
            manager.register(PlaySoundFadeNode.__node_definition__)
            manager.register(SetVolumeNode.__node_definition__)
            manager.register(SetPitchNode.__node_definition__)
            manager.register(StopAllSoundsNode.__node_definition__)

            # Camera
            manager.register(CameraShakeNode.__node_definition__)
            manager.register(CameraFollowNode.__node_definition__)
            manager.register(CameraStopFollowNode.__node_definition__)
            manager.register(CameraLookAtNode.__node_definition__)
            manager.register(CameraSetZoomNode.__node_definition__)

            # Components
            manager.register(AddComponentNode.__node_definition__)
            manager.register(RemoveComponentNode.__node_definition__)

            # Dialog
            manager.register(ShowDialogNode.__node_definition__)
            manager.register(WaitDialogChoiceNode.__node_definition__)
            manager.register(SetDialogChoiceNode.__node_definition__)
            manager.register(CloseDialogNode.__node_definition__)

            # Dynamic UI
            manager.register(CreateUILabelNode.__node_definition__)
            manager.register(CreateUIProgressBarNode.__node_definition__)
            manager.register(CreateUIButtonNode.__node_definition__)
            manager.register(CreateUIImageNode.__node_definition__)
            manager.register(DestroyUIWidgetNode.__node_definition__)
            manager.register(UpdateUIWidgetPropertyNode.__node_definition__)
            manager.register(GetUIWidgetPropertyNode.__node_definition__)
            manager.register(GetProgressBarValueNode.__node_definition__)

            # Events
            manager.register(CompareNumberNode.__node_definition__)
            manager.register(CompareTextNode.__node_definition__)
            manager.register(KeyPressedNode.__node_definition__)
            manager.register(KeyHeldNode.__node_definition__)
            manager.register(IsGroundedNode.__node_definition__)
            manager.register(InputAxisNode.__node_definition__)
            manager.register(ReadKeyAxisNode.__node_definition__)

            # Flow
            manager.register(IfElseNode.__node_definition__)
            manager.register(RestartSceneNode.__node_definition__)
            manager.register(OnceNode.__node_definition__)
            manager.register(CooldownNode.__node_definition__)

            # Input Advanced
            manager.register(DetectTouchNode.__node_definition__)
            manager.register(DetectSwipeNode.__node_definition__)
            manager.register(DetectPinchNode.__node_definition__)
            manager.register(IsKeyPressedNode.__node_definition__)
            manager.register(WaitKeyReleaseNode.__node_definition__)

            # Misc
            manager.register(SetVariableNode.__node_definition__)
            manager.register(GetVariableNode.__node_definition__)
            manager.register(CallSubgraphNode.__node_definition__)
            manager.register(SubgraphReturnNode.__node_definition__)
            manager.register(SequenceNode.__node_definition__)
            manager.register(SetHudNode.__node_definition__)
            manager.register(EmitEventNode.__node_definition__)

            # Movement
            manager.register(MoveNode.__node_definition__)
            manager.register(MoveByNode.__node_definition__)
            manager.register(JumpNode.__node_definition__)
            manager.register(PatrolAxisNode.__node_definition__)
            manager.register(StartContinuousMotionNode.__node_definition__)
            manager.register(StopContinuousMotionNode.__node_definition__)
            manager.register(UpdateContinuousMotionNode.__node_definition__)
            manager.register(GetContinuousMotionNode.__node_definition__)
            manager.register(PauseContinuousMotionNode.__node_definition__)
            manager.register(ResumeContinuousMotionNode.__node_definition__)

            # Particles
            manager.register(CreateParticleSystemNode.__node_definition__)
            manager.register(EmitParticlesNode.__node_definition__)
            manager.register(StopParticlesNode.__node_definition__)

            # Pathfinding
            manager.register(FindPathNode.__node_definition__)
            manager.register(FollowPathNode.__node_definition__)
            manager.register(StopPathNode.__node_definition__)
            manager.register(DistanceToPointNode.__node_definition__)

            # Physics
            manager.register(ModifyRigidbodyNode.__node_definition__)
            manager.register(ModifyColliderNode.__node_definition__)
            manager.register(ApplyForceNode.__node_definition__)

            # Prefabs
            manager.register(CreateObjectNode.__node_definition__)
            manager.register(CreatePrefabNode.__node_definition__)
            manager.register(CloneObjectNode.__node_definition__)

            # Save/Load
            manager.register(SaveGameNode.__node_definition__)
            manager.register(LoadGameNode.__node_definition__)
            manager.register(DeleteSaveNode.__node_definition__)
            manager.register(HasSaveNode.__node_definition__)

            # State Machine
            manager.register(CreateStateMachineNode.__node_definition__)
            manager.register(AddTransitionNode.__node_definition__)
            manager.register(ChangeStateNode.__node_definition__)
            manager.register(GetStateNode.__node_definition__)
            manager.register(IsInStateNode.__node_definition__)

            # UI
            manager.register(BindUIToBlackboardNode.__node_definition__)
            manager.register(SetUIProgressBarNode.__node_definition__)
            manager.register(SetUITextNode.__node_definition__)
            manager.register(SetUIVisibleNode.__node_definition__)

            # UI Binding
            try:
                manager.register(BindUIToVariableNode_def)
                print("OK: bind_ui_to_variable registered")
            except Exception as e:
                print(f"ERROR registering bind_ui_to_variable: {e}")
            try:
                manager.register(UpdateUIBindingNode_def)
                print("OK: update_ui_binding registered")
            except Exception as e:
                print(f"ERROR registering update_ui_binding: {e}")

        sync_logic_registry_to_metadata(context)

        # Phase 9.5B Stage 1: never let the editor start on a corrupt catalogue.
        # Duplicate ids raise; contract errors are logged loudly.
        from engine.logic.boot_validation import validate_catalogue_at_boot
        validate_catalogue_at_boot()
