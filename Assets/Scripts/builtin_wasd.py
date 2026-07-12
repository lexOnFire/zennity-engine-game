"""Movimento 2D com WASD ou setas."""

CONFIG = {"speed": 200.0}


def on_update(game, dt):
    game.move(
        game.axis("left", "right") * CONFIG["speed"] * dt,
        game.axis("up", "down") * CONFIG["speed"] * dt,
    )
