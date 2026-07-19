from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from editor.premium_panels import RealInspectorPanel
from editor.runtime.command_manager import CommandManager
from engine.components import ScriptComponent
from engine.core import Component, ComponentRegistry, component_registry
from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.prefabs.prefab_serializer import deserialize_prefab, serialize_prefab
from engine.scene.scene_serializer import deserialize_game_object, serialize_game_object


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_component_has_identity_type_enabled_and_serializes() -> None:
    component = Component()

    data = component.serialize()

    assert component.enabled
    assert data["type"] == "Component"
    assert data["enabled"] is True
    assert data["properties"] == {}


def test_component_registry_registers_and_creates_component() -> None:
    class CustomComponent(Component):
        component_type = "Custom"

    registry = ComponentRegistry()
    registry.register(CustomComponent)

    component = registry.create({"type": "Custom", "enabled": False})

    assert isinstance(component, CustomComponent)
    assert component.enabled is False


def test_game_object_add_remove_find_components_and_prevent_unique_duplicates() -> None:
    obj = GameObject("Player")
    first = obj.add_component(RigidBody(mass=2.0))
    
    with pytest.raises(ValueError, match="UNIQUE"):
        obj.add_component(RigidBody(mass=5.0))

    assert obj.get_component(RigidBody) is first
    assert obj.get_components(RigidBody) == [first]

    obj.remove_component(first)

    assert obj.get_component(RigidBody) is None


def test_game_object_transform_is_required() -> None:
    obj = GameObject("Player")

    try:
        obj.remove_component(obj.transform)
    except ValueError as exc:
        assert "Transform" in str(exc)
    else:
        raise AssertionError("Transform removal should fail")


def test_builtin_components_are_registered() -> None:
    assert component_registry.resolve("RigidBody") is RigidBody
    assert component_registry.resolve("BoxCollider").__name__ == BoxCollider.__name__
    assert component_registry.resolve("Script") is ScriptComponent
    assert component_registry.create({"type": "BoxCollider"}).__class__.__name__ == "BoxCollider"


def test_component_serialization_round_trip() -> None:
    obj = GameObject("Player")
    obj.add_component(RigidBody(mass=3.0, gravity_scale=0.5, is_kinematic=True))
    obj.add_component(BoxCollider(width=44.0, height=22.0, is_trigger=True))
    obj.add_component(ScriptComponent("Assets/Scripts/player.py"))

    data = serialize_game_object(obj)
    restored = deserialize_game_object(data)

    assert "items" in data["components"]
    rb = restored.get_component(RigidBody)
    collider = restored.get_component(BoxCollider)
    script = restored.get_component(ScriptComponent)
    assert rb is not None and rb.mass == 3.0 and rb.gravity_scale == 0.5 and rb.is_kinematic
    assert collider is not None and collider.width == 44.0 and collider.height == 22.0 and collider.is_trigger
    assert script is not None and script.script_path == "Assets/Scripts/player.py"


def test_old_scene_component_format_still_loads() -> None:
    data = {
        "name": "OldPlayer",
        "transform": {"position": [1, 2, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1]},
        "components": {
            "collider": {"type": "box", "width": 30, "height": 40},
            "rigidbody": {"mass": 9},
            "scripts": ["Assets/Scripts/legacy.py"],
        },
    }

    obj = deserialize_game_object(data)

    assert obj.get_component(BoxCollider) is not None
    assert obj.get_component(RigidBody).mass == 9
    assert obj.get_component(ScriptComponent).script_path == "Assets/Scripts/legacy.py"


def test_old_prefab_format_still_loads() -> None:
    prefab = {
        "prefab_uuid": "prefab-1",
        "source_object_name": "OldPrefab",
        "transform": {"position": [5, 6, 0], "rotation": [0, 0, 0], "scale": [1, 1, 1]},
        "components": {"collider": {"type": "box", "width": 10, "height": 20}},
        "visual": {"mesh_type": "Quadrado"},
    }

    obj = deserialize_prefab(prefab)

    assert obj.prefab_uuid == "prefab-1"
    assert obj.get_component(BoxCollider) is not None
    assert np.allclose(obj.transform.position, [5, 6, 0])


def test_prefab_serializes_component_items() -> None:
    obj = GameObject("PrefabSource")
    obj.add_component(RigidBody(mass=4.0))

    data = serialize_prefab(obj, "prefab-2")

    assert data["components"]["items"][0]["type"] == "RigidBody"


def test_inspector_lists_components_and_edits_with_undo_redo(qapp) -> None:
    obj = GameObject("Inspectable")
    rb = obj.add_component(RigidBody(mass=1.0))
    inspector = RealInspectorPanel()
    commands = CommandManager()
    inspector.set_command_manager(commands)

    inspector.load_object(obj)
    inspector.set_component_property(rb, "mass", 8.0)

    assert "RigidBody" in inspector.renderer_label.text()
    assert rb.mass == 8.0

    commands.undo()
    assert rb.mass == 1.0

    commands.redo()
    assert rb.mass == 8.0
