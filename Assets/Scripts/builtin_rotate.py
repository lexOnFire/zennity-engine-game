"""Rotação contínua 2D."""

CONFIG = {"speed": 60.0}


def on_update(game, dt):
    game.rotation = (game.rotation + CONFIG["speed"] * dt) % 360.0
