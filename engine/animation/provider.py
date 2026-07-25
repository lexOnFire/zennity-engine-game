from engine.core.provider import EngineProvider
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.animation import (
    AnimationClipDefinition,
    AnimatorDefinition,
    TrackDefinition,
    CurveDefinition,
    BlendTreeDefinition,
    AnimationEventDefinition,
)
from engine.animation.tracks import (
    TransformTrack,
    SpriteTrack,
    AudioTrack,
    EventTrack,
    PropertyTrack,
)


from engine.animation.animation_player_service import AnimationPlayerService


class AnimationProvider(EngineProvider):
    """Provedor oficial de metadados da Plataforma de Animação e Track Framework."""

    def register_services(self, context: EngineContext) -> None:
        service = AnimationPlayerService()
        context.services.register(AnimationPlayerService, service)

    def boot(self, context: EngineContext) -> None:
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return

        # 1. Definições de Assets de Animação
        manager.register(AnimationClipDefinition(
            id="animation_clip", title_key="asset.animation", extensions=[".zanim"]
        ))
        manager.register(AnimatorDefinition(
            id="animator_controller", title_key="asset.animator", extensions=[".zanimator"]
        ))

        # 2. Definições de Trilhas do Track Framework
        manager.register(TrackDefinition(
            id="transform_track",
            title_key="track.transform",
            track_class=TransformTrack,
            color="#4A90E2",
            icon="📐 "
        ))
        manager.register(TrackDefinition(
            id="sprite_track",
            title_key="track.sprite",
            track_class=SpriteTrack,
            color="#50E3C2",
            icon="🖼️ "
        ))
        manager.register(TrackDefinition(
            id="audio_track",
            title_key="track.audio",
            track_class=AudioTrack,
            color="#F5A623",
            icon="🔊 "
        ))
        manager.register(TrackDefinition(
            id="event_track",
            title_key="track.event",
            track_class=EventTrack,
            color="#D0021B",
            icon="⚡ "
        ))
        manager.register(TrackDefinition(
            id="property_track",
            title_key="track.property",
            track_class=PropertyTrack,
            color="#BD10E0",
            icon="⚙️ "
        ))

        # 3. Definições de Curvas e Blending
        manager.register(CurveDefinition(id="hermite_curve", curve_type="hermite"))
        manager.register(BlendTreeDefinition(id="blend_tree_1d", blend_type="1D"))
        manager.register(AnimationEventDefinition(id="generic_event", event_type="generic"))

        # 4. Registro de Nós do Graph Framework para Animator Controllers
        from engine.animation.graph_nodes import (
            AnimationStateNode,
            AnimatorParameterNode,
            BlendTree1DNode,
        )
        manager.register(AnimationStateNode.__node_definition__)
        manager.register(AnimatorParameterNode.__node_definition__)
        manager.register(BlendTree1DNode.__node_definition__)
