import ast
from pathlib import Path


def test_center_workspace_builders_are_bounded() -> None:
    source = Path("editor/ui/workspace_builder.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    sizes = {
        node.name: node.end_lineno - node.lineno + 1
        for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    assert sizes["build_center_workspace"] < 15
    assert max(sizes.values()) < 100
