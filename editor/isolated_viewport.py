"""Janela Pygame independente usada pelo experimento de viewport isolada."""
from __future__ import annotations

import math
import os
import sys
from copy import deepcopy
from queue import Empty
from typing import Any


def _send(events: Any, payload: dict[str, Any]) -> None:
    if events is None:
        return
    try:
        events.put_nowait(payload)
    except Exception:
        pass


def _attach_native_window(pygame: Any, parent_window_id: int | None, width: int, height: int) -> bool:
    if not parent_window_id:
        return False
    if sys.platform != "win32":
        return bool(os.environ.get("SDL_WINDOWID"))
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = int(pygame.display.get_wm_info().get("window", 0))
        if not hwnd:
            return False
        user32 = ctypes.windll.user32
        user32.SetParent.argtypes = (wintypes.HWND, wintypes.HWND)
        user32.SetParent.restype = wintypes.HWND
        user32.SetWindowPos.argtypes = (
            wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, wintypes.UINT,
        )
        user32.SetWindowPos.restype = wintypes.BOOL

        long_ptr = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
        get_style = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
        set_style = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
        get_style.argtypes = (wintypes.HWND, ctypes.c_int)
        get_style.restype = long_ptr
        set_style.argtypes = (wintypes.HWND, ctypes.c_int, long_ptr)
        set_style.restype = long_ptr

        user32.SetParent(hwnd, int(parent_window_id))
        style = int(get_style(hwnd, -16))
        decorations = 0x00C00000 | 0x00080000 | 0x00040000 | 0x00020000 | 0x00010000
        style = (style | 0x40000000) & ~(0x80000000 | decorations)
        set_style(hwnd, -16, style)
        user32.SetWindowPos(hwnd, 0, 0, 0, int(width), int(height), 0x0020 | 0x0040 | 0x0004)
        return True
    except Exception:
        return False


def run_viewport(
    commands: Any = None,
    events: Any = None,
    parent_window_id: int | None = None,
    initial_size: tuple[int, int] = (900, 700),
) -> None:
    import pygame

    if parent_window_id and sys.platform != "win32":
        os.environ["SDL_WINDOWID"] = str(parent_window_id)
    pygame.init()
    display_flags = pygame.RESIZABLE
    if parent_window_id and sys.platform == "win32":
        display_flags |= pygame.NOFRAME
    screen = pygame.display.set_mode(initial_size, display_flags)
    pygame.display.set_caption("Zennity — Viewport isolada (Pygame)")
    embedded = _attach_native_window(pygame, parent_window_id, *initial_size)
    _send(events, {"type": "viewport_mode", "embedded": embedded})
    clock = pygame.time.Clock()
    running = True
    objects: dict[str, dict[str, Any]] = {}
    dragging = False
    selected_name: str | None = None
    active_tool = "select"
    drag_start_mouse = (0.0, 0.0)
    drag_start_object: dict[str, Any] = {}
    playing = False
    edit_snapshot = deepcopy(objects)
    velocities_y: dict[str, float] = {}

    while running:
        if commands is not None:
            while True:
                try:
                    command = commands.get_nowait()
                except Empty:
                    break
                if command.get("type") == "shutdown":
                    running = False
                elif command.get("type") == "viewport_size":
                    new_size = (max(32, int(command.get("w", 32))), max(32, int(command.get("h", 32))))
                    screen = pygame.display.set_mode(new_size, display_flags)
                    _attach_native_window(pygame, parent_window_id, *new_size)
                elif command.get("type") == "scene_snapshot":
                    objects = {item["name"]: dict(item) for item in command.get("objects", [])}
                    edit_snapshot = deepcopy(objects)
                    selected_name = None
                    playing = False
                    velocities_y = {}
                elif command.get("type") == "set_tool":
                    tool = str(command.get("tool", "select")).lower()
                    if tool in {"select", "move", "rotate", "scale"}:
                        active_tool = tool
                elif command.get("type") == "play":
                    if not playing:
                        edit_snapshot = deepcopy(objects)
                        playing = True
                        velocities_y = {}
                        _send(events, {"type": "play_state", "state": "play"})
                elif command.get("type") == "stop":
                    if playing:
                        objects = deepcopy(edit_snapshot)
                        playing = False
                        velocities_y = {}
                        _send(events, {"type": "play_state", "state": "edit"})
                        _send(events, {"type": "scene_snapshot", "objects": list(objects.values())})
                elif command.get("type") == "select_object":
                    name = str(command.get("name", ""))
                    if name in objects:
                        selected_name = name
                        _send(events, {"type": "selected", "name": name})
                elif command.get("type") == "move_selected" and selected_name in objects:
                    obj = objects[selected_name]
                    obj["x"] += float(command.get("dx", 0.0))
                    obj["y"] += float(command.get("dy", 0.0))
                    _send(events, {"type": "transform", "name": selected_name, "x": obj["x"], "y": obj["y"]})
                elif command.get("type") == "set_transform":
                    name = str(command.get("name", ""))
                    if name in objects and not playing:
                        obj = objects[name]
                        for key in ("x", "y", "w", "h"):
                            if key in command:
                                obj[key] = float(command[key])
                        _send(events, {"type": "transform", "name": name, **{key: obj[key] for key in ("x", "y", "w", "h")}})
                elif command.get("type") == "set_physics":
                    name = str(command.get("name", ""))
                    if name in objects and not playing and isinstance(command.get("rigidbody"), dict):
                        objects[name]["rigidbody"] = dict(command["rigidbody"])
                elif command.get("type") == "reset_scene":
                    _send(events, {"type": "snapshot_requested"})

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not playing:
                for name, obj in reversed(list(objects.items())):
                    if abs(event.pos[0] - obj["x"]) <= obj["w"] / 2 and abs(event.pos[1] - obj["y"]) <= obj["h"] / 2:
                        dragging = True
                        selected_name = name
                        drag_start_mouse = (float(event.pos[0]), float(event.pos[1]))
                        drag_start_object = deepcopy(obj)
                        _send(events, {"type": "selected", "name": name})
                        if active_tool != "select":
                            _send(events, {"type": "transform_begin", "name": name})
                        else:
                            dragging = False
                        break
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging and selected_name is not None:
                    _send(events, {"type": "transform_end", "name": selected_name})
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging and not playing:
                if selected_name in objects:
                    obj = objects[selected_name]
                    if active_tool == "move":
                        obj["x"], obj["y"] = map(float, event.pos)
                    elif active_tool == "rotate":
                        obj["rotation"] = math.degrees(math.atan2(event.pos[1] - obj["y"], event.pos[0] - obj["x"]))
                    elif active_tool == "scale":
                        dx = float(event.pos[0]) - drag_start_mouse[0]
                        dy = float(event.pos[1]) - drag_start_mouse[1]
                        obj["w"] = max(1.0, float(drag_start_object.get("w", obj["w"])) + dx * 2.0)
                        obj["h"] = max(1.0, float(drag_start_object.get("h", obj["h"])) + dy * 2.0)
                    _send(events, {"type": "transform", "name": selected_name, **{key: obj.get(key, 0.0) for key in ("x", "y", "w", "h", "rotation")}})

        width, height = screen.get_size()
        dt = clock.get_time() / 1000.0
        if playing:
            static_colliders = [obj for obj in objects.values() if obj.get("collider") and (obj.get("rigidbody") or {}).get("is_kinematic", True)]
            for name, obj in objects.items():
                rigidbody = obj.get("rigidbody") or {}
                if rigidbody.get("is_kinematic", False) or not rigidbody.get("use_gravity", False):
                    continue
                velocity = velocities_y.get(name, 0.0) + 980.0 * float(rigidbody.get("gravity_scale", 1.0)) * dt
                previous_bottom = obj["y"] + obj["h"] / 2
                obj["y"] += velocity * dt
                for floor in static_colliders:
                    overlaps_x = abs(obj["x"] - floor["x"]) * 2 < obj["w"] + floor["w"]
                    floor_top = floor["y"] - floor["h"] / 2
                    player_bottom = obj["y"] + obj["h"] / 2
                    if overlaps_x and previous_bottom <= floor_top and player_bottom >= floor_top:
                        obj["y"] = floor_top - obj["h"] / 2
                        velocity = 0.0
                        break
                velocities_y[name] = velocity
        screen.fill((22, 24, 31))
        for x in range(0, width, 32):
            pygame.draw.line(screen, (45, 48, 59), (x, 0), (x, height))
        for y in range(0, height, 32):
            pygame.draw.line(screen, (45, 48, 59), (0, y), (width, y))
        pygame.draw.line(screen, (112, 120, 142), (0, height // 2), (width, height // 2), 2)
        for name, obj in objects.items():
            box = pygame.Rect(int(obj["x"] - obj["w"] / 2), int(obj["y"] - obj["h"] / 2), int(obj["w"]), int(obj["h"]))
            object_surface = pygame.Surface((max(1, box.width), max(1, box.height)), pygame.SRCALPHA)
            pygame.draw.rect(object_surface, tuple(obj.get("color", (180, 180, 180))), object_surface.get_rect(), border_radius=4)
            rotated = pygame.transform.rotate(object_surface, -float(obj.get("rotation", 0.0)))
            screen.blit(rotated, rotated.get_rect(center=(obj["x"], obj["y"])))
            if name == selected_name:
                pygame.draw.rect(screen, (125, 212, 255), box.inflate(8, 8), 2, border_radius=4)
                if active_tool == "move":
                    pygame.draw.line(screen, (245, 78, 78), (obj["x"], obj["y"]), (obj["x"] + 92, obj["y"]), 4)
                    pygame.draw.line(screen, (82, 211, 106), (obj["x"], obj["y"]), (obj["x"], obj["y"] - 92), 4)
                elif active_tool == "rotate":
                    pygame.draw.circle(screen, (245, 194, 78), (int(obj["x"]), int(obj["y"])), int(max(obj["w"], obj["h"]) / 2 + 20), 3)
                elif active_tool == "scale":
                    for point in (box.topleft, box.topright, box.bottomleft, box.bottomright):
                        pygame.draw.rect(screen, (125, 212, 255), (point[0] - 4, point[1] - 4, 8, 8))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
