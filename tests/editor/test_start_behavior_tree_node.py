import os
from pathlib import Path
from engine.logic.graph_asset import NODE_DEFINITIONS
from editor.widgets.logic_asset_picker import ASSET_KINDS
from editor.runtime.viewport_logic_api import PlayLogicAPI


def test_start_behavior_tree_node_definition_and_asset_kind_exist() -> None:
    assert "start_behavior_tree" in NODE_DEFINITIONS
    node_def = NODE_DEFINITIONS["start_behavior_tree"]
    assert node_def["category"] == "Action"
    assert node_def["properties"]["path"] == ""

    assert "behavior" in ASSET_KINDS
    label, extensions = ASSET_KINDS["behavior"]
    assert label == "Behavior Tree"
    assert ".zbehavior" in extensions


def test_play_logic_api_start_behavior_tree_updates_object_behavior() -> None:
    obj = {"name": "Comida", "tag": "Food"}
    api = PlayLogicAPI("Comida", obj, [])
    
    res = api.start_behavior_tree("Assets/Behaviors/patrol_comida.zbehavior")
    assert obj["behavior"]["controller_path"] == "Assets/Behaviors/patrol_comida.zbehavior"


def test_start_behavior_tree_uses_linked_asset_and_registers_runner(tmp_path) -> None:
    asset = tmp_path / "Assets" / "Behaviors" / "enemy.zbehavior"
    asset.parent.mkdir(parents=True)
    asset.write_text(
        '{"format":"zennity.generic_graph","version":1,"category":"Behavior Tree","nodes":[],"edges":[]}',
        encoding="utf-8",
    )
    obj = {"name": "Enemy", "behavior": {"controller_path": "Assets/Behaviors/enemy.zbehavior"}}
    runners = {}
    api = PlayLogicAPI(
        "Enemy", obj, None, {"Enemy": obj}, behavior_runners=runners,
        project_root=tmp_path,
    )

    assert api.start_behavior_tree("") is True
    first = runners["Enemy"]
    assert api.start_behavior_tree("") is True
    assert runners["Enemy"] is first
