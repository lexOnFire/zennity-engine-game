from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from editor.script_workspace_controller import ScriptWorkspaceController
from editor.script_templates import build_isolated_script_template


class _SceneController:
    def __init__(self) -> None:
        self.snapshots = 0
        self.selected: list[str] = []

    def publish_snapshot(self, _snapshot) -> None:
        self.snapshots += 1

    def select(self, name: str) -> None:
        self.selected.append(name)


class _StatusBar:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, message: str) -> None:
        self.messages.append(message)


class _Host:
    def __init__(self) -> None:
        self._play_session = SimpleNamespace(is_running=False)
        self._scene_snapshot = [{"name": "Player"}]
        self._objects_by_name = {"Player": self._scene_snapshot[0]}
        self._selected_name = "Player"
        self._component_expanded = {}
        self._updating_inspector = False
        self._scene_controller = _SceneController()
        self.history = 0
        self.refreshed: list[str] = []
        self.logs: list[tuple[str, str]] = []
        self.status = _StatusBar()

    def statusBar(self):
        return self.status

    def _record_history(self) -> None:
        self.history += 1

    def _update_inspector(self, name: str) -> None:
        self.refreshed.append(name)

    def _log(self, level: str, message: str) -> None:
        self.logs.append((level, message))


def test_script_workspace_discovers_and_binds_scripts(tmp_path: Path) -> None:
    scripts = tmp_path / "Assets" / "Scripts"
    scripts.mkdir(parents=True)
    script = scripts / "movement.py"
    script.write_text(build_isolated_script_template("movement"), encoding="utf-8")
    (scripts / "__init__.py").write_text("", encoding="utf-8")
    host = _Host()
    workspace = ScriptWorkspaceController(host, tmp_path)

    assert workspace.available_scripts() == [script]
    workspace.attach("Player", script)

    assert host._objects_by_name["Player"]["scripts"] == ["Assets/Scripts/movement.py"]
    assert host.history == 1
    assert host._scene_controller.snapshots == 1
    assert host.refreshed == ["Player"]


def test_script_workspace_updates_and_removes_binding(tmp_path: Path) -> None:
    host = _Host()
    host._objects_by_name["Player"]["scripts"] = ["Assets/Scripts/old.py"]
    workspace = ScriptWorkspaceController(host, tmp_path)

    workspace.change("Assets/Scripts/old.py", "Assets/Scripts/new.py")
    workspace.update_property("Assets/Scripts/new.py", "speed", 5.0)
    workspace.remove("Assets/Scripts/new.py")

    player = host._objects_by_name["Player"]
    assert "scripts" not in player
    assert player["script_properties"]["Assets/Scripts/new.py"]["speed"] == 5.0
    assert host.history == 3
    assert host._scene_controller.snapshots == 3


def test_script_workspace_does_not_attach_during_play(tmp_path: Path) -> None:
    script = tmp_path / "blocked.py"
    script.write_text(build_isolated_script_template("blocked"), encoding="utf-8")
    host = _Host()
    host._play_session.is_running = True

    ScriptWorkspaceController(host, tmp_path).attach("Player", script)

    assert "scripts" not in host._objects_by_name["Player"]
    assert host.history == 0
