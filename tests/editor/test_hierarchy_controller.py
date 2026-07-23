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
    inspected = []
    status = _Status()
    host = SimpleNamespace(
        _objects_by_name={"Player": {}}, _runtime_objects_by_name={},
        _runtime_playing=False, _selected_name=None,
        _scene_controller=SimpleNamespace(select=selected.append),
        _update_inspector=inspected.append,
    )
    host.statusBar = lambda: status
    return host, selected, inspected, status


def test_hierarchy_selection_synchronizes_scene_and_inspector() -> None:
    host, selected, inspected, status = _host()

    HierarchyController(host, _Renderer()).select_item("Player")

    assert host._selected_name == "Player"
    assert selected == ["Player"]
    assert inspected == ["Player"]
    assert status.messages == ["Interface: Player selecionado"]


def test_hierarchy_selection_supports_runtime_only_objects() -> None:
    host, selected, inspected, status = _host()
    host._runtime_playing = True
    host._runtime_objects_by_name = {"Projectile": {}}

    HierarchyController(host, _Renderer()).select_item("Projectile")

    assert selected == ["Projectile"]
    assert inspected == ["Projectile"]
    assert status.messages == ["Runtime: Projectile selecionado"]


def test_hierarchy_ignores_unknown_items() -> None:
    host, selected, inspected, status = _host()

    HierarchyController(host, _Renderer()).select_item("Missing")

    assert host._selected_name is None
    assert selected == [] and inspected == [] and status.messages == []


def test_hierarchy_delegates_prefab_refresh_and_revert() -> None:
    host, *_ = _host()
    calls = []
    host._prefab_workspace = SimpleNamespace(
        refresh_instance=lambda name: calls.append(("refresh", name)) or True,
        revert_instance=lambda name: calls.append(("revert", name)) or True,
    )
    controller = HierarchyController(host, _Renderer())

    assert controller.refresh_prefab_instance("Player")
    assert controller.revert_prefab_instance("Player")
    assert calls == [("refresh", "Player"), ("revert", "Player")]
