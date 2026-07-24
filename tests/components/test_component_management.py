from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from editor.premium_panels import RealInspectorPanel
from editor.runtime.command_manager import CommandManager
from editor.runtime.component_commands import AddComponentCommand, RemoveComponentCommand
from engine.components import ScriptComponent
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


def test_add_component_command_adds_component() -> None:
    obj = GameObject("Player")
    command = AddComponentCommand(obj, "RigidBody")

    command.execute()

    assert isinstance(command.component, RigidBody)
    assert obj.get_component(RigidBody) is command.component


def test_remove_component_command_removes_component() -> None:
    obj = GameObject("Player")
    rigidbody = obj.add_component(RigidBody())
    command = RemoveComponentCommand(obj, rigidbody)

    command.execute()

    assert obj.get_component(RigidBody) is None
    assert rigidbody.game_object is None


def test_undo_and_redo_add_component() -> None:
    obj = GameObject("Player")
    manager = CommandManager()
    command = AddComponentCommand(obj, "RigidBody")

    manager.execute(command)
    manager.undo()
    manager.redo()

    assert obj.get_component(RigidBody) is command.component


def test_undo_and_redo_remove_component_restores_same_instance_and_order() -> None:
    obj = GameObject("Player")
    collider = obj.add_component(BoxCollider())
    rigidbody = obj.add_component(RigidBody())
    manager = CommandManager()

    manager.execute(RemoveComponentCommand(obj, collider))
    manager.undo()
    manager.redo()

    assert obj.get_component(BoxCollider) is None
    manager.undo()
    assert obj.components[1] is collider
    assert obj.components[2] is rigidbody


def test_cannot_remove_transform() -> None:
    obj = GameObject("Player")

    with pytest.raises(ValueError):
        RemoveComponentCommand(obj, obj.transform).execute()


def test_cannot_add_duplicate_unique_component() -> None:
    obj = GameObject("Player")
    AddComponentCommand(obj, "RigidBody").execute()

    with pytest.raises(ValueError):
        AddComponentCommand(obj, "RigidBody").execute()


def test_inspector_adds_and_removes_components_with_undo_redo(qapp) -> None:
    obj = GameObject("Inspectable")
    inspector = RealInspectorPanel()
    manager = CommandManager()
    inspector.set_command_manager(manager)
    inspector.load_object(obj)

    component = inspector.add_component_to_selected("RigidBody")
    assert component is obj.get_component(RigidBody)
    assert "RigidBody" in inspector.renderer_label.text()

    manager.undo()
    inspector.load_object(obj)
    assert obj.get_component(RigidBody) is None
    assert "RigidBody" not in inspector.renderer_label.text()

    manager.redo()
    inspector.load_object(obj)
    assert obj.get_component(RigidBody) is component

    assert inspector.remove_component_from_selected(component)
    assert obj.get_component(RigidBody) is None
    manager.undo()
    inspector.load_object(obj)
    assert obj.get_component(RigidBody) is component


def test_inspector_blocks_transform_removal(qapp) -> None:
    obj = GameObject("Inspectable")
    inspector = RealInspectorPanel()
    inspector.load_object(obj)

    assert inspector.remove_component_from_selected(obj.transform) is False
    assert obj.transform in obj.components
    assert "nao pode ser removido" in inspector.status_label.text()


def test_inspector_available_components_respects_unique_components(qapp) -> None:
    obj = GameObject("Inspectable")
    inspector = RealInspectorPanel()
    inspector.load_object(obj)

    assert "RigidBody" in inspector.available_component_names()

    inspector.add_component_to_selected("RigidBody")

    assert "RigidBody" not in inspector.available_component_names()


def test_serialization_reflects_added_and_removed_components() -> None:
    obj = GameObject("Player")
    add = AddComponentCommand(obj, "RigidBody")
    add.execute()
    obj.add_component(ScriptComponent("Assets/Scripts/player.py"))

    data = serialize_game_object(obj)
    assert [item["type"] for item in data["components"]["items"]] == ["RigidBody", "ScriptComponent"]

    RemoveComponentCommand(obj, add.component).execute()
    data = serialize_game_object(obj)
    assert [item["type"] for item in data["components"]["items"]] == ["ScriptComponent"]

    restored = deserialize_game_object(data)
    assert restored.get_component(RigidBody) is None
    assert restored.get_component(ScriptComponent).script_path == "Assets/Scripts/player.py"


def test_prefab_serialization_keeps_component_changes() -> None:
    obj = GameObject("PrefabSource")
    AddComponentCommand(obj, "BoxCollider").execute()
    prefab = serialize_prefab(obj, "prefab-components")

    restored = deserialize_prefab(prefab)

    assert restored.get_component(BoxCollider) is not None
