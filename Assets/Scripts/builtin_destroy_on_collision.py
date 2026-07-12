"""Desativa o objeto quando colide com uma Tag."""

CONFIG = {"target_tag": "perigoso"}


def on_collision(game, other):
    if other.tag.lower() == CONFIG["target_tag"].lower():
        game.destroy()


def on_trigger(game, other):
    on_collision(game, other)
