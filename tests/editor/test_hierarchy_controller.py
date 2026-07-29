from __future__ import annotations

from types import SimpleNamespace

from editor.hierarchy_controller import HierarchyController


class _Renderer:
    def __init__(self) -> None:
        self.refreshes = 0

    def item_name(self, item) -> str:
        return str(item)

    def refresh(self, *, force=False) -> bool:
        self.refreshes += 1
        return bool(force)


class _Status:
    def __init__(self) -> None:
        self.messages = []

    def showMessage(self, message: str) -> None:
        self.messages.append(message)


def _host():
    selected = []
    action_selected = []
    status = _Status()
    selection = SimpleNamespace(
        select=lambda name, source="Interface": selected.append((name, source)) or True,
        select_for_action=lambda name: action_selected.append(name) or True,
    )
    scene_objects = SimpleNamespace(
        duplicated=0,
        duplicate_selected=lambda: setattr(scene_objects, "duplicated", scene_objects.duplicated + 1),
    )
    host = SimpleNamespace(
        _objects_by_name={"Player": {}}, _runtime_objects_by_name={},
        _runtime_playing=False, _selected_name=None,
        _selection=selection, _scene_objects=scene_objects,
    )
    host.statusBar = lambda: status
    return host, selected, action_selected, status


def test_hierarchy_selection_synchronizes_scene_and_inspector() -> None:
    host, selected, _action_selected, _status = _host()

    HierarchyController(host, _Renderer()).select_item("Player")

    assert selected == [("Player", "Interface")]


def test_hierarchy_selection_supports_runtime_only_objects() -> None:
    host, selected, _action_selected, _status = _host()
    host._runtime_playing = True
    host._runtime_objects_by_name = {"Projectile": {}}

    HierarchyController(host, _Renderer()).select_item("Projectile")

    assert selected == [("Projectile", "Runtime")]


def test_hierarchy_ignores_unknown_items() -> None:
    host, selected, action_selected, status = _host()

    HierarchyController(host, _Renderer()).select_item("Missing")

    assert host._selected_name is None
    assert selected == [] and action_selected == [] and status.messages == []


def test_hierarchy_action_selection_delegates_before_duplicate() -> None:
    host, _selected, action_selected, _status = _host()

    HierarchyController(host, _Renderer()).select_and_duplicate("Player")

    assert action_selected == ["Player"]
    assert host._scene_objects.duplicated == 1
