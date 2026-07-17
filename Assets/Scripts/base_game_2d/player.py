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
    _refresh_hud(game)
    _set_ui_text(game, "HUD_Controles", "A/D: mover   ESPAÇO: pular   R: reiniciar", "controls", (180, 195, 220), "bottom-left", 19)
    _set_ui_text(game, "HUD_Resultado", "", "result", (255, 255, 255), "center", 34)


def on_update(game, dt):
    if game.key_pressed("r"):
        game.restart()
        return
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

    if command == "restart_game":
        game.restart()
    elif command == "add_coin" and game.state.get("status") == "playing":
        game.state["coins"] += int(value or 1)
        game.log(f"MOEDAS: {game.state['coins']}/{CONFIG['coins_to_win']}")
        _refresh_hud(game)
    elif command == "damage" and game.state.get("status") == "playing":
        _take_damage(game, int(value or 1))
    elif command == "finish" and game.state.get("status") == "playing":
        if game.state.get("coins", 0) >= CONFIG["coins_to_win"]:
            game.state["status"] = "victory"
            game.log("VOCÊ VENCEU! Aperte Stop e Play para jogar novamente.")
            _set_ui_text(game, "HUD_Resultado", "VOCÊ VENCEU!  Pressione R para reiniciar", "result", (117, 255, 151), "center", 34)
        else:
            missing = CONFIG["coins_to_win"] - game.state.get("coins", 0)
            game.log(f"A saída está bloqueada. Faltam {missing} moeda(s).")


def _take_damage(game, amount):
    game.state["health"] = max(0, game.state.get("health", CONFIG["max_health"]) - amount)
    game.log(f"VIDA: {game.state['health']}/{CONFIG['max_health']}")
    _refresh_hud(game)
    if game.state["health"] <= 0:
        game.state["status"] = "defeat"
        game.log("GAME OVER! Aperte Stop e Play para reiniciar.")
        _set_ui_text(game, "HUD_Resultado", "GAME OVER  |  Pressione R para reiniciar", "result", (255, 105, 115), "center", 34)


def _refresh_hud(game):
    health = game.state.get("health", CONFIG["max_health"])
    coins = game.state.get("coins", 0)
    _set_ui_text(game, "HUD_Vida", f"VIDA: {health}/{CONFIG['max_health']}", "health", (255, 115, 125), "top-left", 24)
    _set_ui_text(game, "HUD_Moedas", f"MOEDAS: {coins}/{CONFIG['coins_to_win']}", "coins", (255, 218, 82), "top-right", 24)


def _set_ui_text(game, object_name, text, legacy_key, color, position, font_size):
    """Usa UI nativa e mantém scripts compatíveis com runtimes antigos."""
    if hasattr(game, "set_ui_text"):
        game.set_ui_text(object_name, text)
    else:
        game.set_hud(legacy_key, text, color, position, font_size)
