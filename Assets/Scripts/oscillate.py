"""Oscilação vertical suave."""

import math

CONFIG = {"height": 71.0, "speed": 10.0}


def on_update(game, dt):
    state = game.state
    state.setdefault("time", 0.0)
    state.setdefault("initial_y", game.y)
    state["time"] += dt
    game.y = state["initial_y"] + math.sin(state["time"] * CONFIG["speed"]) * CONFIG["height"]