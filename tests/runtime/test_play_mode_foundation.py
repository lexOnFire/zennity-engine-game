from __future__ import annotations

import numpy as np

from editor_legacy.editor_2d import Editor2DScene
from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.runtime import RuntimeManager, RuntimeScene, RuntimeState, clone_game_object


def _editor_scene_with_object() -> tuple[Editor2DScene, GameObject]:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()

    parent = GameObject("Player", tag="Player")
    parent.layer = 2
    parent.mesh_type = "Player"
    parent.transform.position = np.array([10.0, 20.0, 0.0], dtype=np.float32)
    parent.transform.rotation = np.array([0.0, 0.0, 45.0], dtype=np.float32)
    parent.transform.scale = np.array([36.0, 48.0, 1.0], dtype=np.float32)
    parent.add_component(BoxCollider(width=36, height=48))
    parent.add_component(RigidBody(mass=2.0, gravity_scale=0.5))

    child = GameObject("Child")
    child.transform.position = np.array([1.0, 2.0, 0.0], dtype=np.float32)
    parent.add_child(child)

    scene._add_go(parent)
    scene.editable_objects.append(parent)
    scene.selected_index = 0
    return scene, parent


def test_clone_game_object_is_deep_and_independent() -> None:
    _, source = _editor_scene_with_object()

    clone = clone_game_object(source)

    assert clone is not source
    assert clone.id != source.id
    assert clone.runtime_source_id == source.id
    assert clone.transform is not source.transform
    assert np.allclose(clone.transform.position, source.transform.position)
    assert clone.get_component(RigidBody) is not source.get_component(RigidBody)
    assert clone.get_component(BoxCollider) is not source.get_component(BoxCollider)
    assert clone.children[0] is not source.children[0]

    clone.transform.position[0] = 999.0
    clone.get_component(RigidBody).velocity[1] = 123.0

    assert float(source.transform.position[0]) == 10.0
    assert float(source.get_component(RigidBody).velocity[1]) == 0.0


def test_runtime_scene_clones_editor_scene_and_maps_selection() -> None:
    editor_scene, editor_obj = _editor_scene_with_object()

    runtime_scene = RuntimeScene(editor_scene)
    runtime_obj = runtime_scene.runtime_for_editor(editor_obj)

    assert runtime_scene.playing
    assert runtime_scene is not editor_scene
    assert runtime_obj is not None
    assert runtime_obj is runtime_scene.editable_objects[0]
    assert runtime_scene.editor_for_runtime(runtime_obj) is editor_obj
    assert runtime_scene.selected_index == editor_scene.selected_index

    runtime_obj.transform.position[1] += 50.0
    assert float(editor_obj.transform.position[1]) == 20.0

    runtime_scene.destroy()
    assert not runtime_scene.playing
    assert runtime_scene.editable_objects == []


def test_runtime_manager_start_stop_lifecycle() -> None:
    editor_scene, _ = _editor_scene_with_object()
    manager = RuntimeManager()

    runtime_scene = manager.start_play(editor_scene)

    assert manager.state == RuntimeState.PLAYING
    assert manager.is_playing
    assert manager.runtime_scene is runtime_scene

    manager.stop_play()

    assert manager.state == RuntimeState.STOPPED
    assert not manager.is_playing
    assert manager.runtime_scene is None
