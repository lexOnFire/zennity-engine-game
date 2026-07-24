"""Mostra o estado ativo do Behavior Controller na Game View."""


def on_update(game, dt):
    state = game.behavior.state
    distance = game.behavior.parameters.get("player_distance", 0.0)
    game.set_hud("behavior_state", f"BEHAVIOR: {state}", (112, 255, 163), "top-left", 24)
    game.set_hud("behavior_distance", f"Distância do Player: {distance:.0f}", (225, 230, 240), "top-left", 18)
