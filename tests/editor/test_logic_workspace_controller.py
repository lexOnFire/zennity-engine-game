from __future__ import annotations

from pathlib import Path
from queue import SimpleQueue
from types import SimpleNamespace

from editor.logic_workspace_controller import LogicWorkspaceController


class _Repository:
    def __init__(self) -> None:
        self.invalidated: list[Path] = []

    def assets(self):
        return []

    def for_object(self, name, obj):
        return [(Path("player.zlogic"), {"target": {"value": name}})] if obj else []

    def invalidate(self, path: Path) -> None:
        self.invalidated.append(path)


class _LogicWorkspace:
    def __init__(self, path: Path) -> None:
        self.current_path = path

    def graph_data(self) -> dict:
        return {
            "debug": {
                "breakpoints": ["node-1"],
                "breakpoint_conditions": {"node-1": "score > 2"},
                "watches": ["score"],
            },
            "variables": {"score": {"value": 3}},
        }


def _host(root: Path):
    return SimpleNamespace(
        _selected_name="Player",
        _objects_by_name={"Player": {"name": "Player"}},
        _logic_assets_repository=_Repository(),
        _commands=SimpleQueue(),
        logic_workspace=_LogicWorkspace(root / "Assets" / "Logic" / "player.zlogic"),
        logs=[],
        _log=lambda level, message: None,
    )


def test_logic_workspace_builds_portable_debug_command(tmp_path: Path) -> None:
    host = _host(tmp_path)
    controller = LogicWorkspaceController(host, tmp_path)

    controller.send_debug_command("continue")

    command = host._commands.get_nowait()
    assert command["type"] == "logic_debug_command"
    assert command["command"] == "continue"
    assert command["graph"] == "Assets/Logic/player.zlogic"
    assert command["breakpoints"] == ["node-1"]
    assert command["variables"] == {"score": {"value": 3}}


def test_logic_workspace_resolves_object_bindings(tmp_path: Path) -> None:
    host = _host(tmp_path)
    controller = LogicWorkspaceController(host, tmp_path)

    assert controller.assets() == []
    assert controller.graphs_for_object("Player")[0][1]["target"]["value"] == "Player"
    assert controller.graphs_for_object("Missing") == []


def test_logic_workspace_warns_when_debug_asset_is_missing(tmp_path: Path) -> None:
    host = _host(tmp_path)
    host.logic_workspace.current_path = None
    messages = []
    host._log = lambda level, message: messages.append((level, message))

    LogicWorkspaceController(host, tmp_path).send_debug_command("step")

    assert host._commands.empty()
    assert messages == [("WARNING", "Abra ou salve um Logic Graph antes de depurar")]
