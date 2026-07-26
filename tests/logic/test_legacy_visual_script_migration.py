from engine.logic.graph_asset import load_logic_graph
from engine.logic.legacy_visual_script import migrate_visual_script_graph


def _legacy_document():
    return {
        "format": "zennity.visual_script",
        "name": "Legacy",
        "nodes": [
            {"id": "start", "type": "vs.event_on_start", "position": [0, 0]},
            {
                "id": "log",
                "type": "vs.log_message",
                "position": [250, 0],
                "inputs": {"message": "migrated"},
            },
        ],
        "connections": [{
            "id": "edge",
            "source_node": "start",
            "source_port": "out",
            "target_node": "log",
            "target_port": "in",
        }],
    }


def test_migrates_legacy_ids_ports_and_properties():
    graph = migrate_visual_script_graph(_legacy_document())
    assert [node["type"] for node in graph["nodes"]] == ["event_start", "log_message"]
    assert graph["nodes"][1]["properties"]["message"] == "migrated"
    assert graph["edges"][0]["from_port"] == "next"
    assert graph["edges"][0]["kind"] == "flow"


def test_loader_accepts_legacy_extension_and_document(tmp_path):
    path = tmp_path / "Legacy.zscriptgraph"
    import json
    path.write_text(json.dumps(_legacy_document()), encoding="utf-8")
    graph = load_logic_graph(path)
    assert graph["format"] == "zennity.logic_graph"
    assert graph["editor"]["migrated_from"] == "zennity.visual_script"
