"""Rotação contínua simples."""

CONFIG = {"speed": 45.0}


def on_update(game, dt):
    game.rotation = (game.rotation + CONFIG["speed"] * dt) % 360.0
