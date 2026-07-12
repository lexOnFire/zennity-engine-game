"""Controle de jogador compatível com o Play Mode atual."""

CONFIG = {"speed": 240.0, "jump_force": 420.0}


def on_update(game, dt):
    game.move(game.axis("left", "right") * CONFIG["speed"] * dt)
    if game.key_pressed("space"):
        game.jump(CONFIG["jump_force"])
