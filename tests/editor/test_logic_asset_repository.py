from engine.logic.graph_asset import default_logic_graph, load_logic_graph, save_logic_graph
from editor.controllers.logic_assets import LogicAssetRepository


def test_repository_renames_only_semantic_object_references(tmp_path) -> None:
    logic_dir = tmp_path / "Assets" / "Logic"
    logic_dir.mkdir(parents=True)
    path = logic_dir / "PlayerLogic.zlogic"
    graph = default_logic_graph("PlayerLogic")
    graph["target"] = {"type": "name", "value": "game_obj"}
    graph["nodes"] = [{
        "id": "node",
        "type": "custom",
        "properties": {
            "target_name": "game_obj",
            "target": "game_obj",
            "label": "game_obj",
            "typed": {"type": "object", "default": "game_obj"},
        },
    }]
    save_logic_graph(path, graph)

    changed = LogicAssetRepository(tmp_path).rename_object_references(
        "game_obj", "player_ship"
    )
    updated = load_logic_graph(path)

    assert changed == [path.resolve()]
    assert updated["target"]["value"] == "player_ship"
    properties = updated["nodes"][0]["properties"]
    assert properties["target_name"] == "player_ship"
    assert properties["typed"]["default"] == "player_ship"
    assert properties["target"] == "game_obj"
    assert properties["label"] == "game_obj"


def test_repository_does_not_change_tag_bound_graph(tmp_path) -> None:
    logic_dir = tmp_path / "Assets" / "Logic"
    logic_dir.mkdir(parents=True)
    path = logic_dir / "Tagged.zlogic"
    graph = default_logic_graph("Tagged")
    graph["target"] = {"type": "tag", "value": "game_obj"}
    save_logic_graph(path, graph)

    assert LogicAssetRepository(tmp_path).rename_object_references(
        "game_obj", "player_ship"
    ) == []
    assert load_logic_graph(path)["target"]["value"] == "game_obj"
