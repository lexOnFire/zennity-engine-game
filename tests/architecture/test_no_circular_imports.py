"""Global circular-import gate for production Python modules."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOTS = (ROOT / "engine", ROOT / "editor")


def _module_name(path: Path) -> str:
    relative = path.relative_to(ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _resolve_from(current: str, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package = current.split(".")
    if not current.endswith("__init__"):
        package = package[:-1]
    keep = max(0, len(package) - node.level + 1)
    prefix = package[:keep]
    if node.module:
        prefix.extend(node.module.split("."))
    return ".".join(prefix)


def _production_graph() -> dict[str, set[str]]:
    # Package facades intentionally re-export implementations.  The release gate
    # targets executable implementation modules, where cycles affect initialization.
    paths = [
        path for root in SOURCE_ROOTS for path in root.rglob("*.py")
        if path.name != "__init__.py" and not path.with_suffix("").is_dir()
    ]
    modules = {_module_name(path): path for path in paths}
    graph = {module: set() for module in modules}
    for module, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        runtime_nodes: list[ast.AST] = []
        pending = list(tree.body)
        while pending:
            node = pending.pop()
            if (
                isinstance(node, ast.If)
                and isinstance(node.test, ast.Name)
                and node.test.id == "TYPE_CHECKING"
            ):
                pending.extend(node.orelse)
                continue
            runtime_nodes.append(node)
            pending.extend(ast.iter_child_nodes(node))
        for node in runtime_nodes:
            candidates: list[str] = []
            if isinstance(node, ast.Import):
                candidates.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = _resolve_from(module, node)
                candidates.append(base)
                candidates.extend(
                    f"{base}.{alias.name}" if base else alias.name
                    for alias in node.names if alias.name != "*"
                )
            for candidate in candidates:
                target = candidate
                while target and target not in modules:
                    target = target.rpartition(".")[0]
                if target in modules and target != module:
                    graph[module].add(target)
    return graph


def _strongly_connected(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
    index = 0
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    active: set[str] = set()
    cycles: list[tuple[str, ...]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = low[node] = index
        index += 1
        stack.append(node)
        active.add(node)
        for target in graph[node]:
            if target not in indices:
                visit(target)
                low[node] = min(low[node], low[target])
            elif target in active:
                low[node] = min(low[node], indices[target])
        if low[node] != indices[node]:
            return
        component: list[str] = []
        while stack:
            target = stack.pop()
            active.remove(target)
            component.append(target)
            if target == node:
                break
        if len(component) > 1:
            cycles.append(tuple(sorted(component)))

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(cycles)


def test_production_import_graph_is_acyclic() -> None:
    cycles = _strongly_connected(_production_graph())
    assert cycles == [], "Circular production imports:\n" + "\n".join(
        " -> ".join(component) for component in cycles
    )
