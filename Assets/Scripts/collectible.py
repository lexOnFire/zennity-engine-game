"""Coleta este objeto quando o Player chega perto."""

# CONFIGURAÇÃO — altere somente estes valores.
RAIO_DE_COLETA = 24.0
ALVO = "Player"


def on_update(game, dt):
    player = game.find(ALVO)
    if player is None:
        return

    if game.distance_to(player) <= RAIO_DE_COLETA:
        game.log("Item coletado")
        game.destroy()
