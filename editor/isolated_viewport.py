"""Public entrypoint for the isolated Pygame viewport."""
from __future__ import annotations

import os
import sys
from typing import Any

try:
    from editor.runtime.viewport_asset_hydration import (
        hydrate_animation_asset_clips,
        hydrate_animator_controllers,
        hydrate_behavior_controllers,
        hydrate_logic_graphs,
        load_project_subgraph,
    )
    from editor.runtime.viewport_logic_api import (
        PlayAnimatorAPI,
        PlayBehaviorAPI,
        PlayLogicAPI,
        _send,
    )
    from editor.runtime.viewport_session import ViewportSession, _attach_native_window
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .viewport_asset_hydration import (
        hydrate_animation_asset_clips,
        hydrate_animator_controllers,
        hydrate_behavior_controllers,
        hydrate_logic_graphs,
        load_project_subgraph,
    )
    from .viewport_logic_api import PlayAnimatorAPI, PlayBehaviorAPI, PlayLogicAPI, _send
    from .viewport_session import ViewportSession, _attach_native_window


__all__ = [
    "PlayAnimatorAPI",
    "PlayBehaviorAPI",
    "PlayLogicAPI",
    "hydrate_animation_asset_clips",
    "hydrate_animator_controllers",
    "hydrate_behavior_controllers",
    "hydrate_logic_graphs",
    "load_project_subgraph",
    "run_viewport",
]


def run_viewport(
    commands: Any = None,
    events: Any = None,
    parent_window_id: int | None = None,
    initial_size: tuple[int, int] = (900, 700),
) -> None:
    import pygame

    if parent_window_id and sys.platform != "win32":
        os.environ["SDL_WINDOWID"] = str(parent_window_id)
    os.environ["PYGAME_PARACHUTE"] = "0"
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    display_flags = pygame.RESIZABLE
    if parent_window_id and sys.platform == "win32":
        display_flags |= pygame.NOFRAME
    screen = pygame.display.set_mode(initial_size, display_flags)
    pygame.display.set_caption("Zennity — Viewport isolada (Pygame)")

    embedded = _attach_native_window(pygame, parent_window_id, *initial_size)
    _send(events, {"type": "viewport_mode", "embedded": embedded})

    clock = pygame.time.Clock()
    session = ViewportSession(
        pygame, screen, display_flags, clock, commands, events, parent_window_id, initial_size
    )
    try:
        while session.running:
            try:
                session.process_commands()
                session.process_events()
                session.step()
                session.render()
                session.clock.tick(60)
                session.sync_stats()
            except Exception:
                session.running = False
    finally:
        try:
            session.teardown()
        except Exception:
            pass
        try:
            pygame.quit()
        except Exception:
            pass
