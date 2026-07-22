import ast
from pathlib import Path


def _class_size(path: str, class_name: str) -> int:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    node = next(
        item for item in tree.body
        if isinstance(item, ast.ClassDef) and item.name == class_name
    )
    return node.end_lineno - node.lineno + 1


def test_viewport_runtime_has_cohesive_file_boundaries() -> None:
    facade = Path("editor/isolated_viewport.py").read_text(encoding="utf-8")
    session = Path("editor/runtime/viewport_session.py").read_text(encoding="utf-8")

    assert len(facade.splitlines()) < 120
    assert "class PlayScriptAPI" not in facade
    assert "def hydrate_logic_graphs(" not in facade
    assert "class PlayScriptAPI" not in session
    assert "def hydrate_logic_graphs(" not in session
    assert _class_size("editor/runtime/viewport_session.py", "ViewportSession") < 500
    assert _class_size("editor/runtime/viewport_script_api.py", "PlayScriptAPI") < 500


def test_exporter_packages_extracted_viewport_boundaries() -> None:
    exporter = Path("engine/build/project_exporter.py").read_text(encoding="utf-8")

    assert "viewport_asset_hydration.py" in exporter
    assert "viewport_script_api.py" in exporter
