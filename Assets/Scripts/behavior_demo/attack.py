"""Estado Attack: demonstra entrada, atualização e saída de estado."""


def on_enter(game):
    game.state["attack_time"] = 0.0
    game.play_animation("Attack")
    game.log("Behavior: entrou em Attack")


def on_update(game, dt):
    game.state["attack_time"] += dt
    if game.state["attack_time"] >= 0.45:
        game.behavior.trigger("attack_finished")


def on_exit(game):
    game.log("Behavior: saiu de Attack")
