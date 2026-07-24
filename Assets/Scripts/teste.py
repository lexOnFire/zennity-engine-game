"""teste — script simples do Zennity."""
import math



CONFIG = {"speed": 200.0, "jump_force": 420.0}
CONFIG_BALA = {"speed": 400.0, "direction_x": 1.0, "direction_y": 0.0, "lifetime": 2.0, "hit_tag": "Enemy", "hit_radius": 16.0}


def on_update(game, dt):
    """Coloque aqui o que o objeto faz durante o Play."""
    direction = game.axis("left", "right")
    game.move(direction * CONFIG["speed"] * dt)

    if game.key_pressed("space"):
        dx = float(CONFIG_BALA["direction_x"])
        dy = float(CONFIG_BALA["direction_y"])
        length = math.hypot(dx, dy) or 1.0
        game.move(dx / length * float(CONFIG_BALA["speed"]) * dt, dy / length * float(CONFIG_BALA["speed"]) * dt)
        game.state["elapsed"] = float(game.state.get("elapsed", 0.0)) + dt
        target = game.find(CONFIG_BALA["hit_tag"])
        if game.state["elapsed"] >= float(CONFIG_BALA["lifetime"]) or (
            target is not None and game.distance_to(target) <= float(CONFIG_BALA["hit_radius"])
        ):
            game.destroy()


# Opcional: receba comandos enviados por outros scripts/sistemas.
def on_instruction(game, instruction):
    if instruction.get("command") == "projectile":
        game.x = float(instruction.get("x", game.x))
        game.y = float(instruction.get("y", game.y))
