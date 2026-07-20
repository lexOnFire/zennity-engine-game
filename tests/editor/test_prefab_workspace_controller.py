from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from editor.prefab_workspace_controller import PrefabWorkspaceController


class _SceneController:
    def __init__(self) -> None:
        self.snapshots = 0
        self.selected = []

    def publish_snapshot(self, _snapshot) -> None:
        self.snapshots += 1

    def select(self, name: str) -> None:
        self.selected.append(name)


def _host():
    obj = {"id": "source", "name": "Crate", "x": 2.0, "y": 3.0, "w": 32.0, "h": 16.0}
    host = SimpleNamespace(
        _selected_name="Crate",
        _objects_by_name={"Crate": obj},
        _scene_snapshot=[obj],
        _scene_controller=_SceneController(),
        history=0,
        logs=[],
        refreshed=[],
    )
    host._record_history = lambda: setattr(host, "history", host.history + 1)
    host._unique_name = lambda name: f"{name} 2"
    host._refresh_hierarchy = lambda: None
    host._update_inspector = lambda name: host.refreshed.append(name)
    host._log = lambda level, message: host.logs.append((level, message))
    return host


def test_prefab_payload_is_portable_and_does_not_persist_scene_id() -> None:
    payload = PrefabWorkspaceController.build_payload(
        {"id": "scene-only", "name": "Crate", "w": 32, "h": 16, "tag": "Prop"},
        "Crate",
    )

    assert payload["format_version"] == 2
    assert "id" not in payload["object"]
    assert {item["name"] for item in payload["exposed_properties"]} >= {"width", "height", "tag"}


def test_prefab_instantiation_creates_independent_scene_object(tmp_path: Path) -> None:
    prefab_dir = tmp_path / "Assets" / "Prefabs"
    prefab_dir.mkdir(parents=True)
    path = prefab_dir / "Crate.zprefab"
    payload = PrefabWorkspaceController.build_payload(
        {"name": "Crate", "x": 2.0, "y": 3.0, "w": 32.0, "h": 16.0},
        "Crate",
    )
    path.write_text(json.dumps(payload), encoding="utf-8")
    host = _host()

    PrefabWorkspaceController(host, tmp_path).instantiate(path)

    created = host._scene_snapshot[-1]
    assert created["name"] == "Crate 2"
    assert created["id"] != "source"
    assert (created["x"], created["y"]) == (18.0, 19.0)
    assert host.history == 1
    assert host._scene_controller.snapshots == 1
    assert host._scene_controller.selected == ["Crate 2"]


def test_prefab_instantiation_rejects_legacy_runtime_shape(tmp_path: Path) -> None:
    path = tmp_path / "Legacy.zprefab"
    path.write_text(json.dumps({"format_version": 2, "object": {"name": "Old", "transform": {}}}), encoding="utf-8")
    host = _host()

    PrefabWorkspaceController(host, tmp_path).instantiate(path)

    assert host.history == 0
    assert len(host._scene_snapshot) == 1
    assert host.logs[-1][0] == "ERROR"
