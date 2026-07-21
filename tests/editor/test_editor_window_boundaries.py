import ast
from pathlib import Path


def _class_size(path: str, name: str) -> int:
    source = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(item for item in tree.body if isinstance(item, ast.ClassDef) and item.name == name)
    return node.end_lineno - node.lineno + 1


def test_official_editor_window_stays_below_release_budget() -> None:
    assert _class_size("editor/isolated_editor_main.py", "IsolatedEditorWindow") < 400
