from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication, QComboBox

from engine.physics.rigidbody import RigidBody
from editor.inspector.plugin_ui_utils import _enum_field
from editor.inspector.plugins.rigid_body_inspector_plugin import RigidBodyInspectorPlugin
from editor.runtime.command_manager import CommandManager
from editor.scene_persistence import EditorScenePersistence


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_enum_property_creates_combobox(qapp):
    changed_val = []
    combo = _enum_field("dynamic", ("dynamic", "kinematic", "static"), lambda v: changed_val.append(v))
    assert isinstance(combo, QComboBox)
    assert combo.count() == 3
    assert combo.currentText() == "Dynamic"


def test_enum_choices_from_component_metadata(qapp):
    rb = RigidBody()
    choices = getattr(rb, "BODY_TYPES", None)
    assert choices == ("dynamic", "kinematic", "static")


def test_rigidbody_enum_choices(qapp):
    rb = RigidBody()
    plugin = RigidBodyInspectorPlugin()
    widget = plugin.create_widget(rb, CommandManager())
    combo = widget.findChild(QComboBox, "InspectorEnumField")
    assert combo is not None
    items = [combo.itemText(i) for i in range(combo.count())]
    assert items == ["Dynamic", "Kinematic", "Static"]


def test_enum_change_updates_model(qapp):
    rb = RigidBody()
    plugin = RigidBodyInspectorPlugin()
    widget = plugin.create_widget(rb, None)
    combo = widget.findChild(QComboBox, "InspectorEnumField")
    
    # Troca de Dynamic para Kinematic
    combo.setCurrentIndex(1)
    assert rb.body_type == "kinematic"
    assert rb.is_kinematic is True

    # Troca para Static
    combo.setCurrentIndex(2)
    assert rb.body_type == "static"
    assert rb.is_kinematic is True
    assert rb.use_gravity is False


def test_enum_change_marks_dirty(qapp):
    rb = RigidBody()
    dirty_calls = []
    plugin = RigidBodyInspectorPlugin()
    widget = plugin.create_widget(rb, None, refresh=lambda: dirty_calls.append(True))
    combo = widget.findChild(QComboBox, "InspectorEnumField")
    combo.setCurrentIndex(1)
    assert len(dirty_calls) == 1


def test_enum_save_reopen_roundtrip(qapp):
    rb = RigidBody(body_type="kinematic")
    serialized = rb.serialize_properties()
    assert serialized.get("body_type") == "kinematic"

    rb2 = RigidBody()
    rb2.deserialize_properties(serialized)
    assert rb2.body_type == "kinematic"
    assert rb2.is_kinematic is True


def test_enum_runtime_value_matches_authoring(qapp):
    rb = RigidBody()
    rb.body_type = "kinematic"
    assert rb.is_kinematic is True
    # Kinematic objects stop taking forces in runtime update
    rb.add_force(100.0, 0.0)
    assert rb.acceleration[0] == 0.0


def test_invalid_enum_does_not_crash(qapp):
    rb = RigidBody()
    combo = _enum_field("unknown_mode", ("dynamic", "kinematic", "static"), lambda v: None)
    assert isinstance(combo, QComboBox)
    assert "Unknown (unknown_mode)" in combo.currentText()


def test_enum_undo(qapp):
    rb = RigidBody(body_type="dynamic")
    cmd_mgr = CommandManager()
    plugin = RigidBodyInspectorPlugin()
    widget = plugin.create_widget(rb, cmd_mgr)
    combo = widget.findChild(QComboBox, "InspectorEnumField")

    # Change to Kinematic
    combo.setCurrentIndex(1)
    assert rb.body_type == "kinematic"

    # Undo
    cmd_mgr.undo()
    assert rb.body_type == "dynamic"


def test_enum_redo(qapp):
    rb = RigidBody(body_type="dynamic")
    cmd_mgr = CommandManager()
    plugin = RigidBodyInspectorPlugin()
    widget = plugin.create_widget(rb, cmd_mgr)
    combo = widget.findChild(QComboBox, "InspectorEnumField")

    combo.setCurrentIndex(1)
    cmd_mgr.undo()
    assert rb.body_type == "dynamic"

    cmd_mgr.redo()
    assert rb.body_type == "kinematic"
