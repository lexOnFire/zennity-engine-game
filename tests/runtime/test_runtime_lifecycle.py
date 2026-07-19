from __future__ import annotations

import numpy as np

from editor_legacy.editor_2d import Editor2DScene
from engine.core import Component
from engine.core.component_registry import register_component
from engine.game_object import GameObject
from engine.runtime import RuntimeManager, RuntimeState


class LifecycleProbe(Component):
    component_type = "LifecycleProbe"
    events: list[tuple[str, str, float | None]] = []

    def __init__(self, label: str = "probe") -> None:
        super().__init__()
        self.label = label

    def serialize_properties(self) -> dict:
        return {"label": self.label}

    def deserialize_properties(self, data: dict) -> None:
        self.label = str(data.get("label", "probe"))

    def on_runtime_start(self) -> None:
        self.events.append(("start", self.label, None))

    def on_runtime_update(self, delta_time: float) -> None:
        self.events.append(("update", self.label, float(delta_time)))

    def on_runtime_stop(self) -> None:
        self.events.append(("stop", self.label, None))


register_component(LifecycleProbe)


def _empty_editor_scene() -> Editor2DScene:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1
    return scene


def _add_probe_object(
    scene: Editor2DScene,
    name: str = "Object",
    label: str = "probe",
    *,
    active: bool = True,
    enabled: bool = True,
) -> GameObject:
    obj = GameObject(name)
    obj.transform.position = np.array([1.0, 2.0, 0.0], dtype=np.float32)
    obj.active = active
    probe = obj.add_component(LifecycleProbe(label))
    probe.enabled = enabled
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    return obj


def setup_function() -> None:
    LifecycleProbe.events.clear()


def test_tick_without_play_does_nothing() -> None:
    manager = RuntimeManager()

    manager.tick(0.5)

    assert LifecycleProbe.events == []
    assert manager.state == RuntimeState.STOPPED


def test_start_calls_runtime_start_once_and_play_twice_does_not_duplicate() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene, label="a")
    manager = RuntimeManager()

    first = manager.start_play(scene)
    second = manager.start_play(scene)

    assert first is second
    assert LifecycleProbe.events == [("start", "a", None)]


def test_tick_calls_runtime_update_only_while_playing() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene, label="a")
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.25)

    assert ("update", "a", 0.25) in LifecycleProbe.events


def test_stop_calls_runtime_stop_and_destroys_scene() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene, label="a")
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.stop_play()

    assert LifecycleProbe.events == [("start", "a", None), ("stop", "a", None)]
    assert manager.runtime_scene is None
    assert manager.state == RuntimeState.STOPPED


def test_stop_twice_is_safe() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene, label="a")
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.stop_play()
    manager.stop_play()

    assert LifecycleProbe.events.count(("stop", "a", None)) == 1


def test_disabled_components_do_not_receive_lifecycle() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene, label="disabled", enabled=False)
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.1)
    manager.stop_play()

    assert LifecycleProbe.events == []


def test_inactive_game_objects_do_not_receive_lifecycle() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene, label="inactive", active=False)
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.1)
    manager.stop_play()

    assert LifecycleProbe.events == []


def test_inactive_parent_blocks_child_lifecycle() -> None:
    scene = _empty_editor_scene()
    parent = _add_probe_object(scene, label="parent", active=False)
    child = GameObject("Child")
    child.add_component(LifecycleProbe("child"))
    parent.add_child(child)
    scene._add_go(child)

    manager = RuntimeManager()
    manager.start_play(scene)
    manager.tick(0.1)
    manager.stop_play()

    assert LifecycleProbe.events == []


def test_multiple_components_receive_update() -> None:
    scene = _empty_editor_scene()
    obj = GameObject("Object")
    obj.add_component(LifecycleProbe("a"))
    obj.add_component(LifecycleProbe("b"))
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.2)

    assert ("update", "a", 0.2) in LifecycleProbe.events
    assert ("update", "b", 0.2) in LifecycleProbe.events


def test_editor_scene_is_not_modified_by_runtime_lifecycle() -> None:
    scene = _empty_editor_scene()
    editor_obj = _add_probe_object(scene, label="editor")
    original_x = float(editor_obj.transform.position[0])
    manager = RuntimeManager()

    manager.start_play(scene)
    runtime_obj = manager.runtime_scene.runtime_for_editor(editor_obj)
    runtime_obj.transform.position[0] = 99.0
    manager.tick(0.1)
    manager.stop_play()

    assert float(editor_obj.transform.position[0]) == original_x


def test_play_tick_stop_sequence_is_safe() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene, label="a")
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.1)
    manager.stop_play()
    manager.tick(0.1)

    assert LifecycleProbe.events == [
        ("start", "a", None),
        ("update", "a", 0.1),
        ("stop", "a", None),
    ]


def test_runtime_manager_notifies_state_transitions_once() -> None:
    scene = _empty_editor_scene()
    manager = RuntimeManager()
    states = []
    manager.subscribe_state(states.append)

    manager.start_play(scene)
    manager.start_play(scene)
    manager.stop_play()
    manager.stop_play()

    assert states == [RuntimeState.PLAYING, RuntimeState.STOPPED]
