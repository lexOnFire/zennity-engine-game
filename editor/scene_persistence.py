"""Lossless scene-document conversion for the official editor."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from editor.runtime.native_ui import scene_item_to_ui, ui_to_scene_item
from engine.logic.graph_asset import load_logic_graph
from engine.scene import SceneDocument


class EditorScenePersistence:
    """Translate editor snapshots at the typed, lossless document boundary."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)

    def save(
        self, path: Path, snapshots: list[dict[str, Any]],
        existing_document: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload = self.build_payload(path, snapshots, existing_document)
        SceneDocument.from_dict(payload).save(path)
        return payload

    def load(self, path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], bool]:
        payload = SceneDocument.load(path).to_dict()
        objects = payload.get("objects", [])
        if not isinstance(objects, list):
            raise ValueError("arquivo de cena inválido")
        snapshots = [
            snapshot for item in objects
            if isinstance(item, dict) and "name" in item
            for snapshot in [self._snapshot_from_object(item)]
            if snapshot is not None
        ]
        if not snapshots and objects:
            raise ValueError("nenhum objeto compatível")
        names = [str(item["name"]) for item in snapshots]
        if len(names) != len(set(names)):
            raise ValueError("existem objetos com nomes duplicados")
        typed = any("transform" in item for item in objects if isinstance(item, dict))
        return payload, snapshots, typed

    def build_payload(
        self, path: Path, snapshots: list[dict[str, Any]],
        existing_document: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload = deepcopy(existing_document) if existing_document else {
            "format_version": 2,
            "scene_name": path.stem,
            "engine_version": "Zennity 0.1.0",
            "objects": [],
        }
        payload["format_version"] = max(2, int(payload.get("format_version", 1)))
        payload["scene_name"] = str(payload.get("scene_name") or path.stem)
        blackboard = payload.get("blackboard")
        if not isinstance(blackboard, dict):
            blackboard = {}
        variables = blackboard.get("variables")
        payload["blackboard"] = {
            "variables": deepcopy(variables) if isinstance(variables, dict) else {}
        }
        existing = payload.get("objects", [])
        existing_by_id = {
            str(item.get("id")): item for item in existing
            if isinstance(item, dict) and item.get("id") is not None
        }
        existing_by_name = {
            str(item.get("name")): item for item in existing if isinstance(item, dict)
        }
        payload["objects"] = [
            self._object_from_snapshot(snapshot, existing_by_id, existing_by_name)
            for snapshot in snapshots
        ]
        return payload

    def collect_logic_variables(self, scope: str) -> dict[str, dict[str, Any]]:
        variables: dict[str, dict[str, Any]] = {}
        directory = self.project_root / "Assets" / "Logic"
        if not directory.is_dir():
            return variables
        for path in sorted(directory.rglob("*.zlogic"), key=lambda item: str(item).casefold()):
            if path.name.endswith(".autosave.zlogic"):
                continue
            try:
                graph = load_logic_graph(path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            for name, definition in graph.get("variables", {}).items():
                if isinstance(definition, dict) and definition.get("scope") == scope:
                    variables[str(name)] = deepcopy(definition)
        return variables

    def _object_from_snapshot(
        self, snapshot: dict[str, Any], existing_by_id: dict[str, dict[str, Any]],
        existing_by_name: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        source = deepcopy(
            existing_by_id.get(str(snapshot.get("id")))
            or existing_by_name.get(str(snapshot["name"]), {})
        )
        active = bool(snapshot.get("active", True))
        source.update({
            "name": snapshot["name"], "active": active, "enabled": active,
            "static": bool(snapshot.get("static", False)),
            "tag": str(snapshot.get("tag", "Untagged")),
            "layer": str(snapshot.get("layer", "Default")),
        })
        source.setdefault("id", snapshot.get("id", snapshot["name"]))
        rotation = float(snapshot.get("rotation", 0.0))
        source["transform"] = {
            "position": [snapshot["x"], snapshot["y"], 0.0],
            "rotation": [0.0, 0.0, rotation], "rz": rotation,
            "scale": [snapshot["w"], snapshot["h"], 1.0],
        }
        visual = source.get("visual")
        if not isinstance(visual, dict):
            visual = {}
            source["visual"] = visual
        visual.update({
            "enabled": bool(snapshot.get("renderer_enabled", True)),
            "material": str(snapshot.get("material", "Default_Material")),
            "mesh_type": snapshot.get("mesh_type"),
            "color": snapshot.get("color", (255, 255, 255)),
            "texture": str(snapshot.get("texture", "")),
            "layer": str(snapshot.get("render_layer", "Default")),
            "order": int(snapshot.get("sort_order", 0)),
        })
        components = source.get("components")
        if not isinstance(components, dict):
            components = {}
            source["components"] = components
        for key in ("controller", "rigidbody", "collider", "camera", "audio", "scripts"):
            components.pop(key, None)
        if snapshot.get("rigidbody") is not None:
            components["rigidbody"] = deepcopy(snapshot["rigidbody"])
        if snapshot.get("collider") is not None:
            collider = deepcopy(snapshot["collider"])
            collider.setdefault("width", snapshot["w"])
            collider.setdefault("height", snapshot["h"])
            components["collider"] = collider
        if snapshot.get("camera") is not None or "Camera2D" in snapshot.get("component_names", []):
            components["camera"] = deepcopy(snapshot.get("camera") or {"active": True, "zoom": 1.0})
        if isinstance(snapshot.get("audio"), dict):
            components["audio"] = deepcopy(snapshot["audio"])
        existing_items = components.get("items") if isinstance(components.get("items"), list) else []
        snapshot_components = snapshot.get("components")
        if isinstance(snapshot_components, dict):
            snapshot_items = snapshot_components.get("items")
            if isinstance(snapshot_items, list):
                for s_item in snapshot_items:
                    if isinstance(s_item, dict) and s_item not in existing_items:
                        existing_items.append(deepcopy(s_item))

        components["items"] = [deepcopy(item) for item in existing_items if scene_item_to_ui(item) is None]
        ui_item = ui_to_scene_item(snapshot.get("ui"))
        if ui_item is not None:
            components["items"].append(ui_item)
        if not components["items"]:
            components.pop("items", None)
        if isinstance(snapshot.get("logic_assets"), list):
            source["logic_assets"] = deepcopy(snapshot["logic_assets"])

        known = {
            "id", "name", "x", "y", "w", "h", "rotation", "color", "mesh_type",
            "renderer_enabled", "material", "texture", "render_layer", "sort_order",
            "active", "static", "tag", "layer", "rigidbody", "collider", "camera",
            "audio", "scripts", "component_names", "ui", "logic_assets", "components",
        }
        editor_data = {
            key: deepcopy(value) for key, value in snapshot.items()
            if key not in known and not str(key).startswith("_")
        }
        if editor_data:
            source["editor_data"] = editor_data
        else:
            source.pop("editor_data", None)
        return source

    @staticmethod
    def _snapshot_from_object(item: dict[str, Any]) -> dict[str, Any] | None:
        if "transform" not in item:
            return dict(item) if {"x", "y", "w", "h"}.issubset(item) else None
        transform = item.get("transform", {})
        position = list(transform.get("position", [0.0, 0.0, 0.0]))
        scale = list(transform.get("scale", [32.0, 32.0, 1.0]))
        visual = item.get("visual", {}) or {}
        components = item.get("components", {}) or {}
        name = str(item["name"])
        color = visual.get("color") or ((91, 194, 100) if name.lower() in {"chao", "floor"} else (88, 117, 255))
        rotation = transform.get("rz", (transform.get("rotation") or [0.0, 0.0, 0.0])[2])
        snapshot = {
            "id": item.get("id", name), "name": name,
            "x": float(position[0]), "y": float(position[1]),
            "w": abs(float(scale[0])), "h": abs(float(scale[1])),
            "rotation": float(rotation), "color": color,
            "mesh_type": visual.get("mesh_type"),
            "renderer_enabled": bool(visual.get("enabled", True)),
            "material": str(visual.get("material", "Default_Material")),
            "texture": str(visual.get("texture", "")),
            "render_layer": str(visual.get("layer", "Default")),
            "sort_order": int(visual.get("order", 0)),
            "active": bool(item.get("active", item.get("enabled", True))),
            "static": bool(item.get("static", False)),
            "tag": str(item.get("tag", "Untagged")),
            "layer": str(item.get("layer", "Default")),
        }
        if isinstance(item.get("editor_data"), dict):
            snapshot["editor_data"] = deepcopy(item["editor_data"])
            snapshot.update(deepcopy(item["editor_data"]))
        if isinstance(item.get("logic_assets"), list):
            snapshot["logic_assets"] = deepcopy(item["logic_assets"])
        if isinstance(components, dict) and components:
            snapshot["components"] = deepcopy(components)

        for key in ("rigidbody", "collider", "camera", "audio"):
            if isinstance(components.get(key), dict):
                snapshot[key] = deepcopy(components[key])
        component_names = ["Camera2D"] if isinstance(components.get("camera"), dict) else []
        for component in components.get("items", []):
            if isinstance(component, dict):
                component_names.append(str(component.get("type") or component.get("component_type") or "Component"))
                parsed_ui = scene_item_to_ui(component)
                if parsed_ui is not None:
                    snapshot["ui"] = parsed_ui
        if component_names:
            snapshot["component_names"] = component_names
        return snapshot
