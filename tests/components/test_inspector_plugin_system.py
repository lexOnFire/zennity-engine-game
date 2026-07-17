from __future__ import annotations

from typing import Any
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from editor.inspector import InspectorPlugin, InspectorPluginRegistry, inspector_plugin_registry
from editor.premium_panels import RealInspectorPanel
from editor.runtime.command_manager import CommandManager
from engine.animation import Animator
from engine.core import Component, register_component
from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.ui.runtime_components import ButtonComponent, Canvas, ImageComponent, LabelComponent


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class DummyPlugin(InspectorPlugin):
    component_type = "Dummy"

    def create_widget(self, component: Any, command_manager: CommandManager | None, refresh: callable | None = None) -> QWidget:
        widget = QLabel("Dummy Editor")
        widget.setProperty("component_type", self.component_type)
        return widget


def test_inspector_plugin_registry_registers_and_resolves_plugin() -> None:
    class DummyComponent(Component):
        component_type = "Dummy"

    registry = InspectorPluginRegistry()
    plugin = registry.register(DummyPlugin)

    assert registry.plugin_for(DummyComponent()) is plugin


def test_default_plugins_resolve_builtin_components() -> None:
    assert inspector_plugin_registry.plugin_for(GameObject("Obj").transform).component_type == "Transform"
    assert inspector_plugin_registry.plugin_for(RigidBody()).component_type == "RigidBody"
    assert inspector_plugin_registry.plugin_for(BoxCollider()).component_type == "Collider"
    assert inspector_plugin_registry.plugin_for(Animator()).component_type == "Animator"
    assert inspector_plugin_registry.plugin_for(Canvas()).component_type == "Canvas"
    assert inspector_plugin_registry.plugin_for(LabelComponent()).component_type == "Label"
    assert inspector_plugin_registry.plugin_for(ImageComponent()).component_type == "Image"
    assert inspector_plugin_registry.plugin_for(ButtonComponent()).component_type == "Button"


def test_inspector_hosts_plugins_for_multiple_components(qapp) -> None:
    obj = GameObject("Inspectable")
    obj.add_component(RigidBody())
    obj.add_component(BoxCollider())
    obj.add_component(Animator())
    inspector = RealInspectorPanel()

    inspector.load_object(obj)

    hosted_types = [
        widget.property("component_type")
        for widget in inspector.component_list.findChildren(QWidget)
        if widget.property("component_type")
    ]
    assert "Transform" in hosted_types
    assert "RigidBody" in hosted_types
    assert "BoxCollider" in hosted_types
    assert "Animator" in hosted_types


def test_inspector_handles_missing_plugin(qapp) -> None:
    class NoPluginComponent(Component):
        component_type = "NoPlugin"

    obj = GameObject("Inspectable")
    obj.add_component(NoPluginComponent())
    inspector = RealInspectorPanel()
    empty_registry = InspectorPluginRegistry()
    inspector.set_inspector_plugin_registry(empty_registry)

    inspector.load_object(obj)

    labels = [label.text() for label in inspector.component_list.findChildren(QLabel)]
    assert "NoPlugin" in labels


def test_plugin_edit_uses_undo_redo(qapp) -> None:
    obj = GameObject("Inspectable")
    rb = obj.add_component(RigidBody(mass=1.0))
    inspector = RealInspectorPanel()
    commands = CommandManager()
    inspector.set_command_manager(commands)
    inspector.load_object(obj)

    inspector.set_component_property(rb, "mass", 9.0)

    assert rb.mass == 9.0
    commands.undo()
    assert rb.mass == 1.0
    commands.redo()
    assert rb.mass == 9.0


def test_inspector_switches_selection_and_rebuilds_plugins(qapp) -> None:
    first = GameObject("First")
    first.add_component(RigidBody())
    second = GameObject("Second")
    second.add_component(BoxCollider())
    inspector = RealInspectorPanel()

    inspector.load_object(first)
    assert "RigidBody" in inspector.renderer_label.text()

    inspector.load_object(second)

    assert "BoxCollider" in inspector.renderer_label.text()
    assert "RigidBody" not in inspector.renderer_label.text()


def test_new_component_and_plugin_appear_without_inspector_change(qapp) -> None:
    class Health(Component):
        component_type = "Health"
        unique = True

    class HealthPlugin(InspectorPlugin):
        component_type = "Health"

        def create_widget(self, component: Any, command_manager: CommandManager | None, refresh: callable | None = None) -> QWidget:
            widget = QLabel("Health Editor")
            widget.setProperty("component_type", self.component_type)
            return widget

    register_component(Health)
    custom_plugins = InspectorPluginRegistry()
    custom_plugins.register(HealthPlugin)
    obj = GameObject("Player")
    inspector = RealInspectorPanel()
    inspector.set_inspector_plugin_registry(custom_plugins)
    inspector.load_object(obj)

    assert "Health" in inspector.available_component_names()

    component = inspector.add_component_to_selected("Health")
    assert isinstance(component, Health)
    assert "Health" in inspector.renderer_label.text()


def test_inspector_dock_does_not_import_concrete_component_widgets() -> None:
    source = Path("editor/widgets/inspector_dock.py").read_text(encoding="utf-8")

    forbidden = [
        "TransformComponentWidget",
        "RigidBodyComponentWidget",
        "ColliderComponentWidget",
        "ScriptComponentWidget",
        "MeshRendererComponentWidget",
        "from engine.physics",
        "isinstance(",
        "elif component_name",
    ]

    for token in forbidden:
        assert token not in source
