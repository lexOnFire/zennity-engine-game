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
    player_x, player_y = 450.0, 250.0
    dragging = False
    selected = False

    while running:
        if commands is not None:
            while True:
                try:
                    command = commands.get_nowait()
                except Empty:
                    break
                if command.get("type") == "shutdown":
                    running = False
                elif command.get("type") == "select_player":
                    selected = True
                elif command.get("type") == "move_player":
                    player_x += float(command.get("dx", 0.0))
                    player_y += float(command.get("dy", 0.0))
                    _send(events, {"type": "transform", "x": player_x, "y": player_y})
                elif command.get("type") == "reset_player":
                    player_x, player_y = 450.0, 250.0
                    _send(events, {"type": "transform", "x": player_x, "y": player_y})

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if math.hypot(event.pos[0] - player_x, event.pos[1] - player_y) < 50:
                    dragging = True
                    selected = True
                    _send(events, {"type": "selected", "name": "Player"})
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                player_x, player_y = map(float, event.pos)
                _send(events, {"type": "transform", "x": player_x, "y": player_y})

        width, height = screen.get_size()
        screen.fill((22, 24, 31))
        for x in range(0, width, 32):
            pygame.draw.line(screen, (45, 48, 59), (x, 0), (x, height))
        for y in range(0, height, 32):
            pygame.draw.line(screen, (45, 48, 59), (0, y), (width, y))
        pygame.draw.line(screen, (112, 120, 142), (0, height // 2), (width, height // 2), 2)
        pygame.draw.rect(screen, (88, 117, 255), (player_x - 18, player_y - 24, 36, 48), border_radius=4)
        pygame.draw.rect(screen, (125, 212, 255) if selected else (86, 104, 155), (player_x - 22, player_y - 28, 44, 56), 2, border_radius=4)
        pygame.draw.line(screen, (245, 78, 78), (player_x, player_y), (player_x + 92, player_y), 4)
        pygame.draw.line(screen, (82, 211, 106), (player_x, player_y), (player_x, player_y - 92), 4)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
