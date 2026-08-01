"""Architecture gates for the split Logic Graph editor."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIXINS = ROOT / "editor" / "widgets" / "logic_graph" / "editor_mixins"


def test_mixins_do_not_import_concrete_logic_graph_editor() -> None:
    offenders: list[str] = []
    for path in sorted(MIXINS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "editor.widgets.logic_graph_editor":
                offenders.append(path.name)
            elif isinstance(node, ast.Import) and any(
                alias.name == "editor.widgets.logic_graph_editor" for alias in node.names
            ):
                offenders.append(path.name)
    assert offenders == []


def test_mixins_use_package_absolute_imports_for_shared_graph_modules() -> None:
    offenders = [
        path.name
        for path in sorted(MIXINS.glob("*.py"))
        if "from .logic_graph." in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
