from engine.logic.graph_asset import create_logic_node, NODE_DEFINITIONS


def test_if_else_and_compare_nodes_have_editable_properties() -> None:
    assert NODE_DEFINITIONS["if_else"]["properties"] == {"condition": False}
    assert NODE_DEFINITIONS["compare_number"]["properties"] == {"operator": ">", "value": 0.0}
    assert NODE_DEFINITIONS["compare_text"]["properties"] == {"operator": "==", "value": ""}

    if_node = create_logic_node("if_else")
    assert if_node["properties"]["condition"] is False

    cmp_num = create_logic_node("compare_number")
    assert cmp_num["properties"]["operator"] == ">"
    assert cmp_num["properties"]["value"] == 0.0

    cmp_txt = create_logic_node("compare_text")
    assert cmp_txt["properties"]["operator"] == "=="
    assert cmp_txt["properties"]["value"] == ""
