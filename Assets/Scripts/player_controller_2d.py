"""Controle 2D simples usado pelo Player padrão."""

CONFIG = {"speed": 240.0, "jump_force": 420.0, "enabled": True}


def on_start(game):
    game.log("Player Controller ativo")


def on_update(game, dt):
    if not CONFIG["enabled"]:
        return

    direction = game.axis("left", "right")
    game.move(direction * CONFIG["speed"] * dt)

    if game.key_pressed("space"):
        game.jump(CONFIG["jump_force"])


def on_instruction(game, instruction):
    command = instruction.get("command")
    if command == "set_speed":
        CONFIG["speed"] = float(instruction.get("value", CONFIG["speed"]))
    elif command == "set_enabled":
        CONFIG["enabled"] = bool(instruction.get("value", True))
    elif command == "jump":
        game.jump(float(instruction.get("value", CONFIG["jump_force"])))


def on_stop(game):
    pass
