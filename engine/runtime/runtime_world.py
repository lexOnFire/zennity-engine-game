"""Modelo leve e compartilhado dos objetos usados pelo Play Mode exportável."""
from __future__ import annotations

import uuid
from copy import deepcopy
from pathlib import Path
import math
from typing import Any, Mapping, MutableMapping

try:
    from .prefab_asset import apply_exposed_properties, load_prefab_asset, resolve_prefab_parameters
except ImportError:
    from engine.prefabs.prefab_asset import apply_exposed_properties, load_prefab_asset, resolve_prefab_parameters


def _vector(value: Any, fallback: tuple[float, float, float]) -> list[float]:
    raw = list(value) if isinstance(value, (list, tuple)) else list(fallback)
    raw = (raw + list(fallback))[:3]
    return [float(raw[0]), float(raw[1]), float(raw[2])]


def normalize_color(value: Any) -> tuple[int, int, int]:
    if isinstance(value, str):
        raw = value.strip().lstrip("#")
        if len(raw) == 6:
            try:
                return tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4))
            except ValueError:
                pass
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return tuple(max(0, min(255, int(channel))) for channel in value[:3])
        except (TypeError, ValueError):
            pass
    return 88, 166, 255


class RuntimeWorld:
    """Fonte única para criação e mutação estrutural do mundo em execução."""

    MAX_POOLED_PER_PREFAB = 128

    def __init__(self, objects: MutableMapping[str, dict[str, Any]]) -> None:
        self.objects = objects
        self.created_count = 0
        self.destroyed_count = 0
        self.reused_count = 0
        self._pool: dict[str, list[dict[str, Any]]] = {}

    def unique_name(self, requested: str) -> str:
        base = str(requested).strip() or "NovoObjeto"
        name, suffix = base, 2
        while name in self.objects:
            name = f"{base}_{suffix}"
            suffix += 1
        return name

    def create_object(self, **values: Any) -> dict[str, Any]:
        name = self.unique_name(str(values.get("name", "NovoObjeto")))
        obj: dict[str, Any] = {
            "id": str(uuid.uuid4()), "name": name,
            "x": float(values.get("x", 0.0)), "y": float(values.get("y", 0.0)),
            "w": max(1.0, float(values.get("width", values.get("w", 64.0)))),
            "h": max(1.0, float(values.get("height", values.get("h", 64.0)))),
            "rotation": float(values.get("rotation", 0.0)),
            "color": normalize_color(values.get("color", "#58a6ff")),
            "tag": str(values.get("tag", "Untagged")).strip() or "Untagged",
            "layer": str(values.get("layer", "Default")),
            "mesh_type": str(values.get("mesh_type", "Sprite")),
            "active": bool(values.get("active", True)),
            "renderer_enabled": bool(values.get("renderer_enabled", True)),
            "spawned_by_logic": bool(values.get("spawned_by_logic", True)),
        }
        texture = str(values.get("texture", "")).strip()
        if texture:
            obj["texture"] = texture
        for key in (
            "rigidbody", "collider", "camera", "audio", "animator", "behavior",
            "ui", "logic_graphs", "prefab_path", "prefab_uuid", "render_layer",
            "sort_order", "static",
            "gameplay", "prefab_parameters", "prefab_exposed", "prefab_base",
        ):
            if key in values:
                obj[key] = deepcopy(values[key])
        pool_key = str(values.get("pool_key", "")).strip()
        if pool_key and self._pool.get(pool_key):
            reused = self._pool[pool_key].pop()
            reused.clear()
            reused.update(obj)
            obj = reused
            self.reused_count += 1
        if pool_key:
            obj["pool_key"] = pool_key
        self.objects[name] = obj
        self.created_count += 1
        return obj

    def clone_object(self, source: Mapping[str, Any], name: str = "", pool_key: str = "") -> dict[str, Any]:
        """Cria uma cópia profunda e independente, preservando componentes e visual."""
        clone = deepcopy(dict(source))
        for key in tuple(clone):
            if str(key).startswith("_"):
                clone.pop(key, None)
        clone.pop("destroyed", None)
        clone.pop("pool_key", None)
        clone["id"] = str(uuid.uuid4())
        clone["name"] = self.unique_name(name or f"{source.get('name', 'Objeto')}_Copia")
        clone["active"] = True
        clone["spawned_by_logic"] = True
        normalized_pool_key = str(pool_key).strip()
        if normalized_pool_key and self._pool.get(normalized_pool_key):
            reused = self._pool[normalized_pool_key].pop()
            reused.clear()
            reused.update(clone)
            clone = reused
            self.reused_count += 1
        if normalized_pool_key:
            clone["pool_key"] = normalized_pool_key
        self.objects[str(clone["name"])] = clone
        self.created_count += 1
        return clone

    def active_spawn_count(self, spawn_group: str) -> int:
        """Conta somente instâncias vivas criadas pelo mesmo bloco."""
        group = str(spawn_group)
        return sum(
            1 for obj in self.objects.values()
            if obj.get("active", True)
            and str((obj.get("spawn_lifecycle") or {}).get("group", "")) == group
        )

    def can_spawn(self, spawn_group: str, maximum: int = 0) -> bool:
        limit = max(0, int(maximum))
        return not limit or self.active_spawn_count(spawn_group) < limit

    def configure_spawned(
        self,
        obj: MutableMapping[str, Any],
        *,
        spawn_group: str,
        lifetime: float = 0.0,
        max_distance: float = 0.0,
        creator_graph: str = "",
        creator_object: str = "",
        creator_node: str = "",
        pool_key: str = "",
    ) -> None:
        """Anexa metadados de origem e descarte usados no Play Mode."""
        if pool_key:
            obj["pool_key"] = str(pool_key)
        obj["spawn_lifecycle"] = {
            "group": str(spawn_group),
            "age": 0.0,
            "lifetime": max(0.0, float(lifetime)),
            "max_distance": max(0.0, float(max_distance)),
            "origin_x": float(obj.get("x", 0.0)),
            "origin_y": float(obj.get("y", 0.0)),
            "creator_graph": str(creator_graph),
            "creator_object": str(creator_object),
            "creator_node": str(creator_node),
        }

    def destroy_after(self, obj: MutableMapping[str, Any], seconds: float) -> None:
        lifecycle = obj.setdefault("spawn_lifecycle", {})
        lifecycle["age"] = 0.0
        lifecycle["lifetime"] = max(0.0, float(seconds))
        lifecycle.setdefault("origin_x", float(obj.get("x", 0.0)))
        lifecycle.setdefault("origin_y", float(obj.get("y", 0.0)))

    def update_lifecycle(self, dt: float) -> list[str]:
        """Descarta instâncias por tempo ou distância e devolve seus nomes."""
        destroyed: list[str] = []
        for name, obj in list(self.objects.items()):
            lifecycle = obj.get("spawn_lifecycle")
            if not isinstance(lifecycle, dict) or not obj.get("active", True):
                continue
            lifecycle["age"] = float(lifecycle.get("age", 0.0)) + max(0.0, float(dt))
            lifetime = max(0.0, float(lifecycle.get("lifetime", 0.0)))
            maximum_distance = max(0.0, float(lifecycle.get("max_distance", 0.0)))
            distance = math.hypot(
                float(obj.get("x", 0.0)) - float(lifecycle.get("origin_x", obj.get("x", 0.0))),
                float(obj.get("y", 0.0)) - float(lifecycle.get("origin_y", obj.get("y", 0.0))),
            )
            if (lifetime and lifecycle["age"] >= lifetime) or (maximum_distance and distance >= maximum_distance):
                destroyed.append(str(name))
                self.destroy_object(obj)
        return destroyed

    def instantiate_prefab(
        self,
        path: str | Path,
        *,
        x: float | None = None,
        y: float | None = None,
        rotation: float | None = None,
        width: float | None = None,
        height: float | None = None,
        include_camera: bool = True,
        include_audio: bool = True,
        include_logic: bool = True,
        parameters: Mapping[str, Any] | None = None,
        project_root: str | Path | None = None,
        pool_key: str | None = None,
    ) -> dict[str, Any]:
        root = Path(project_root or Path.cwd())
        payload = load_prefab_asset(path, root)
        isolated_object = deepcopy(payload["object"])
        definitions = payload.get("exposed_properties", [])
        resolved_parameters = resolve_prefab_parameters(definitions, parameters)
        apply_exposed_properties(isolated_object, definitions, resolved_parameters)
        if not any(key in isolated_object for key in ("transform", "visual", "components")):
            values = isolated_object
            values.pop("id", None)
            values.pop("uuid", None)
            values["name"] = values.get("name") or payload.get("prefab_name", "Prefab")
            if x is not None:
                values["x"] = x
            if y is not None:
                values["y"] = y
            if rotation is not None:
                values["rotation"] = rotation
            if width is not None:
                values["w"] = width
                values["width"] = width
            if height is not None:
                values["h"] = height
                values["height"] = height
            values["prefab_parameters"] = resolved_parameters
            values["prefab_exposed"] = definitions
            values["prefab_base"] = payload.get("base_prefab", "")
            self._apply_prefab_component_policy(values, include_camera, include_audio, include_logic)
            values["prefab_path"] = str(path)
            values["pool_key"] = pool_key or f"prefab:{Path(path).as_posix().casefold()}"
            return self.create_object(**values)
        transform = isolated_object.get("transform") if isinstance(isolated_object.get("transform"), dict) else {}
        position = _vector(transform.get("position"), (0.0, 0.0, 0.0))
        scale = _vector(transform.get("scale"), (64.0, 64.0, 1.0))
        transform_rotation = _vector(transform.get("rotation"), (0.0, 0.0, 0.0))
        visual = isolated_object.get("visual") if isinstance(isolated_object.get("visual"), dict) else {}
        components = isolated_object.get("components") if isinstance(isolated_object.get("components"), dict) else {}
        values: dict[str, Any] = {
            "name": isolated_object.get("source_object_name") or isolated_object.get("name", payload.get("prefab_name", "Prefab")),
            "x": position[0] if x is None else x, "y": position[1] if y is None else y,
            "width": abs(scale[0]) if width is None else width,
            "height": abs(scale[1]) if height is None else height,
            "rotation": transform_rotation[2] if rotation is None else rotation,
            "color": visual.get("color", (180, 180, 190)),
            "texture": visual.get("texture", visual.get("sprite_path", "")),
            "renderer_enabled": visual.get("enabled", True), "tag": isolated_object.get("tag", "Untagged"),
            "active": isolated_object.get("active", isolated_object.get("enabled", True)),
            "layer": isolated_object.get("layer", "Default"),
            "prefab_uuid": isolated_object.get("prefab_uuid"),
            "prefab_parameters": resolved_parameters,
            "prefab_exposed": definitions,
            "prefab_base": payload.get("base_prefab", ""),
        }
        if isinstance(isolated_object.get("gameplay"), Mapping):
            values["gameplay"] = isolated_object["gameplay"]
        for key in ("rigidbody", "collider", "camera", "audio"):
            if isinstance(components.get(key), dict):
                values[key] = components[key]
        if isinstance(components.get("logic_graphs"), list):
            values["logic_graphs"] = components["logic_graphs"]
        editor_data = isolated_object.get("editor_data") if isinstance(isolated_object.get("editor_data"), dict) else {}
        for key in ("animator", "behavior"):
            if isinstance(editor_data.get(key), dict):
                values[key] = editor_data[key]
        if isinstance(editor_data.get("logic_graphs"), list):
            values["logic_graphs"] = editor_data["logic_graphs"]
        for item in components.get("items", []):
            if not isinstance(item, dict):
                continue
            kind = str(item.get("type", "")).casefold()
            properties = deepcopy(item.get("properties", {})) if isinstance(item.get("properties"), dict) else {}
            if kind in {"camera", "camera2d"} and "camera" not in values:
                if "clear_color" in properties and "background_color" not in properties:
                    properties["background_color"] = properties.pop("clear_color")
                properties.setdefault("active", bool(item.get("enabled", True)))
                values["camera"] = properties
                continue
            if kind in {"audiosource", "audio_source"} and "audio" not in values:
                if "audio_clip" in properties and "path" not in properties:
                    properties["path"] = properties.pop("audio_clip")
                if "play_on_awake" in properties and "autoplay" not in properties:
                    properties["autoplay"] = properties.pop("play_on_awake")
                properties.setdefault("enabled", bool(item.get("enabled", True)))
                values["audio"] = properties
                continue
            if kind not in {"canvas", "label", "uilabel", "image", "uiimage", "button", "uibutton"}:
                continue
            ui = properties
            ui["type"] = {"label": "text", "uilabel": "text", "uiimage": "image", "uibutton": "button"}.get(kind, kind)
            ui.setdefault("visible", bool(item.get("enabled", True)))
            values["ui"] = ui
            break
        values["prefab_path"] = str(path)
        values["pool_key"] = pool_key or f"prefab:{Path(path).as_posix().casefold()}"
        self._apply_prefab_component_policy(values, include_camera, include_audio, include_logic)
        return self.create_object(**values)

    @staticmethod
    def _apply_prefab_component_policy(
        values: MutableMapping[str, Any],
        include_camera: bool,
        include_audio: bool,
        include_logic: bool,
    ) -> None:
        """Remove componentes globais quando o bloco não os autorizou explicitamente."""
        if not include_camera:
            values.pop("camera", None)
        if not include_audio:
            values.pop("audio", None)
        if not include_logic:
            values.pop("logic_graphs", None)

    @staticmethod
    def add_component(obj: MutableMapping[str, Any], component: str, properties: Mapping[str, Any] | None = None) -> None:
        key = str(component).strip().casefold().replace(" ", "_")
        aliases = {
            "boxcollider": "box_collider", "rigidbody2d": "rigidbody",
            "rigid_body": "rigidbody", "audiosource": "audio",
            "audio_source": "audio", "camera2d": "camera",
            "animator2d": "animator", "spriterenderer": "sprite_renderer",
            "uitext": "ui_text", "uiimage": "ui_image", "uibutton": "ui_button",
        }
        key = aliases.get(key, key)
        values = deepcopy(dict(properties or {}))
        if key == "sprite_renderer":
            obj["renderer_enabled"] = True
            for name in ("texture", "color", "render_layer", "sort_order"):
                if name in values:
                    obj[name] = values[name]
            return
        if key in {"box_collider", "circlecollider", "circle_collider"}:
            values.setdefault(
                "type", "circle" if "circle" in key else "box"
            )
            obj["collider"] = values
            return
        if key in {"canvas", "ui_text", "ui_image", "ui_button"}:
            values["type"] = {
                "canvas": "canvas", "ui_text": "text",
                "ui_image": "image", "ui_button": "button",
            }[key]
            values.setdefault("visible", True)
            obj["ui"] = values
            obj["renderer_enabled"] = False
            obj["mesh_type"] = "UI"
            return
        obj[key] = values
        if key == "collider":
            obj[key].setdefault("type", "box")
        elif key == "rigidbody":
            obj[key].setdefault("is_kinematic", False)
            obj[key].setdefault("use_gravity", True)

    @staticmethod
    def remove_component(obj: MutableMapping[str, Any], component: str) -> bool:
        key = str(component).strip().casefold().replace(" ", "_")
        aliases = {
            "boxcollider": "collider", "box_collider": "collider",
            "circlecollider": "collider", "circle_collider": "collider",
            "rigidbody2d": "rigidbody", "audiosource": "audio",
            "audio_source": "audio", "camera2d": "camera",
            "animator2d": "animator", "spriterenderer": "renderer_enabled",
            "sprite_renderer": "renderer_enabled", "canvas": "ui",
            "uitext": "ui", "ui_text": "ui", "uiimage": "ui",
            "ui_image": "ui", "uibutton": "ui", "ui_button": "ui",
        }
        return obj.pop(aliases.get(key, key), None) is not None

    def destroy_object(self, obj: MutableMapping[str, Any]) -> None:
        if obj.get("active", True):
            obj["active"] = False
            obj["destroyed"] = True
            self.destroyed_count += 1
            name = str(obj.get("name", ""))
            if name and self.objects.get(name) is obj:
                self.objects.pop(name, None)
            pool_key = str(obj.get("pool_key", ""))
            if pool_key and len(self._pool.get(pool_key, ())) < self.MAX_POOLED_PER_PREFAB:
                self._pool.setdefault(pool_key, []).append(obj)  # type: ignore[arg-type]

    def stats(self) -> dict[str, int]:
        active = sum(1 for obj in self.objects.values() if obj.get("active", True))
        pooled = sum(len(items) for items in self._pool.values())
        return {"objects": len(self.objects), "active": active, "created": self.created_count, "destroyed": self.destroyed_count, "reused": self.reused_count, "pooled": pooled}

    def reset_session(self) -> None:
        self.created_count = 0
        self.destroyed_count = 0
        self.reused_count = 0
        self._pool.clear()
