from engine.logic.graph_asset import validate_logic_graph
from engine.logic.graph_templates import GRAPH_TEMPLATES, build_logic_template


def test_every_guided_template_builds_a_valid_canonical_document():
    assert {"empty", "movement_2d", "platformer", "enemy", "interaction", "ui"} <= set(GRAPH_TEMPLATES)
    for template_id in GRAPH_TEMPLATES:
        graph = build_logic_template(template_id, f"Template_{template_id}")
        assert graph["format"] == "zennity.logic_graph"
        assert graph["name"] == f"Template_{template_id}"
        assert isinstance(graph["nodes"], list)
        assert isinstance(graph["edges"], list)
        assert not [
            issue for issue in validate_logic_graph(graph)
            if issue.get("level") == "error"
        ]


def test_non_empty_templates_include_connected_nodes():
    for template_id in set(GRAPH_TEMPLATES) - {"empty"}:
        graph = build_logic_template(template_id)
        assert len(graph["nodes"]) >= 2
        assert graph["edges"]
