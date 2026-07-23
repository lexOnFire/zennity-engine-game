from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QFileDialog

from editor.project_workflow_controller import ProjectWorkflowController
from editor.runtime.diagnostics import DiagnosticCenter


class _Persistence:
    def __init__(self) -> None:
        self.scopes = []

    def collect_logic_variables(self, scope: str):
        self.scopes.append(scope)
        return {"score": {"type": "number", "value": 2}}

    def load(self, path: Path):
        return ({"scene_name": path.stem}, [{"name": "Player", "id": "p1"}], True)

    def save(self, path: Path, snapshot, document):
        self.saved = (path, snapshot, document)
        return {"scene_name": path.stem}


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
        _diagnostics=DiagnosticCenter(),
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


def test_project_workflow_syncs_prefab_overrides_before_save(
    tmp_path: Path, monkeypatch,
) -> None:
    host, _ = _host()
    sync_calls = []
    host._prefab_workspace = SimpleNamespace(
        sync_scene_instances=lambda: sync_calls.append(True)
    )
    scene = tmp_path / "Level.zscene"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(scene), ""),
    )

    saved = ProjectWorkflowController(host, tmp_path).save_scene()

    assert saved is True
    assert sync_calls == [True]
    assert host._scene_persistence.saved[0] == scene


def test_project_workflow_reports_actionable_load_failure(tmp_path: Path) -> None:
    host, status = _host()
    scene = tmp_path / "Broken.zscene"
    host._scene_persistence.load = lambda _path: (_ for _ in ()).throw(
        ValueError("JSON inválido")
    )

    assert ProjectWorkflowController(host, tmp_path).load_scene(scene) is False
    diagnostic = host._diagnostics.records[-1]
    assert diagnostic.title == "Falha ao abrir cena"
    assert diagnostic.path == scene
    assert "restaure uma cópia válida" in diagnostic.action
    assert host.logs[-1][0] == "ERROR"
    assert status.messages[-1].startswith("Falha ao abrir cena.")
