"""Pulo com Espaço; requer Rigidbody com gravidade."""

CONFIG = {"jump_force": 420.0}


def on_update(game, dt):
    if game.key_pressed("space"):
        game.jump(CONFIG["jump_force"])
