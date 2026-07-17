"""Inimigo que patrulha horizontalmente e causa dano ao Player."""

CONFIG = {"distance": 110.0, "speed": 85.0, "damage": 1}


def on_start(game):
    game.state["origin_x"] = game.x
    game.state["direction"] = 1.0


def on_update(game, dt):
    origin = game.state.get("origin_x", game.x)
    direction = game.state.get("direction", 1.0)
    game.move(direction * CONFIG["speed"] * dt)

    if game.x >= origin + CONFIG["distance"]:
        game.x = origin + CONFIG["distance"]
        game.state["direction"] = -1.0
    elif game.x <= origin - CONFIG["distance"]:
        game.x = origin - CONFIG["distance"]
        game.state["direction"] = 1.0


def on_trigger(game, other):
    if other.tag.lower() != "player":
        return
    other.send("damage", CONFIG["damage"])
    # Pequeno empurrão para separar os colliders e permitir novo contato.
    push = -55.0 if other.x < game.x else 55.0
    other.move(push, -20.0)

