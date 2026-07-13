"""Jogador do projeto-base 2D.

Controles: A/D ou setas para andar; Espaço para pular.
"""

CONFIG = {
    "speed": 260.0,
    "jump_force": 460.0,
    "max_health": 3,
    "coins_to_win": 5,
    "spawn_x": 120.0,
    "spawn_y": 590.0,
}


def on_start(game):
    game.state.update({"health": CONFIG["max_health"], "coins": 0, "status": "playing"})
    game.log("JOGO INICIADO | A/D: mover | ESPAÇO: pular | Colete 5 moedas")


def on_update(game, dt):
    if game.state.get("status") != "playing":
        return

    direction = game.axis("left", "right")
    game.move(direction * CONFIG["speed"] * dt)

    if game.key_pressed("space"):
        game.jump(CONFIG["jump_force"])

    # Segurança caso o jogador caia fora da fase.
    if game.y > 760.0:
        _take_damage(game, 1)
        game.x, game.y = CONFIG["spawn_x"], CONFIG["spawn_y"]


def on_instruction(game, instruction):
    command = instruction.get("command")
    value = instruction.get("value")

    if command == "add_coin" and game.state.get("status") == "playing":
        game.state["coins"] += int(value or 1)
        game.log(f"MOEDAS: {game.state['coins']}/{CONFIG['coins_to_win']}")
    elif command == "damage" and game.state.get("status") == "playing":
        _take_damage(game, int(value or 1))
    elif command == "finish" and game.state.get("status") == "playing":
        if game.state.get("coins", 0) >= CONFIG["coins_to_win"]:
            game.state["status"] = "victory"
            game.log("VOCÊ VENCEU! Aperte Stop e Play para jogar novamente.")
        else:
            missing = CONFIG["coins_to_win"] - game.state.get("coins", 0)
            game.log(f"A saída está bloqueada. Faltam {missing} moeda(s).")


def _take_damage(game, amount):
    game.state["health"] = max(0, game.state.get("health", CONFIG["max_health"]) - amount)
    game.log(f"VIDA: {game.state['health']}/{CONFIG['max_health']}")
    if game.state["health"] <= 0:
        game.state["status"] = "defeat"
        game.log("GAME OVER! Aperte Stop e Play para reiniciar.")

