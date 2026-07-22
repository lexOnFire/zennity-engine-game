"""Edit-mode command handlers for the isolated viewport."""
from __future__ import annotations

import math
import uuid
from pathlib import Path
from typing import Any, Callable


class ViewportEditCommandHandler:
    """Applies scene editing commands independently from the render loop."""

    COMMAND_TYPES = frozenset({
        "select_object", "move_selected", "set_transform", "set_physics",
        "set_collider", "script_instruction", "script_drop_at",
        "create_object_at", "create_sprite_at", "reset_scene",
    })

    def __init__(
        self,
        objects: dict[str, dict[str, Any]],
        emit: Callable[[dict[str, Any]], None],
        world_to_screen: Callable[[float, float], tuple[float, float]],
        screen_to_world: Callable[[float, float], tuple[float, float]],
        view_zoom: Callable[[], float],
    ) -> None:
        self.objects = objects
        self.emit = emit
        self.world_to_screen = world_to_screen
        self.screen_to_world = screen_to_world
        self.view_zoom = view_zoom

    def handle(
        self,
        command: dict[str, Any],
        *,
        playing: bool,
        selected_name: str | None,
    ) -> tuple[bool, str | None]:
        command_type = str(command.get("type", ""))
        if command_type not in self.COMMAND_TYPES:
            return False, selected_name
        if command_type == "select_object":
            name = str(command.get("name", ""))
            if name in self.objects:
                selected_name = name
                self.emit({"type": "selected", "name": name})
        elif command_type == "move_selected" and selected_name in self.objects:
            obj = self.objects[selected_name]
            obj["x"] += float(command.get("dx", 0.0))
            obj["y"] += float(command.get("dy", 0.0))
            self.emit({"type": "transform", "name": selected_name, "x": obj["x"], "y": obj["y"]})
        elif command_type == "set_transform":
            name = str(command.get("name", ""))
            if name in self.objects and not playing:
                obj = self.objects[name]
                for key in ("x", "y", "w", "h", "rotation"):
                    if key in command:
                        obj[key] = float(command[key])
                self.emit({"type": "transform", "name": name, **{key: obj[key] for key in ("x", "y", "w", "h", "rotation")}})
        elif command_type == "set_physics":
            self._set_dictionary_component(command, "rigidbody", playing)
        elif command_type == "set_collider":
            self._set_dictionary_component(command, "collider", playing)
        elif command_type == "script_instruction":
            name = str(command.get("name", ""))
            instruction = command.get("instruction")
            if name in self.objects and isinstance(instruction, dict):
                self.objects[name].setdefault("script_instructions", []).append(dict(instruction))
        elif command_type == "script_drop_at" and not playing:
            self._attach_script_at(command, selected_name)
        elif command_type == "create_object_at" and not playing:
            selected_name = self._create_object_at(command)
        elif command_type == "create_sprite_at" and not playing:
            selected_name = self._create_sprite_at(command)
        elif command_type == "reset_scene":
            self.emit({"type": "snapshot_requested"})
        return True, selected_name

    def _set_dictionary_component(self, command: dict[str, Any], key: str, playing: bool) -> None:
        name = str(command.get("name", ""))
        value = command.get(key)
        if name in self.objects and not playing and isinstance(value, dict):
            self.objects[name][key] = dict(value)

    def _attach_script_at(self, command: dict[str, Any], selected_name: str | None) -> None:
        mouse_x = float(command.get("screen_x", 0.0))
        mouse_y = float(command.get("screen_y", 0.0))
        target_name = None
        for name, obj in reversed(list(self.objects.items())):
            object_x, object_y = self.world_to_screen(float(obj["x"]), float(obj["y"]))
            angle = math.radians(-float(obj.get("rotation", 0.0)))
            dx, dy = mouse_x - object_x, mouse_y - object_y
            local_x = dx * math.cos(angle) - dy * math.sin(angle)
            local_y = dx * math.sin(angle) + dy * math.cos(angle)
            zoom = self.view_zoom()
            if abs(local_x) <= float(obj["w"]) * zoom / 2.0 and abs(local_y) <= float(obj["h"]) * zoom / 2.0:
                target_name = name
                break
        target_name = target_name or selected_name
        if target_name in self.objects:
            self.emit({"type": "attach_script", "name": target_name, "path": str(command.get("path", ""))})

    def _unique_name(self, base: str) -> str:
        name = base
        index = 1
        while name in self.objects:
            index += 1
            name = f"{base}_{index}"
        return name

    def _create_object_at(self, command: dict[str, Any]) -> str:
        kind = str(command.get("kind", "Sprite"))
        world_x, world_y = self.screen_to_world(float(command.get("screen_x", 0.0)), float(command.get("screen_y", 0.0)))
        presets = {
            "Empty": ("GameObject", 40.0, 40.0, (160, 164, 174), None),
            "Sprite": ("Sprite", 64.0, 64.0, (180, 180, 190), None),
            "Player": ("Player", 36.0, 48.0, (88, 117, 255), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Platform": ("Platform", 160.0, 32.0, (91, 194, 100), {"is_kinematic": True, "use_gravity": False}),
            "Enemy": ("Enemy", 40.0, 40.0, (220, 88, 88), {"is_kinematic": False, "use_gravity": True, "gravity_scale": 1.0}),
            "Trigger": ("Trigger", 80.0, 80.0, (222, 178, 72), {"is_kinematic": True, "use_gravity": False}),
            "Camera": ("Camera2D", 96.0, 54.0, (110, 190, 210), None),
        }
        base, width, height, color, rigidbody = presets.get(kind, presets["Sprite"])
        name = self._unique_name(base)
        obj = {"id": str(uuid.uuid4()), "name": name, "x": world_x, "y": world_y, "w": width, "h": height, "rotation": 0.0, "color": color, "mesh_type": kind}
        if rigidbody is not None:
            obj["rigidbody"] = rigidbody
            obj["collider"] = {"type": "box"}
        if kind == "Trigger":
            obj["collider"]["is_trigger"] = True
        if kind == "Player":
            obj["scripts"] = ["Assets/Scripts/player_controller_2d.py"]
        if kind == "Camera":
            obj["component_names"] = ["Camera2D"]
            obj["camera"] = {"active": True, "zoom": 1.0}
        return self._store_created(name, obj)

    def _create_sprite_at(self, command: dict[str, Any]) -> str:
        texture = str(command.get("texture", ""))
        name = self._unique_name(Path(texture).stem or "Sprite")
        world_x, world_y = self.screen_to_world(float(command.get("screen_x", 0.0)), float(command.get("screen_y", 0.0)))
        obj = {
            "id": str(uuid.uuid4()), "name": name, "x": world_x, "y": world_y,
            "w": float(command.get("width", 64.0)), "h": float(command.get("height", 64.0)),
            "rotation": 0.0, "color": (255, 255, 255), "mesh_type": "Sprite",
            "texture": texture, "renderer_enabled": True, "render_layer": "Default", "sort_order": 0,
        }
        return self._store_created(name, obj)

    def _store_created(self, name: str, obj: dict[str, Any]) -> str:
        self.objects[name] = obj
        self.emit({"type": "scene_snapshot", "objects": list(self.objects.values())})
        self.emit({"type": "selected", "name": name})
        return name

