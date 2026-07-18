from __future__ import annotations

import sys
# Restaura o ambiente contra poluição de mocks de outros testes
for name in ["engine.physics.collider", "engine.physics.rigidbody", "engine.physics", "engine.transitions", "engine.audio", "engine.ui.ui_manager", "engine.ui"]:
    if name in sys.modules:
        mod = sys.modules[name]
        if not getattr(mod, "__file__", None) and not getattr(mod, "__path__", None):
            sys.modules.pop(name, None)

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
from editor.models.scene_model import SceneModel
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.runtime.editor_context import EditorContext
from editor.widgets.inspector_dock import InspectorDock


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def editor_context() -> EditorContext:
    return EditorContext()


@pytest.fixture
def scene_model() -> SceneModel:
    return SceneModel()


@pytest.fixture
def scene_viewmodel(scene_model: SceneModel, editor_context: EditorContext) -> SceneViewModel:
    return SceneViewModel(
        scene_model,
        selection_manager=editor_context.selection
    )


@pytest.fixture
def inspector(qapp: QApplication, scene_viewmodel: SceneViewModel) -> InspectorDock:
    dock = InspectorDock()
    dock.set_viewmodel(scene_viewmodel)
    return dock


def test_inspector_empty_state_without_selection(inspector: InspectorDock) -> None:
    assert inspector.lc.count() == 1
    widget = inspector.lc.itemAt(0).widget()
    assert widget is not None
    assert "Selecione um objeto" in widget.text()


def test_inspector_populates_fields_on_selection(inspector: InspectorDock, scene_viewmodel: SceneViewModel) -> None:
    obj = GameObject("Target")
    obj.transform.position = np.array([12.5, 45.0, 0.0], dtype=np.float32)
    obj.transform.rotation = np.array([0.0, 0.0, 90.0], dtype=np.float32)
    obj.transform.scale = np.array([2.0, 2.5, 1.0], dtype=np.float32)

    scene_viewmodel.selected_object = obj

    assert inspector.lc.count() > 1
    assert hasattr(inspector, "transform_widget")
    
    tw = inspector.transform_widget
    assert tw.sb_pos_x.value() == 12.5
    assert tw.sb_pos_y.value() == 45.0
    assert tw.sb_rot_z.value() == 90.0
    assert tw.sb_sc_x.value() == 2.0
    assert tw.sb_sc_y.value() == 2.5


def test_inspector_interactive_update(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel
) -> None:
    obj = GameObject("Target")
    scene_viewmodel.selected_object = obj
    tw = inspector.transform_widget

    tw.sb_pos_x.setValue(55.0)
    QApplication.processEvents()
    
    assert obj.transform.position[0] == 55.0


def test_inspector_selection_switch_updates_fields(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel
) -> None:
    obj1 = GameObject("Obj1")
    obj1.transform.position = np.array([1.0, 1.0, 0.0], dtype=np.float32)
    obj2 = GameObject("Obj2")
    obj2.transform.position = np.array([2.0, 2.0, 0.0], dtype=np.float32)

    scene_viewmodel.selected_object = obj1
    assert inspector.transform_widget.sb_pos_x.value() == 1.0

    scene_viewmodel.selected_object = obj2
    assert inspector.transform_widget.sb_pos_x.value() == 2.0


def test_inspector_deleted_object_does_not_crash(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel, scene_model: SceneModel
) -> None:
    obj = GameObject("Deletable")
    scene_model.add_object(obj)
    scene_viewmodel.selected_object = obj
    
    scene_model.remove_object(obj)
    scene_viewmodel.selected_object = None

    assert inspector.lc.count() == 1
    widget = inspector.lc.itemAt(0).widget()
    assert "Selecione um objeto" in widget.text()


def test_rigidbody_properties_update(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel
) -> None:
    obj = GameObject("RBObject")
    rb = RigidBody()
    rb.mass = 1.0
    rb.gravity_scale = 1.0
    rb.is_kinematic = False
    obj.add_component(rb)

    scene_viewmodel.selected_object = obj
    assert hasattr(inspector, "rb_widget")
    
    rw = inspector.rb_widget
    assert rw.sb_mass.value() == 1.0
    
    rw.sb_mass.setValue(5.5)
    QApplication.processEvents()
    
    assert rb.mass == 5.5


def test_collider_properties_update(
    inspector: InspectorDock, scene_viewmodel: SceneViewModel
) -> None:
    obj = GameObject("ColObject")
    col = BoxCollider(width=100, height=200)
    obj.add_component(col)
    
    scene_viewmodel.selected_object = obj
    assert hasattr(inspector, "col_widget")
    
    cw = inspector.col_widget
    assert cw.sb_w.value() == 100
    
    cw.sb_w.setValue(300)
    QApplication.processEvents()
    
    assert col.width == 300
