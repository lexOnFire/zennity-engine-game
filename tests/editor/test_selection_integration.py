from __future__ import annotations

from editor.core.event_bus import EventBus, EVENT_SELECTION_CHANGED
from editor.models.scene_model import SceneModel
from editor.runtime.selection_manager import SelectionManager
from editor.viewmodels.scene_viewmodel import SceneViewModel


def test_viewmodel_selection_setter_delegates_to_selection_manager(simple_go) -> None:
    manager = SelectionManager()
    viewmodel = SceneViewModel(SceneModel(), selection_manager=manager)

    viewmodel.selected_object = simple_go

    assert manager.selected is simple_go
    assert viewmodel.selected_object is simple_go


def test_selection_manager_updates_viewmodel_signal(simple_go) -> None:
    manager = SelectionManager()
    viewmodel = SceneViewModel(SceneModel(), selection_manager=manager)
    calls = []

    viewmodel.selection_changed.connect(calls.append)
    manager.set_selected(simple_go)

    assert viewmodel.selected_object is simple_go
    assert calls == [simple_go]


def test_viewmodel_keeps_event_bus_compatibility(simple_go) -> None:
    EventBus.clear(EVENT_SELECTION_CHANGED)
    manager = SelectionManager()
    viewmodel = SceneViewModel(SceneModel(), selection_manager=manager)
    calls = []
    EventBus.subscribe(EVENT_SELECTION_CHANGED, lambda obj: calls.append(obj))

    manager.set_selected(simple_go)

    assert calls == [simple_go]
    EventBus.clear(EVENT_SELECTION_CHANGED)
