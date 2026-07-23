"""Global structural release budgets for the official production packages."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_ROOTS = (ROOT / "engine", ROOT / "editor")


def _production_nodes() -> list[tuple[Path, ast.AST]]:
    nodes: list[tuple[Path, ast.AST]] = []
    for package in PRODUCTION_ROOTS:
        for path in sorted(package.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            nodes.extend((path, node) for node in ast.walk(tree))
    return nodes


def test_production_classes_stay_below_five_hundred_lines() -> None:
    oversized = {
        f"{path.relative_to(ROOT).as_posix()}:{node.lineno}:{node.name}":
            node.end_lineno - node.lineno + 1
        for path, node in _production_nodes()
        if isinstance(node, ast.ClassDef)
        and node.end_lineno - node.lineno + 1 > 500
    }
    assert oversized == {}


def test_production_functions_stay_below_one_hundred_lines() -> None:
    oversized = {
        f"{path.relative_to(ROOT).as_posix()}:{node.lineno}:{node.name}":
            node.end_lineno - node.lineno + 1
        for path, node in _production_nodes()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.end_lineno - node.lineno + 1 > 100
    }
    assert oversized == {}
