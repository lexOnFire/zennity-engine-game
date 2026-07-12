"""Segue suavemente o objeto com Tag Player."""

CONFIG = {"speed": 150.0, "target_tag": "Player", "stop_distance": 8.0}


def on_update(game, dt):
    target = game.find(CONFIG["target_tag"])
    if target is None:
        return
    distance = game.distance_to(target)
    if distance <= CONFIG["stop_distance"]:
        return
    step = min(CONFIG["speed"] * dt, distance)
    game.move((target.x - game.x) / distance * step, (target.y - game.y) / distance * step)
