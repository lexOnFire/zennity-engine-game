from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from editor.project_workflow_controller import ProjectWorkflowController


class _Persistence:
    def __init__(self) -> None:
        self.scopes = []

    def collect_logic_variables(self, scope: str):
        self.scopes.append(scope)
        return {"score": {"type": "number", "value": 2}}

    def load(self, path: Path):
        return ({"scene_name": path.stem}, [{"name": "Player", "id": "p1"}], True)


class _SceneBridge:
    def __init__(self) -> None:
        self.snapshots = []

    def publish_snapshot(self, snapshot) -> None:
        self.snapshots.append(snapshot)


class _Status:
    def __init__(self) -> None:
        self.messages = []

    def showMessage(self, message: str) -> None:
        self.messages.append(message)


def _host():
    status = _Status()
    host = SimpleNamespace(
        _scene_persistence=_Persistence(), _scene_snapshot=[], _objects_by_name={},
        _scene_document=None, _current_scene_path=None, _selected_name="Old",
        _scene_controller=_SceneBridge(), history=0, refreshed=0, logs=[],
    )
    host._record_history = lambda: setattr(host, "history", host.history + 1)
    host._refresh_hierarchy = lambda: setattr(host, "refreshed", host.refreshed + 1)
    host._log = lambda level, message: host.logs.append((level, message))
    host.statusBar = lambda: status
    return host, status


def test_project_workflow_delegates_logic_variable_collection(tmp_path: Path) -> None:
    host, _ = _host()

    variables = ProjectWorkflowController(host, tmp_path).collect_logic_variables("scene")

    assert variables["score"]["value"] == 2
    assert host._scene_persistence.scopes == ["scene"]


def test_project_workflow_loads_typed_scene_and_publishes_snapshot(tmp_path: Path) -> None:
    host, status = _host()
    scene = tmp_path / "Level.zscene"

    loaded = ProjectWorkflowController(host, tmp_path).load_scene(scene)

    assert loaded is True
    assert host._objects_by_name["Player"]["id"] == "p1"
    assert host._scene_document == {"scene_name": "Level"}
    assert host._current_scene_path == scene
    assert host._selected_name is None
    assert host.history == 1
    assert host._scene_controller.snapshots == [[{"name": "Player", "id": "p1"}]]
    assert status.messages == [f"Cena aberta: {scene}"]
