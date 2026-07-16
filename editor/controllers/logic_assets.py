"""Descoberta e vinculação de Logic Graphs fora da janela principal."""

from __future__ import annotations

import json
from pathlib import Path

from engine.logic.graph_asset import load_logic_graph, save_logic_graph


class LogicAssetRepository:
    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self._cache: dict[Path, tuple[int, dict]] = {}

    def invalidate(self, path: Path) -> None:
        self._cache.pop(Path(path).resolve(), None)

    def save(self, path: Path, graph: dict) -> None:
        save_logic_graph(path, graph)
        self.invalidate(path)

    def assets(self) -> list[tuple[Path, dict]]:
        directory = self.project_root / "Assets" / "Logic"
        if not directory.is_dir():
            return []
        assets: list[tuple[Path, dict]] = []
        for path in sorted(directory.rglob("*.zlogic"), key=lambda entry: str(entry).casefold()):
            try:
                resolved = path.resolve()
                stamp = resolved.stat().st_mtime_ns
                cached = self._cache.get(resolved)
                if cached is None or cached[0] != stamp:
                    graph = load_logic_graph(resolved)
                    self._cache[resolved] = (stamp, graph)
                else:
                    graph = cached[1]
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if any(node.get("type") == "subgraph_start" for node in graph.get("nodes", [])):
                continue
            assets.append((resolved, graph))
        return assets

    def for_object(self, object_name: str, object_data: dict) -> list[tuple[Path, dict]]:
        tag = str(object_data.get("tag", object_data.get("name", object_name))).casefold()
        result: list[tuple[Path, dict]] = []
        for path, graph in self.assets():
            if not bool(graph.get("enabled", True)):
                continue
            target = graph.get("target", {})
            target_type = str(target.get("type", "name"))
            wanted = str(target.get("value", "")).casefold()
            if (target_type == "name" and wanted == object_name.casefold()) or (target_type == "tag" and wanted == tag):
                result.append((path, graph))
        return result

