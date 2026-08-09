"""Descoberta e vinculação de Logic Graphs fora da janela principal."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from engine.logic.graph_asset import load_logic_graph, save_logic_graph


class LogicAssetRepository:
    OBJECT_NAME_KEYS = frozenset({
        "object",
        "object_name",
        "target_name",
        "target_object",
        "follow_target",
    })

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
            if path.name.endswith(".autosave.zlogic"):
                continue
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

        # Explicit paths from object definition
        explicit_paths = set()
        has_explicit_declaration = "logic_assets" in object_data
        if isinstance(object_data.get("logic_assets"), list):
            for item in object_data["logic_assets"]:
                explicit_paths.add(str(item).replace("\\", "/").casefold())
        if isinstance(object_data.get("editor_data"), dict) and isinstance(object_data["editor_data"].get("logic_graphs"), list):
            has_explicit_declaration = True
            for item in object_data["editor_data"]["logic_graphs"]:
                if isinstance(item, dict) and item.get("path"):
                    explicit_paths.add(str(item["path"]).replace("\\", "/").casefold())
        if isinstance(object_data.get("components"), dict):
            items = object_data["components"].get("items", []) if isinstance(object_data["components"], dict) else []
            for comp in items:
                if isinstance(comp, dict) and comp.get("type") == "LogicGraph":
                    has_explicit_declaration = True
                    g_path = comp.get("graph_path") or comp.get("properties", {}).get("graph_path", "")
                    if g_path:
                        explicit_paths.add(str(g_path).replace("\\", "/").casefold())

        for path, graph in self.assets():
            if not bool(graph.get("enabled", True)):
                continue
            try:
                rel_path = str(path.relative_to(self.project_root.resolve()).as_posix()).casefold()
            except ValueError:
                rel_path = str(path).replace("\\", "/").casefold()

            target = graph.get("target", {})
            target_type = str(target.get("type", "name"))
            wanted = str(target.get("value", "")).casefold()

            if has_explicit_declaration:
                if rel_path in explicit_paths:
                    result.append((path, graph))
                continue
            if (target_type == "name" and wanted == object_name.casefold()) or (target_type == "tag" and wanted == tag):
                result.append((path, graph))
        return result

    def rename_object_references(self, old_name: str, new_name: str) -> list[Path]:
        """Persistently rename explicit object references across Logic Graph assets."""
        changed: list[tuple[Path, dict, dict]] = []
        for path, source in self.assets():
            graph = deepcopy(source)
            if self._rename_graph_references(graph, old_name, new_name):
                changed.append((path, source, graph))
        saved: list[tuple[Path, dict]] = []
        try:
            for path, source, graph in changed:
                self.save(path, graph)
                saved.append((path, source))
        except (OSError, ValueError):
            for path, source in reversed(saved):
                self.save(path, source)
            raise
        return [path for path, _source, _graph in changed]

    @classmethod
    def _rename_graph_references(
        cls, graph: dict, old_name: str, new_name: str
    ) -> bool:
        changed = False
        target = graph.get("target")
        if (
            isinstance(target, dict)
            and str(target.get("type", "name")) == "name"
            and str(target.get("value", "")).casefold() == old_name.casefold()
        ):
            target["value"] = new_name
            changed = True
        return cls._rename_nested_references(
            graph.get("nodes", []), old_name, new_name
        ) or cls._rename_nested_references(
            graph.get("variables", {}), old_name, new_name
        ) or changed

    @classmethod
    def _rename_nested_references(
        cls, value, old_name: str, new_name: str
    ) -> bool:
        changed = False
        if isinstance(value, list):
            for item in value:
                changed = cls._rename_nested_references(
                    item, old_name, new_name
                ) or changed
            return changed
        if not isinstance(value, dict):
            return False
        is_object_value = str(value.get("type", "")).casefold() == "object"
        for key, item in value.items():
            if (
                isinstance(item, str)
                and item.casefold() == old_name.casefold()
                and (str(key) in cls.OBJECT_NAME_KEYS or (
                    is_object_value and str(key) in {"value", "default"}
                ))
            ):
                value[key] = new_name
                changed = True
            else:
                changed = cls._rename_nested_references(
                    item, old_name, new_name
                ) or changed
        return changed
