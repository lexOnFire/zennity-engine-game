"""Release budgets for registered Logic Graph node handlers."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "engine" / "logic" / "runtime"
MAX_HANDLER_LINES = 60


def _is_registered_handler(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        call = decorator if isinstance(decorator, ast.Call) else None
        target = call.func if call is not None else decorator
        if isinstance(target, ast.Attribute) and target.attr in {
            "register_executor", "register_evaluator",
        }:
            return True
    return False


def test_registered_node_handlers_stay_below_sixty_lines() -> None:
    handlers: dict[str, int] = {}
    for path in sorted((RUNTIME / "nodes").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_registered_handler(node):
                handlers[f"{path.name}:{node.name}"] = node.end_lineno - node.lineno + 1
    assert len(handlers) >= 10, "Registry discovery failed; too few handlers were measured"
    oversized = {name: size for name, size in handlers.items() if size > MAX_HANDLER_LINES}
    assert oversized == {}, f"Logic Graph handlers above {MAX_HANDLER_LINES} lines: {oversized}"


def test_runtime_orchestration_methods_stay_below_one_hundred_lines() -> None:
    path = RUNTIME / "core.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    runtime = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LogicGraphRuntime"
    )
    oversized = {
        node.name: node.end_lineno - node.lineno + 1
        for node in runtime.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.end_lineno - node.lineno + 1 > 100
    }
    assert oversized == {}


def test_graph_asset_boundaries_stay_below_one_hundred_lines() -> None:
    entrypoint_limits = {
        "graph_normalizer.py": ("normalize_logic_graph", 30),
        "graph_validator.py": ("validate_logic_graph", 40),
    }
    for filename, (entrypoint, entrypoint_limit) in entrypoint_limits.items():
        path = ROOT / "engine" / "logic" / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        sizes = {
            node.name: node.end_lineno - node.lineno + 1
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        assert sizes[entrypoint] <= entrypoint_limit
        assert max(sizes.values()) < 100
