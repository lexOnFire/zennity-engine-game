from __future__ import annotations

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")

from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from editor.runtime.command_manager import CommandManager
from editor.widgets.inspector_dock import InspectorDock


class _ViewModel:
    def __init__(self, selected_object: GameObject) -> None:
        self.selected_object = selected_object
        self.command_manager = CommandManager()

    def rename_object(self, obj: GameObject, name: str) -> None:
        obj.name = name


def _app():
    app = QtWidgets.QApplication.instance()
    return app or QtWidgets.QApplication([])


def test_inspector_component_filter_keeps_matching_components() -> None:
    _app()
    obj = GameObject("Player")
    rb = obj.add_component(RigidBody())
    dock = InspectorDock()

    assert dock._component_matches_filter(obj.transform)
    dock._component_filter_text = "rigid"

    assert not dock._component_matches_filter(obj.transform)
    assert dock._component_matches_filter(rb)


def test_inspector_copy_paste_component_values_uses_command_manager() -> None:
    _app()
    source = RigidBody(mass=5.0, gravity_scale=2.0, drag=0.5)
    target = RigidBody(mass=1.0, gravity_scale=1.0, drag=0.0)
    obj = GameObject("Player")
    obj.add_component(target)
    dock = InspectorDock()
    dock.viewmodel = _ViewModel(obj)

    dock._copy_component(source)
    dock._paste_component_values(target)

    assert target.mass == 5.0
    assert target.gravity_scale == 2.0
    assert target.drag == 0.5
    dock.viewmodel.command_manager.undo()
    assert target.mass == 1.0
    assert target.gravity_scale == 1.0
    assert target.drag == 0.0


def test_inspector_reset_component_is_reversible() -> None:
    _app()
    obj = GameObject("Player")
    rb = obj.add_component(RigidBody(mass=10.0, gravity_scale=3.0, drag=2.0))
    dock = InspectorDock()
    dock.viewmodel = _ViewModel(obj)

    dock._reset_component(rb)

    assert rb.mass == 1.0
    assert rb.gravity_scale == 1.0
    assert rb.drag == 0.0
    dock.viewmodel.command_manager.undo()
    assert rb.mass == 10.0
    assert rb.gravity_scale == 3.0
    assert rb.drag == 2.0


def test_inspector_move_component_is_reversible() -> None:
    _app()
    obj = GameObject("Player")
    rb = obj.add_component(RigidBody())
    dock = InspectorDock()
    dock.viewmodel = _ViewModel(obj)

    dock._move_component(obj, rb, -1)

    assert obj.components[0] is rb
    dock.viewmodel.command_manager.undo()
    assert obj.components[1] is rb


def test_inspector_object_property_command_is_reversible() -> None:
    _app()
    obj = GameObject("Player")
    dock = InspectorDock()
    dock.viewmodel = _ViewModel(obj)

    dock._set_object_property("tag", "Enemy")

    assert obj.tag == "Enemy"
    dock.viewmodel.command_manager.undo()
    assert obj.tag == "Untagged"
