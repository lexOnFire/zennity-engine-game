"""Estado Patrol: movimento simples de patrulha."""


def on_enter(game):
    game.state["patrol_direction"] = 1
    game.log("Behavior: entrou em Patrol")


def on_update(game, dt):
    game.move(40.0 * game.state.get("patrol_direction", 1) * dt)


def on_exit(game):
    game.log("Behavior: saiu de Patrol")
