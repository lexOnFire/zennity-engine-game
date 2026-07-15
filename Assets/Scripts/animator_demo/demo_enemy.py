"""Alvo simples da demo de ataque."""


def on_start(game):
    game.state["health"] = 3


def on_update(game, dt):
    game.set_hud("enemy_health", f"ALVO: {game.state.get('health', 3)} HP", (255, 116, 126), "top-right", 20)


def on_instruction(game, instruction):
    if instruction.get("command") != "damage":
        return
    game.state["health"] = max(0, game.state.get("health", 3) - int(instruction.get("value") or 1))
    game.log(f"Dano recebido. HP={game.state['health']}")
    if game.state["health"] <= 0:
        game.active = False
        game.remove_hud("enemy_health")
