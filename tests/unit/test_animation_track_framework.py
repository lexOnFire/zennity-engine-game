import pytest
import numpy as np
from engine.core.bootstrap import EngineBootstrap
from engine.metadata.manager import MetadataManager
from engine.core.metadata.animation import (
    AnimationClipDefinition,
    AnimatorDefinition,
    TrackDefinition,
)
from engine.animation.tracks import (
    TransformTrack,
    SpriteTrack,
    AudioTrack,
    EventTrack,
    PropertyTrack,
)


def test_animation_provider_boots_metadata():
    context = EngineBootstrap.boot()
    meta_manager = context.services.get(MetadataManager)
    
    clip_def = meta_manager.get(AnimationClipDefinition, "animation_clip")
    assert clip_def is not None
    assert ".zanim" in clip_def.extensions
    
    animator_def = meta_manager.get(AnimatorDefinition, "animator_controller")
    assert animator_def is not None
    assert ".zanimator" in animator_def.extensions
    
    tracks = meta_manager.get_all(TrackDefinition)
    assert len(tracks) >= 5
    track_ids = {t.id for t in tracks}
    assert "transform_track" in track_ids
    assert "sprite_track" in track_ids
    assert "audio_track" in track_ids
    assert "event_track" in track_ids
    assert "property_track" in track_ids


def test_transform_track_sampling():
    track = TransformTrack(name="MoveTrack")
    track.position_keyframes = [
        {"time": 0.0, "value": [0.0, 0.0, 0.0]},
        {"time": 1.0, "value": [10.0, 20.0, 0.0]},
    ]
    
    class DummyTarget:
        class DummyTransform:
            def __init__(self):
                self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                self.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                self.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        def __init__(self):
            self.transform = self.DummyTransform()

    target = DummyTarget()
    
    # Sample t = 0.5 (midpoint)
    track.sample(0.5, target)
    assert target.transform.position[0] == pytest.approx(5.0)
    assert target.transform.position[1] == pytest.approx(10.0)
    
    # Serialization
    serialized = track.serialize()
    assert serialized["name"] == "MoveTrack"
    
    new_track = TransformTrack()
    new_track.deserialize(serialized)
    assert len(new_track.position_keyframes) == 2


def test_property_track_sampling():
    track = PropertyTrack(name="OpacityTrack", property_name="opacity")
    track.keyframes = [
        {"time": 0.0, "value": 0.0},
        {"time": 2.0, "value": 1.0},
    ]

    class DummyComponent:
        def __init__(self):
            self.opacity = 0.0

    target = DummyComponent()
    track.sample(1.0, target)  # t = 1.0 midpoint
    assert target.opacity == pytest.approx(0.5)
