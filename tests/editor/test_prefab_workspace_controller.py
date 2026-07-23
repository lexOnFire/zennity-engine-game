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
    assert created["prefab_source"] == "Assets/Prefabs/Crate.zprefab"
    assert created["prefab_guid"]
    assert set(created["prefab_overrides"]["values"]) >= {"/x", "/y"}
    assert "/name" not in created["prefab_overrides"]["values"]


def test_prefab_instantiation_rejects_legacy_runtime_shape(tmp_path: Path) -> None:
    path = tmp_path / "Legacy.zprefab"
    path.write_text(json.dumps({"format_version": 2, "object": {"name": "Old", "transform": {}}}), encoding="utf-8")
    host = _host()

    PrefabWorkspaceController(host, tmp_path).instantiate(path)

    assert host.history == 0
    assert len(host._scene_snapshot) == 1
    assert host.logs[-1][0] == "ERROR"


def test_scene_instance_overrides_sync_refresh_and_revert(tmp_path: Path) -> None:
    prefab_dir = tmp_path / "Assets" / "Prefabs"
    prefab_dir.mkdir(parents=True)
    path = prefab_dir / "Crate.zprefab"
    payload = PrefabWorkspaceController.build_payload(
        {"name": "Crate", "x": 2.0, "y": 3.0, "w": 32.0, "h": 16.0},
        "Crate",
    )
    path.write_text(json.dumps(payload), encoding="utf-8")
    host = _host()
    controller = PrefabWorkspaceController(host, tmp_path)
    controller.instantiate(path)
    created = host._scene_snapshot[-1]
    created["w"] = 80.0
    controller.sync_scene_instances()

    payload["object"]["h"] = 40.0
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert controller.refresh_instance(created["name"])
    refreshed = host._scene_snapshot[-1]

    assert refreshed["w"] == 80.0
    assert refreshed["h"] == 40.0
    assert controller.revert_instance(refreshed["name"])
    reverted = host._scene_snapshot[-1]
    assert reverted["w"] == 32.0
    assert reverted["h"] == 40.0
    assert reverted["prefab_overrides"] == {"values": {}, "removed": []}
