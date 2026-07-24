from __future__ import annotations

import numpy as np
import pytest

from editor_legacy.editor_2d import Editor2DScene
from engine.animation import AnimationClip, Animator, Keyframe
from engine.core.component_registry import component_registry
from engine.game_object import GameObject
from engine.runtime import RuntimeManager, Time
from engine.scene.scene_serializer import deserialize_game_object, serialize_game_object


def _empty_editor_scene() -> Editor2DScene:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1
    return scene


def _move_clip(loop: bool = False) -> AnimationClip:
    return AnimationClip(
        "move",
        frames=[],
        duration=1.0,
        loop=loop,
        keyframes=[
            Keyframe(0.0, "position", [0.0, 0.0, 0.0]),
            Keyframe(1.0, "position", [10.0, 0.0, 0.0]),
        ],
    )


def setup_function() -> None:
    Time._runtime_reset()


def teardown_function() -> None:
    Time._runtime_reset()


def test_keyframe_creation_and_serialization() -> None:
    keyframe = Keyframe(0.5, "scale", [2.0, 2.0, 1.0])

    restored = Keyframe.deserialize(keyframe.serialize())

    assert restored.time == pytest.approx(0.5)
    assert restored.property == "scale"
    assert restored.value == [2.0, 2.0, 1.0]


def test_animation_clip_samples_interpolated_properties() -> None:
    clip = _move_clip()

    sample = clip.sample(0.5)

    assert sample["position"] == pytest.approx([5.0, 0.0, 0.0])
    assert clip.properties == ["position"]
    assert clip.duration == pytest.approx(1.0)


def test_animator_play_pause_and_stop() -> None:
    animator = Animator(default_clip="move")
    animator.add_clip(_move_clip())

    animator.play("move")
    assert animator.is_playing("move")

    animator.pause()
    assert not animator.is_any_playing

    animator.resume()
    assert animator.is_any_playing

    animator.stop()
    assert animator.current_clip is None
    assert not animator.is_any_playing


def test_animator_loop_wraps_clip_time() -> None:
    obj = GameObject("Animated")
    animator = obj.add_component(Animator(default_clip="move"))
    animator.add_clip(_move_clip(loop=True))
    animator.play("move")

    Time._runtime_tick(1.25)
    animator.on_runtime_update(999.0)

    assert animator.current_time == pytest.approx(0.25)
    assert float(obj.transform.position[0]) == pytest.approx(2.5)


def test_animator_uses_official_time_delta_time() -> None:
    obj = GameObject("Animated")
    animator = obj.add_component(Animator(default_clip="move"))
    animator.add_clip(_move_clip())
    animator.play("move")

    Time.time_scale = 0.5
    Time._runtime_tick(1.0)
    animator.on_runtime_update(999.0)

    assert Time.delta_time == pytest.approx(0.5)
    assert float(obj.transform.position[0]) == pytest.approx(5.0)


def test_animator_changes_runtime_transform_and_preserves_editor_world() -> None:
    scene = _empty_editor_scene()
    editor_obj = GameObject("Player")
    editor_obj.transform.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    animator = editor_obj.add_component(Animator(default_clip="move"))
    animator.add_clip(_move_clip())
    scene._add_go(editor_obj)
    scene.editable_objects.append(editor_obj)
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    manager.tick(0.5)
    runtime_obj = runtime_scene.runtime_for_editor(editor_obj)

    assert runtime_obj is not None
    assert float(runtime_obj.transform.position[0]) == pytest.approx(5.0)
    assert float(editor_obj.transform.position[0]) == pytest.approx(0.0)

    manager.stop_play()
    assert manager.runtime_scene is None
    assert float(editor_obj.transform.position[0]) == pytest.approx(0.0)


def test_animator_component_serializes_and_deserializes() -> None:
    animator = Animator(default_clip="move", speed=1.5)
    animator.add_clip(_move_clip(loop=True))
    animator.play("move")

    restored = component_registry.create(animator.serialize())

    assert isinstance(restored, Animator)
    assert restored.speed == pytest.approx(1.5)
    assert restored.current_clip == "move"
    assert restored._clips["move"].loop is True
    assert restored._clips["move"].keyframes[1].value == [10.0, 0.0, 0.0]


def test_scene_serialization_preserves_animator_component() -> None:
    obj = GameObject("Animated")
    animator = obj.add_component(Animator(default_clip="move"))
    animator.add_clip(_move_clip())

    data = serialize_game_object(obj)
    restored = deserialize_game_object(data)
    restored_animator = restored.get_component(Animator)

    assert data["components"]["items"][0]["type"] == "Animator"
    assert restored_animator is not None
    assert restored_animator._clips["move"].duration == pytest.approx(1.0)
