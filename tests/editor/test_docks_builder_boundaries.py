import ast
from pathlib import Path


def _function_sizes(path: str) -> dict[str, int]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    return {
        node.name: node.end_lineno - node.lineno + 1
        for node in tree.body if isinstance(node, ast.FunctionDef)
    }


def test_dock_composition_root_stays_small() -> None:
    source = Path("editor/ui/docks_builder.py").read_text(encoding="utf-8")
    assert len(source.splitlines()) < 50
    assert "build_navigation_panels(window)" in source
    assert "build_inspector_dock(window)" in source
    assert "build_bottom_panels(window, left)" in source


def test_inspector_sections_have_bounded_complexity() -> None:
    sizes = _function_sizes("editor/ui/inspector_builder.py")
    assert sizes
    assert max(sizes.values()) < 150
