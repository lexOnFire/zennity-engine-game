"""Impede aumento acidental da dívida estrutural já medida."""
from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = ("editor", "engine", "editor_legacy")


def collect() -> dict[str, int]:
    classes: list[int] = []
    methods: list[int] = []
    imports: dict[str, set[str]] = defaultdict(set)
    modules: set[str] = set()
    files_over_500 = 0
    for root_name in SOURCE_ROOTS:
        for path in (ROOT / root_name).rglob("*.py"):
            source = path.read_text(encoding="utf-8-sig")
            if len(source.splitlines()) > 500:
                files_over_500 += 1
            tree = ast.parse(source)
            module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
            modules.add(module)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.end_lineno - node.lineno + 1)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(node.end_lineno - node.lineno + 1)
                elif isinstance(node, ast.Import):
                    imports[module].update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports[module].add(node.module)
    graph = {module: set() for module in modules}
    for module, dependencies in imports.items():
        for dependency in dependencies:
            candidates = [item for item in modules if item == dependency or item.startswith(dependency + ".")]
            if candidates:
                graph[module].add(min(candidates, key=len))
    return {
        "max_class_lines": max(classes, default=0),
        "max_method_lines": max(methods, default=0),
        "max_files_over_500_lines": files_over_500,
        "max_import_cycles": strongly_connected_count(graph),
    }


def strongly_connected_count(graph: dict[str, set[str]]) -> int:
    index = 0
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles = 0

    def visit(node: str) -> None:
        nonlocal index, cycles
        indexes[node] = lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in graph[node]:
            if target not in indexes:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[target])
        if lowlinks[node] == indexes[node]:
            size = 0
            while True:
                target = stack.pop()
                on_stack.remove(target)
                size += 1
                if target == node:
                    break
            if size > 1:
                cycles += 1

    for node in graph:
        if node not in indexes:
            visit(node)
    return cycles


def main() -> int:
    budget = json.loads((ROOT / "tools" / "architecture_budget.json").read_text(encoding="utf-8"))
    actual = collect()
    failures = [f"{name}: {actual[name]} > {limit}" for name, limit in budget.items() if actual[name] > limit]
    print(json.dumps({"actual": actual, "budget": budget}, indent=2))
    if failures:
        print("Architecture budget exceeded:\n- " + "\n- ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
