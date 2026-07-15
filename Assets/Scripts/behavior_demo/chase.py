"""Estado Chase: aproxima o inimigo do Player."""


def on_enter(game):
    game.log("Behavior: entrou em Chase")


def on_update(game, dt):
    player = game.find("Player")
    if player is None:
        game.behavior.set_float("player_distance", 999.0)
        return
    distance = game.distance_to(player)
    game.behavior.set_float("player_distance", distance)
    direction = 1 if player.x > game.x else -1
    game.move(direction * 90.0 * dt)
    if distance < 65.0:
        game.behavior.trigger("attack")


def on_exit(game):
    game.log("Behavior: saiu de Chase")
