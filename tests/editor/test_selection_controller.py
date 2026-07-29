from types import SimpleNamespace

from editor.controllers.selection_controller import EditorSelectionController


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
        _objects_by_name={"Player": {}},
        _runtime_objects_by_name={},
        _runtime_playing=False,
        _selected_name=None,
        _scene_controller=SimpleNamespace(select=selected.append),
        _update_inspector=inspected.append,
    )
    host.statusBar = lambda: status
    return host, selected, inspected, status


def test_selection_controller_selects_scene_object_and_updates_inspector() -> None:
    host, selected, inspected, status = _host()

    result = EditorSelectionController(host).select("Player")

    assert result is True
    assert host._selected_name == "Player"
    assert selected == ["Player"]
    assert inspected == ["Player"]
    assert status.messages == ["Interface: Player selecionado"]


def test_selection_controller_selects_runtime_object_with_source_label() -> None:
    host, selected, inspected, status = _host()
    host._runtime_playing = True
    host._runtime_objects_by_name = {"Projectile": {}}

    result = EditorSelectionController(host).select("Projectile", source="Runtime")

    assert result is True
    assert host._selected_name == "Projectile"
    assert selected == ["Projectile"]
    assert inspected == ["Projectile"]
    assert status.messages == ["Runtime: Projectile selecionado"]


def test_selection_controller_ignores_unknown_selection() -> None:
    host, selected, inspected, status = _host()

    result = EditorSelectionController(host).select("Missing")

    assert result is False
    assert host._selected_name is None
    assert selected == []
    assert inspected == []
    assert status.messages == []


def test_selection_controller_select_for_action_only_accepts_scene_objects() -> None:
    host, _selected, _inspected, _status = _host()
    controller = EditorSelectionController(host)

    assert controller.select_for_action("Player") is True
    assert host._selected_name == "Player"
    assert controller.select_for_action("Missing") is False
    assert host._selected_name == "Player"


def test_selection_controller_returns_selected_scene_object() -> None:
    host, _selected, _inspected, _status = _host()
    host._selected_name = "Player"

    selected = EditorSelectionController(host).selected_scene_object()

    assert selected == ("Player", host._objects_by_name["Player"])


def test_selection_controller_blocks_selected_object_while_updating_inspector() -> None:
    host, _selected, _inspected, _status = _host()
    host._selected_name = "Player"
    host._updating_inspector = True

    assert EditorSelectionController(host).selected_scene_object() is None


def test_selection_controller_publishes_and_refreshes_selected_change() -> None:
    host, selected, inspected, _status = _host()
    published = []
    host._scene_snapshot = [{"name": "Player"}]
    host._selected_name = "Player"
    host._scene_controller.publish_snapshot = published.append

    EditorSelectionController(host).publish_selected_change(select=True, inspect=True)

    assert published == [host._scene_snapshot]
    assert selected == ["Player"]
    assert inspected == ["Player"]
