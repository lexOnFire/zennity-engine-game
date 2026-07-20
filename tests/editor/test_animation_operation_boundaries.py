import ast
from pathlib import Path


def _class_size(path: str, name: str) -> int:
    source = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == name)
    return node.end_lineno - node.lineno + 1


def test_animation_operations_are_split_by_responsibility() -> None:
    assert _class_size("editor/animation_asset_operations.py", "AnimationAssetOperations") < 500
    assert _class_size("editor/animation_preview_operations.py", "AnimationPreviewOperations") < 500
    assert _class_size("editor/animation_workspace_operations.py", "AnimationWorkspaceOperations") < 20


def test_animation_operation_methods_are_bounded() -> None:
    for path in ("editor/animation_asset_operations.py", "editor/animation_preview_operations.py"):
        source = Path(path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        sizes = [
            node.end_lineno - node.lineno + 1
            for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        ]
        assert sizes and max(sizes) < 100
