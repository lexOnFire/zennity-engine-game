import ast
from pathlib import Path


def _class_size(path: str) -> int:
    source = Path(path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    node = next(item for item in tree.body if isinstance(item, ast.ClassDef))
    return node.end_lineno - node.lineno + 1


def test_logic_graph_editor_responsibilities_are_bounded() -> None:
    assert _class_size("editor/widgets/logic_graph_editor.py") < 500
    for path in (
        "editor/widgets/logic_graph/editor_mixins/palette_mixin.py",
        "editor/widgets/logic_graph/editor_mixins/runtime_view_mixin.py",
        "editor/widgets/logic_graph/editor_mixins/canvas_mixin.py",
        "editor/widgets/logic_graph/editor_mixins/properties_mixin.py",
        "editor/widgets/logic_graph/editor_mixins/persistence_mixin.py",
    ):
        assert _class_size(path) < 500
