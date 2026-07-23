import pytest
import numpy as np
from PySide6.QtWidgets import QApplication
from editor.widgets.inspector_dock import InspectorDock
from editor.viewmodels.scene_viewmodel import SceneViewModel
from editor.models.scene_model import SceneModel
from engine.game_object import GameObject
from editor.runtime.command_manager import CommandManager

@pytest.fixture
def command_manager() -> CommandManager:
    return CommandManager()

@pytest.fixture
def scene_model() -> SceneModel:
    return SceneModel()

@pytest.fixture
def scene_viewmodel(scene_model: SceneModel) -> SceneViewModel:
    return SceneViewModel(model=scene_model)

@pytest.fixture
def qapp_instance():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def inspector(qapp_instance, scene_viewmodel: SceneViewModel) -> InspectorDock:
    dock = InspectorDock()
    dock.set_viewmodel(scene_viewmodel)
    return dock

def test_inspector_empty_state_without_selection(inspector: InspectorDock) -> None:
    assert inspector.renderer_label.text() == "Components\n  Sem componentes"

def test_inspector_populates_fields_on_selection(inspector: InspectorDock, scene_viewmodel: SceneViewModel) -> None:
    obj = GameObject("Target")
    obj.transform.position = np.array([12.5, 45.0, 0.0], dtype=np.float32)
    obj.transform.rotation = np.array([0.0, 0.0, 90.0], dtype=np.float32)
    obj.transform.scale = np.array([2.0, 2.5, 1.0], dtype=np.float32)
    scene_viewmodel.selected_object = obj
    inspector.load_object(obj)
    assert inspector.object_name.text() == "Target"
    text = inspector.transform_label.text()
    assert "12.5" in text
    assert "45.0" in text

def test_inspector_selection_switch_updates_fields(inspector: InspectorDock, scene_viewmodel: SceneViewModel) -> None:
    obj1 = GameObject("Obj1")
    obj2 = GameObject("Obj2")
    scene_viewmodel.selected_object = obj1
    inspector.load_object(obj1)
    assert inspector.object_name.text() == "Obj1"
    scene_viewmodel.selected_object = obj2
    inspector.load_object(obj2)
    assert inspector.object_name.text() == "Obj2"

def test_inspector_deleted_object_does_not_crash(inspector: InspectorDock, scene_viewmodel: SceneViewModel, scene_model: SceneModel) -> None:
    obj = GameObject("Deletable")
    scene_model.add_object(obj)
    scene_viewmodel.selected_object = obj
    scene_model.remove_object(obj)
    scene_viewmodel.selected_object = None
    assert inspector.renderer_label.text() == "Components\n  Sem componentes"
