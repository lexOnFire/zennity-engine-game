"""Hitbox temporária ativada pelo evento do frame de ataque."""


def on_trigger(game, other):
    if other.tag.lower() == "enemy":
        other.send("damage", 1)
        game.active = False
        game.log("Ataque acertou " + other.name)
