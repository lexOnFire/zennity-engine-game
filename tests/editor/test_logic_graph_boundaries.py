import ast
from pathlib import Path


def test_logic_graph_editor_has_no_large_methods() -> None:
    source = Path("editor/widgets/logic_graph_editor.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    editor = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LogicGraphEditor"
    )
    sizes = {
        node.name: node.end_lineno - node.lineno + 1
        for node in editor.body if isinstance(node, ast.FunctionDef)
    }

    assert sizes["_build_ui"] <= 6
    assert max(sizes.values()) < 100


def test_logic_graph_ui_builder_is_a_separate_boundary() -> None:
    source = Path("editor/widgets/logic_graph/ui_builder.py")
    assert source.is_file()
    assert len(source.read_text(encoding="utf-8").splitlines()) < 400
