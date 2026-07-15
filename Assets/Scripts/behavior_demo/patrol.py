"""Estado Patrol: movimento simples de patrulha."""


def on_enter(game):
    game.state["patrol_direction"] = 1
    game.log("Behavior: entrou em Patrol")


def on_update(game, dt):
    game.move(40.0 * game.state.get("patrol_direction", 1) * dt)
    player = game.find("Player")
    game.behavior.set_float("player_distance", game.distance_to(player) if player else 999.0)


def on_exit(game):
    game.log("Behavior: saiu de Patrol")
