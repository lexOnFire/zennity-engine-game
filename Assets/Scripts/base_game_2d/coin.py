"""Moeda coletável: envia um ponto ao Player e desaparece."""


def on_update(game, dt):
    # Rotação simples deixa o coletável visualmente vivo.
    game.rotation = (game.rotation + 120.0 * dt) % 360.0


def on_trigger(game, other):
    if game.active and other.tag.lower() == "player":
        game.active = False
        other.send("add_coin", 1)

