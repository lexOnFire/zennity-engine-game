"""Public entrypoint for the isolated Pygame viewport."""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from engine.diagnostics import (
    get_logger,
    install_process_hooks,
    report_crash,
    set_context,
    setup_logging,
    swallow,
)

log = get_logger("viewport")

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
    # A multiprocessing child inherits none of the parent's logging or exception
    # hooks, so the viewport installs its own before touching pygame.  Without
    # this the process can die with no diagnostic whatsoever (Phase 9.5A P0 #3).
    setup_logging(Path.cwd(), process_name="Viewport")
    install_process_hooks(process_name="Viewport")
    set_context(process="Viewport", mode="Play")
    log.info("Viewport process starting (pid=%s, parent_window=%s)",
             os.getpid(), parent_window_id)

    import pygame

    if parent_window_id and sys.platform != "win32":
        os.environ["SDL_WINDOWID"] = str(parent_window_id)
    os.environ["PYGAME_PARACHUTE"] = "0"
    pygame.init()
    with swallow(log, "initialise the audio mixer (audio will be unavailable)",
                 level=logging.WARNING):
        pygame.mixer.init()

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
            except Exception as exc:
                # Behaviour is unchanged -- the frame loop still stops -- but the
                # reason is now recorded and pushed to the editor instead of the
                # process simply going dark (Phase 9.5A P0 #3).
                report_crash(
                    type(exc), exc, exc.__traceback__,
                    origin="viewport frame loop",
                    extra_context={"frame_stage": "main loop"},
                )
                _send(events, {
                    "type": "runtime_log",
                    "level": "ERROR",
                    "message": f"Viewport crashed: {type(exc).__name__}: {exc}",
                })
                _send(events, {
                    "type": "viewport_crashed",
                    "error": f"{type(exc).__name__}: {exc}",
                })
                session.running = False
    finally:
        with swallow(log, "tear down the viewport session"):
            session.teardown()
        with swallow(log, "shut down pygame"):
            pygame.quit()
        log.info("Viewport process exiting (pid=%s)", os.getpid())
