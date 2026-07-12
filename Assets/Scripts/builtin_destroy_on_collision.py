"""Desativa o objeto quando chega perto de uma Tag."""

CONFIG = {"target_tag": "perigoso", "distance": 24.0}


def on_update(game, dt):
    target = game.find(CONFIG["target_tag"])
    if target is not None and game.distance_to(target) <= CONFIG["distance"]:
        game.destroy()
