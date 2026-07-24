"""Pulso de tamanho suave."""

import math

CONFIG = {"amount": 0.25, "speed": 4.0}


def on_update(game, dt):
    state = game.state
    state.setdefault("time", 0.0)
    state.setdefault("width", game.width)
    state.setdefault("height", game.height)
    state["time"] += dt
    scale = 1.0 + math.sin(state["time"] * CONFIG["speed"]) * CONFIG["amount"]
    game.width = state["width"] * scale
    game.height = state["height"] * scale
