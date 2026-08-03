import pytest
import numpy as np
from engine.animation.animation_player_service import AnimationPlayerService, AnimationPlaybackState
from engine.animation.tracks import TransformTrack


def test_animation_player_service_playback():
    service = AnimationPlayerService()
    
    class DummyTarget:
        class DummyTransform:
            def __init__(self):
                self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                self.rotation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
                self.scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
        def __init__(self):
            self.transform = self.DummyTransform()

    target = DummyTarget()
    
    track = TransformTrack(name="Move")
    track.position_keyframes = [
        {"time": 0.0, "value": [0.0, 0.0, 0.0]},
        {"time": 2.0, "value": [20.0, 0.0, 0.0]},
    ]
    
    pb = service.create_playback(target, "MoveAnim", [track], duration=2.0, loop=False)
    assert pb.state == AnimationPlaybackState.STOPPED
    
    pb.play()
    assert pb.state == AnimationPlaybackState.PLAYING
    
    # Update dt = 1.0 s
    targets = {id(target): target}
    service.update(1.0, targets)
    assert pb.current_time == pytest.approx(1.0)
    assert target.transform.position[0] == pytest.approx(10.0)
    
    # Blend test
    v1 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([10.0, 10.0, 0.0], dtype=np.float32)
    blended = service.blend_vectors(v1, v2, 0.5)
    assert blended[0] == 5.0
    assert blended[1] == 5.0
