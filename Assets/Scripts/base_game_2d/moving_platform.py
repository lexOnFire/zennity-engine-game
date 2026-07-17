"""Plataforma móvel horizontal fácil de reutilizar."""

CONFIG = {"distance": 90.0, "speed": 55.0}


def on_start(game):
    game.state["origin_x"] = game.x
    game.state["direction"] = 1.0


def on_update(game, dt):
    origin = game.state.get("origin_x", game.x)
    direction = game.state.get("direction", 1.0)
    game.move(direction * CONFIG["speed"] * dt)
    if game.x >= origin + CONFIG["distance"] or game.x <= origin - CONFIG["distance"]:
        game.state["direction"] = -direction

