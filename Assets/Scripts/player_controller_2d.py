"""Controle 2D simples usado pelo Player padrão."""

CONFIG = {"speed": 240.0, "jump_force": 420.0}


def on_update(game, dt):
    direction = game.axis("left", "right")
    game.move(direction * CONFIG["speed"] * dt)

    if game.key_pressed("space"):
        game.jump(CONFIG["jump_force"])


def on_instruction(game, instruction):
    if instruction.get("command") == "set_speed":
        CONFIG["speed"] = float(instruction.get("value", CONFIG["speed"]))
