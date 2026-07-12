"""Faz a câmera seguir o Player suavemente."""

# CONFIGURAÇÃO — altere somente estes valores.
SUAVIDADE = 5.0
ALVO = "Player"
OFFSET_X = 0.0
OFFSET_Y = 0.0


def on_update(game, dt):
    player = game.find(ALVO)
    if player is None:
        return

    aproximacao = min(1.0, SUAVIDADE * dt)
    destino_x = player.x + OFFSET_X
    destino_y = player.y + OFFSET_Y
    game.move(
        (destino_x - game.x) * aproximacao,
        (destino_y - game.y) * aproximacao,
    )
