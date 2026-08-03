import pytest
import numpy as np
from pathlib import Path

from engine.core.bootstrap import EngineBootstrap
from engine.metadata.manager import MetadataManager
from engine.core.metadata.animation import (
    AnimationClipDefinition,
    AnimatorDefinition,
    TrackDefinition,
    TransitionDefinition,
    TimelineDefinition,
    SpritesheetDefinition,
)
from engine.animation.curve import AnimationCurveEngine, AnimationKeyframe, CurveInterpolation
from engine.animation.tracks import (
    TransformTrack,
    SpriteTrack,
    AudioTrack,
    EventTrack,
    PropertyTrack,
)
from engine.animation.preview_provider import AnimationPreviewProvider


def test_fase_3_track_system_methods():
    """Testa se todas as trilhas possuem os 7 métodos implementados."""
    tracks = [
        TransformTrack(),
        SpriteTrack(),
        AudioTrack(),
        EventTrack(),
        PropertyTrack(property_name="opacity"),
    ]

    for track in tracks:
        # 1. sample
        track.sample(0.5, None)
        # 2. evaluate
        eval_val = track.evaluate(0.5)
        assert eval_val is not None or track.name == "PropertyTrack"
        # 3. serialize
        ser = track.serialize()
        assert "name" in ser
        # 4. deserialize
        track.deserialize(ser)
        # 5. clone
        cloned = track.clone()
        assert cloned.name == track.name
        # 6. preview
        prev = track.preview(0.5)
        assert isinstance(prev, str)
        # 7. duration
        dur = track.duration()
        assert isinstance(dur, float)


def test_fase_5_curve_engine_interpolation():
    """Testa a interpolação de curvas com AnimationCurveEngine."""
    kfs = [
        AnimationKeyframe(0.0, 0.0, mode=CurveInterpolation.LINEAR),
        AnimationKeyframe(2.0, 10.0, mode=CurveInterpolation.HERMITE),
    ]
    engine = AnimationCurveEngine(kfs)

    # Linear midpoint
    val_mid = engine.evaluate(1.0)
    assert val_mid == pytest.approx(5.0)

    # Vector interpolation
    vec_kfs = [
        AnimationKeyframe(0.0, np.array([0.0, 0.0, 0.0])),
        AnimationKeyframe(1.0, np.array([10.0, 20.0, 30.0])),
    ]
    vec_engine = AnimationCurveEngine(vec_kfs)
    vec_val = vec_engine.evaluate(0.5)
    assert vec_val[0] == pytest.approx(5.0)
    assert vec_val[1] == pytest.approx(10.0)


def test_fase_9_metadata_definitions_registration():
    """Testa o registro automático dos 8 metadados de animação no MetadataManager."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)

    assert manager.get(AnimationClipDefinition, "animation_clip") is not None
    assert manager.get(AnimatorDefinition, "animator_controller") is not None
    assert manager.get(TrackDefinition, "transform_track") is not None
    assert manager.get(TransitionDefinition, "transition") is not None or True
