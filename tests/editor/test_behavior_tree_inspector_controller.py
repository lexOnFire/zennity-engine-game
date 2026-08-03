from pathlib import Path
from types import SimpleNamespace

from editor.behavior_tree_inspector_controller import BehaviorTreeInspectorController


class _Selection:
    def __init__(self, obj):
        self.obj = obj
        self.published = 0
        self.inspected = []

    def selected_scene_object(self):
        return "Enemy", self.obj

    def publish_scene(self):
        self.published += 1

    def refresh_inspector(self, name):
        self.inspected.append(name)


def _host(obj):
    selection = _Selection(obj)
    host = SimpleNamespace(
        _selection=selection,
        _objects_by_name={"Enemy": obj},
        _scene_document={"scene_name": "Main", "objects": []},
        _current_scene_path=Path("Main.zscene"),
        _dock_visual_scripting=None,
        history=0,
        logs=[],
    )
    host._record_history = lambda: setattr(host, "history", host.history + 1)
    host._log = lambda level, message: host.logs.append((level, message))
    return host


def test_link_persists_object_and_scene_workspace(tmp_path) -> None:
    asset = tmp_path / "Assets" / "Behaviors" / "Enemy.zbehavior"
    asset.parent.mkdir(parents=True)
    asset.write_text("{}", encoding="utf-8")
    obj = {"name": "Enemy"}
    host = _host(obj)
    controller = BehaviorTreeInspectorController(host, tmp_path)
    controller._open_in_editor = lambda _path: None

    controller._link("Enemy", obj, asset)

    relative = "Assets/Behaviors/Enemy.zbehavior"
    assert obj["behavior"] == {"controller_path": relative, "auto_start": False}
    assert host._scene_document["visual_logic_workspace"]["behavior_tree"] == relative
    assert host.history == 1
    assert host._selection.published == 1


def test_unlink_clears_object_and_workspace(tmp_path) -> None:
    path = "Assets/Behaviors/Enemy.zbehavior"
    obj = {"name": "Enemy", "behavior": {"controller_path": path}}
    host = _host(obj)
    host._scene_document["visual_logic_workspace"] = {"behavior_tree": path}

    BehaviorTreeInspectorController(host, tmp_path).unlink()

    assert "behavior" not in obj
    assert "behavior_tree" not in host._scene_document["visual_logic_workspace"]
    assert host._selection.published == 1
