from __future__ import annotations

import numpy as np
import pytest

from editor_legacy.editor_2d import Editor2DScene
from engine.core import Component
from engine.core.component_registry import register_component
from engine.game_object import GameObject
from engine.physics import BoxCollider, CircleCollider, Physics, PhysicsWorld, RigidBody
from engine.runtime import RuntimeManager, Time


class TriggerProbe(Component):
    component_type = "TriggerProbe"
    events: list[tuple[str, str]] = []

    def on_trigger_enter(self, other) -> None:
        owner = self.game_object.name if self.game_object else "<none>"
        self.events.append(("enter", owner))

    def on_trigger_exit(self, other) -> None:
        owner = self.game_object.name if self.game_object else "<none>"
        self.events.append(("exit", owner))


register_component(TriggerProbe)


def _empty_editor_scene() -> Editor2DScene:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1
    return scene


def _add_object(scene: Editor2DScene, name: str, x: float, y: float) -> GameObject:
    obj = GameObject(name)
    obj.transform.position = np.array([x, y, 0.0], dtype=np.float32)
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    return obj


def setup_function() -> None:
    Time._runtime_reset()
    TriggerProbe.events.clear()
    Physics.unbind_world()


def teardown_function() -> None:
    Time._runtime_reset()
    TriggerProbe.events.clear()
    Physics.unbind_world()


def test_physics_world_registers_and_unregisters_rigidbody() -> None:
    obj = GameObject("Body")
    body = obj.add_component(RigidBody())
    world = PhysicsWorld()

    world.register_rigidbody(body)
    assert world.rigidbodies == [body]
    assert body._runtime_physics_managed is True

    world.unregister_rigidbody(body)
    assert world.rigidbodies == []
    assert body._runtime_physics_managed is False


def test_physics_world_registers_and_unregisters_collider() -> None:
    obj = GameObject("Collider")
    collider = obj.add_component(BoxCollider())
    world = PhysicsWorld()

    world.register_collider(collider)
    world.unregister_collider(collider)

    assert world.colliders == []


def test_physics_world_detects_box_box_collision() -> None:
    scene = _empty_editor_scene()
    a = _add_object(scene, "A", 0.0, 0.0)
    b = _add_object(scene, "B", 10.0, 0.0)
    ca = a.add_component(BoxCollider(width=32, height=32))
    cb = b.add_component(BoxCollider(width=32, height=32))
    world = PhysicsWorld()
    world.register_collider(ca)
    world.register_collider(cb)

    contacts = world.detect_collisions()

    assert len(contacts) == 1
    assert contacts[0].a is ca
    assert contacts[0].b is cb
    assert contacts[0].is_trigger is False


def test_physics_world_detects_circle_circle_collision() -> None:
    scene = _empty_editor_scene()
    a = _add_object(scene, "A", 0.0, 0.0)
    b = _add_object(scene, "B", 20.0, 0.0)
    ca = a.add_component(CircleCollider(radius=16))
    cb = b.add_component(CircleCollider(radius=16))
    world = PhysicsWorld()
    world.register_collider(ca)
    world.register_collider(cb)

    contacts = world.detect_collisions()

    assert len(contacts) == 1
    assert contacts[0].is_trigger is False


def test_physics_world_detects_box_circle_collision() -> None:
    scene = _empty_editor_scene()
    box_obj = _add_object(scene, "Box", 0.0, 0.0)
    circle_obj = _add_object(scene, "Circle", 18.0, 0.0)
    box = box_obj.add_component(BoxCollider(width=32, height=32))
    circle = circle_obj.add_component(CircleCollider(radius=8))
    world = PhysicsWorld()
    world.register_collider(box)
    world.register_collider(circle)

    contacts = world.detect_collisions()

    assert len(contacts) == 1


def test_trigger_enter_and_exit_are_emitted() -> None:
    scene = _empty_editor_scene()
    a = _add_object(scene, "A", 0.0, 0.0)
    b = _add_object(scene, "B", 10.0, 0.0)
    a.add_component(TriggerProbe())
    b.add_component(TriggerProbe())
    ca = a.add_component(BoxCollider(width=32, height=32, is_trigger=True))
    cb = b.add_component(BoxCollider(width=32, height=32))
    world = PhysicsWorld()
    world.register_collider(ca)
    world.register_collider(cb)

    world.detect_collisions()
    b.transform.position[0] = 200.0
    world.detect_collisions()

    assert TriggerProbe.events[:2] == [("enter", "A"), ("enter", "B")]
    assert set(TriggerProbe.events[2:]) == {("exit", "A"), ("exit", "B")}


def test_runtime_builds_physics_world_from_runtime_scene_and_cleans_on_stop() -> None:
    scene = _empty_editor_scene()
    obj = _add_object(scene, "Player", 0.0, 0.0)
    obj.add_component(RigidBody(use_gravity=False))
    obj.add_component(BoxCollider())
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)

    assert len(runtime_scene.physics_world.rigidbodies) == 1
    assert len(runtime_scene.physics_world.colliders) == 1
    assert Physics.contacts() == []

    world = runtime_scene.physics_world
    manager.stop_play()

    assert world.rigidbodies == []
    assert world.colliders == []
    assert Physics.contacts() == []


def test_runtime_physics_uses_fixed_delta_time_and_does_not_modify_editor_world() -> None:
    scene = _empty_editor_scene()
    editor_obj = _add_object(scene, "Player", 0.0, 0.0)
    body = editor_obj.add_component(RigidBody(use_gravity=False))
    body.velocity = np.array([60.0, 0.0], dtype=np.float32)
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    runtime_obj = runtime_scene.runtime_for_editor(editor_obj)
    manager.tick(0.5)

    assert float(runtime_obj.transform.position[0]) == pytest.approx(60.0 * Time.fixed_delta_time)
    assert float(editor_obj.transform.position[0]) == pytest.approx(0.0)


def test_runtime_physics_detects_trigger_contacts_between_clones_only() -> None:
    scene = _empty_editor_scene()
    a = _add_object(scene, "A", 0.0, 0.0)
    b = _add_object(scene, "B", 10.0, 0.0)
    a.add_component(BoxCollider(width=32, height=32, is_trigger=True))
    b.add_component(BoxCollider(width=32, height=32))
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    manager.tick(0.1)
    contact = runtime_scene.physics_world.detected_contacts[0]

    assert contact.is_trigger is True
    assert contact.a.game_object is not a
    assert contact.b.game_object is not b
