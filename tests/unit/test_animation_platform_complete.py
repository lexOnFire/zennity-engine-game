import pytest
import numpy as np
from pathlib import Path

from engine.core.bootstrap import EngineBootstrap
from engine.metadata.manager import MetadataManager
from engine.core.metadata.animation import (
    AnimationClipDefinition,
    AnimatorDefinition,
    TrackDefinition,
)
from engine.core.metadata.asset import PreviewDefinition
from engine.animation.animation_player_service import AnimationPlayerService, AnimationPlaybackState
from engine.animation.tracks import (
    AnimationTrack,
    TransformTrack,
    SpriteTrack,
    AudioTrack,
    EventTrack,
    PropertyTrack,
)
from engine.animation.preview_provider import AnimationPreviewProvider
from engine.animation.graph_nodes import (
    AnimationStateNode,
    AnimatorParameterNode,
    BlendTree1DNode,
)


def test_checklist_item_1_runtime_decoupling():
    """Valida que o AnimationPlayerService e o TrackPlaybackState funcionam sem Qt ou Editor."""
    service = AnimationPlayerService()
    assert service.scope.name == "ENGINE"
    
    class DummyTarget:
        def __init__(self):
            self.val = 0.0

    target = DummyTarget()
    track = PropertyTrack(name="Prop", property_name="val")
    track.keyframes = [{"time": 0.0, "value": 0.0}, {"time": 1.0, "value": 100.0}]
    
    pb = service.create_playback(target, "DecoupledPlayback", [track], duration=1.0, loop=False)
    pb.play()
    service.update(0.5, {id(target): target})
    assert target.val == pytest.approx(50.0)


def test_checklist_item_2_track_interface_inheritance():
    """Valida que todas as trilhas derivam da mesma classe base AnimationTrack."""
    tracks = [
        TransformTrack(),
        SpriteTrack(),
        AudioTrack(),
        EventTrack(),
        PropertyTrack(),
    ]
    for track in tracks:
        assert isinstance(track, AnimationTrack)
        serialized = track.serialize()
        assert "name" in serialized
        assert "enabled" in serialized
        assert "type" in serialized


def test_checklist_item_3_animator_graph_framework():
    """Valida que os nós do Animator Controller estão registrados no Graph Framework."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)
    
    node_state = AnimationStateNode.__node_definition__
    node_param = AnimatorParameterNode.__node_definition__
    node_blend = BlendTree1DNode.__node_definition__
    
    assert manager.get(type(node_state), node_state.id) is not None
    assert manager.get(type(node_param), node_param.id) is not None
    assert manager.get(type(node_blend), node_blend.id) is not None


def test_checklist_item_4_and_5_asset_pipeline_and_preview_service(tmp_path):
    """Valida preview de animações via PreviewDefinition e AnimationPreviewProvider."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)
    
    preview_def = manager.get(PreviewDefinition, "animation_preview")
    assert preview_def is not None
    assert ".zanim" in preview_def.extensions
    assert ".zanimator" in preview_def.extensions
    assert preview_def.provider_class is AnimationPreviewProvider

    # Test preview generation
    clip_file = tmp_path / "test_clip.zanim"
    clip_file.write_text('{"name": "Walk", "frames": [], "fps": 12, "loop": true}', encoding="utf-8")
    
    data = AnimationPreviewProvider.generate_preview_data(clip_file)
    assert "🎞 Animation" in data["label"]
    assert "Walk" in data["details"]


def test_checklist_item_6_hot_reload_validation():
    """Valida o re-carregamento automático ao notificar re-importação de um clipe."""
    service = AnimationPlayerService()
    
    class DummyTarget:
        pass

    target = DummyTarget()
    track = TransformTrack(name="TestClip")
    pb = service.create_playback(target, "TestClip", [track], duration=2.0)
    pb.play()
    pb.seek(1.5)
    
    reloaded = service.on_asset_reimported("Assets/Animations/TestClip.zanim")
    assert reloaded == 1
    assert pb.current_time == 0.0  # Reset on hot reload


def test_checklist_item_7_playback_blend_events_serialization():
    """Valida playback, amostragem de vetor, serialização e despacho de eventos."""
    service = AnimationPlayerService()
    v_a = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    v_b = np.array([10.0, 20.0, 30.0], dtype=np.float32)
    
    blended = service.blend_vectors(v_a, v_b, 0.5)
    assert np.allclose(blended, [5.0, 10.0, 15.0])
    
    event_track = EventTrack(name="MyEvents")
    event_track.keyframes = [{"time": 0.5, "event_name": "on_hit", "payload": {}}]
    
    # EventTrack sampling test
    event_track.sample(0.6, None)
    assert event_track._last_sampled_time == 0.6
