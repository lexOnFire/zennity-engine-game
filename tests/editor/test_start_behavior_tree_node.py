import os
from pathlib import Path
from engine.logic.graph_asset import NODE_DEFINITIONS
from editor.widgets.logic_asset_picker import ASSET_KINDS
from editor.runtime.viewport_logic_api import PlayLogicAPI


def test_start_behavior_tree_node_definition_and_asset_kind_exist() -> None:
    assert "start_behavior_tree" in NODE_DEFINITIONS
    node_def = NODE_DEFINITIONS["start_behavior_tree"]
    assert node_def["category"] == "Action"
    assert node_def["properties"]["path"] == "Assets/Behaviors/patrol_comida.zbehavior"

    assert "behavior" in ASSET_KINDS
    label, extensions = ASSET_KINDS["behavior"]
    assert label == "Behavior Tree"
    assert ".zbehavior" in extensions


def test_play_logic_api_start_behavior_tree_updates_object_behavior() -> None:
    obj = {"name": "Comida", "tag": "Food"}
    api = PlayLogicAPI("Comida", obj, [])
    
    res = api.start_behavior_tree("Assets/Behaviors/patrol_comida.zbehavior")
    assert obj["behavior"]["controller_path"] == "Assets/Behaviors/patrol_comida.zbehavior"
