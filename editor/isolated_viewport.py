"""Janela Pygame independente usada pelo experimento de viewport isolada."""
from __future__ import annotations

import math
from queue import Empty
from typing import Any


def _send(events: Any, payload: dict[str, Any]) -> None:
    if events is None:
        return
    try:
        events.put_nowait(payload)
    except Exception:
        pass


def run_viewport(commands: Any = None, events: Any = None) -> None:
    import pygame

    pygame.init()
    screen = pygame.display.set_mode((900, 700), pygame.RESIZABLE)
    pygame.display.set_caption("Zennity — Viewport isolada (Pygame)")
    clock = pygame.time.Clock()
    running = True
    objects = {
        "Chao": {"x": 450.0, "y": 500.0, "w": 600.0, "h": 32.0, "color": (91, 194, 100)},
        "Player": {"x": 450.0, "y": 250.0, "w": 36.0, "h": 48.0, "color": (88, 117, 255)},
    }
    dragging = False
    selected_name: str | None = None

    while running:
        if commands is not None:
            while True:
                try:
                    command = commands.get_nowait()
                except Empty:
                    break
                if command.get("type") == "shutdown":
                    running = False
                elif command.get("type") == "scene_snapshot":
                    objects = {item["name"]: dict(item) for item in command.get("objects", [])}
                    selected_name = None
                elif command.get("type") == "select_object":
                    name = str(command.get("name", ""))
                    if name in objects:
                        selected_name = name
                elif command.get("type") == "move_selected" and selected_name in objects:
                    obj = objects[selected_name]
                    obj["x"] += float(command.get("dx", 0.0))
                    obj["y"] += float(command.get("dy", 0.0))
                    _send(events, {"type": "transform", "name": selected_name, "x": obj["x"], "y": obj["y"]})
                elif command.get("type") == "reset_scene":
                    _send(events, {"type": "snapshot_requested"})

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, obj in reversed(list(objects.items())):
                    if abs(event.pos[0] - obj["x"]) <= obj["w"] / 2 and abs(event.pos[1] - obj["y"]) <= obj["h"] / 2:
                        dragging = True
                        selected_name = name
                        _send(events, {"type": "selected", "name": name})
                        break
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                if selected_name in objects:
                    objects[selected_name]["x"], objects[selected_name]["y"] = map(float, event.pos)
                    _send(events, {"type": "transform", "name": selected_name, "x": event.pos[0], "y": event.pos[1]})

        width, height = screen.get_size()
        screen.fill((22, 24, 31))
        for x in range(0, width, 32):
            pygame.draw.line(screen, (45, 48, 59), (x, 0), (x, height))
        for y in range(0, height, 32):
            pygame.draw.line(screen, (45, 48, 59), (0, y), (width, y))
        pygame.draw.line(screen, (112, 120, 142), (0, height // 2), (width, height // 2), 2)
        for name, obj in objects.items():
            box = pygame.Rect(int(obj["x"] - obj["w"] / 2), int(obj["y"] - obj["h"] / 2), int(obj["w"]), int(obj["h"]))
            pygame.draw.rect(screen, tuple(obj.get("color", (180, 180, 180))), box, border_radius=4)
            if name == selected_name:
                pygame.draw.rect(screen, (125, 212, 255), box.inflate(8, 8), 2, border_radius=4)
                pygame.draw.line(screen, (245, 78, 78), (obj["x"], obj["y"]), (obj["x"] + 92, obj["y"]), 4)
                pygame.draw.line(screen, (82, 211, 106), (obj["x"], obj["y"]), (obj["x"], obj["y"] - 92), 4)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
