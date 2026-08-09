"""Logic Graph binding operations shared by Phase 1 editor surfaces."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from engine.logic.graph_asset import create_logic_node, default_logic_graph, load_logic_graph


class LogicBindingController:
    """Owns Logic Graph asset bindings without depending on a specific window."""

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()

    def assets(self) -> list[tuple[Path, dict]]:
        return self.host._logic_assets_repository.assets()

    def graphs_for_object(self, object_name: str) -> list[tuple[Path, dict]]:
        obj = self.host._objects_by_name.get(object_name, {})
        return self.host._logic_assets_repository.for_object(object_name, obj)

    def save_binding(self, path: Path, graph: dict) -> None:
        self.host._logic_assets_repository.save(path, graph)
        self._refresh_surfaces()

    def bind_existing_to_object(self, path: Path, object_name: str) -> dict:
        graph = deepcopy(load_logic_graph(path))
        graph["enabled"] = True
        graph["target"] = {"type": "name", "value": object_name}
        self.save_binding(path, graph)
        self._update_object_logic_assets(object_name, path)
        return graph

    def _update_object_logic_assets(self, object_name: str, path: Path) -> None:
        obj = getattr(self.host, "_objects_by_name", {}).get(object_name)
        if isinstance(obj, dict):
            try:
                rel = path.relative_to(self.project_root.resolve()).as_posix()
            except ValueError:
                rel = str(path).replace("\\", "/")
            obj["logic_assets"] = [rel]

    def create_for_object(self, object_name: str) -> Path:
        return self._create_for_object(object_name, with_start_event=True)

    def create_blank_for_object(self, object_name: str) -> Path:
        return self._create_for_object(object_name, with_start_event=False)

    def _create_for_object(
        self, object_name: str, *, with_start_event: bool
    ) -> Path:
        directory = self.project_root / "Assets" / "Logic"
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(char if char.isalnum() else "_" for char in object_name).strip("_") or "Object"
        path = directory / f"{safe_name}Logic.zlogic"
        suffix = 2
        while path.exists():
            path = directory / f"{safe_name}Logic{suffix}.zlogic"
            suffix += 1
        graph = default_logic_graph(path.stem)
        graph["target"] = {"type": "name", "value": object_name}
        graph["nodes"] = (
            [create_logic_node("event_start", (80.0, 100.0))]
            if with_start_event else []
        )
        self.save_binding(path, graph)
        self._update_object_logic_assets(object_name, path)
        return path

    def detach(self, path: Path) -> None:
        graph = deepcopy(load_logic_graph(path))
        graph["enabled"] = False
        self.save_binding(path, graph)
        target_name = graph.get("target", {}).get("value")
        if target_name and target_name in getattr(self.host, "_objects_by_name", {}):
            obj = self.host._objects_by_name[target_name]
            if isinstance(obj, dict):
                try:
                    rel = path.relative_to(self.project_root.resolve()).as_posix()
                except ValueError:
                    rel = str(path).replace("\\", "/")
                if "logic_assets" in obj:
                    obj["logic_assets"] = [p for p in obj["logic_assets"] if p != rel]
                if isinstance(obj.get("components"), dict):
                    items = obj["components"].get("items", [])
                    if isinstance(items, list):
                        obj["components"]["items"] = [
                            c for c in items
                            if not (isinstance(c, dict) and c.get("type") == "LogicGraph" and (c.get("graph_path") == rel or c.get("properties", {}).get("graph_path") == rel))
                        ]
                if isinstance(obj.get("editor_data"), dict):
                    obj["editor_data"].pop("logic_graphs", None)

    def detach_all_for_object(self, object_name: str) -> int:
        bindings = self.graphs_for_object(object_name)
        for path, source in bindings:
            graph = deepcopy(source)
            graph["enabled"] = False
            self.host._logic_assets_repository.save(path, graph)
        obj = getattr(self.host, "_objects_by_name", {}).get(object_name)
        if isinstance(obj, dict):
            obj["logic_assets"] = []
            if isinstance(obj.get("components"), dict):
                items = obj["components"].get("items", [])
                if isinstance(items, list):
                    obj["components"]["items"] = [
                        c for c in items if not (isinstance(c, dict) and c.get("type") == "LogicGraph")
                    ]
            if isinstance(obj.get("editor_data"), dict):
                obj["editor_data"].pop("logic_graphs", None)
                if isinstance(obj["editor_data"].get("editor_data"), dict):
                    obj["editor_data"]["editor_data"].pop("logic_graphs", None)
        self._refresh_surfaces()
        return len(bindings)

    def _refresh_surfaces(self) -> None:
        h = self.host
        h._asset_browser.refresh()
        if h._selected_name in h._objects_by_name:
            h._update_inspector(h._selected_name)
