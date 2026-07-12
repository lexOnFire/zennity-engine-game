# Scripts simples do Zennity

Edite apenas a seção **CONFIGURAÇÃO** no topo de cada script.

- `on_start(game)` roda uma vez quando o Play começa.
- `on_update(game, dt)` roda em todos os frames.
- `game.move(x, y)` move o objeto.
- `game.find("Player")` procura um objeto pela Tag.
- `game.key("right")` verifica uma tecla.
- `game.key_pressed("space")` verifica o primeiro toque.
- `game.state` guarda valores do script.
- `game.destroy()` remove o objeto.

Exemplo mínimo:

```python
VELOCIDADE = 200.0


def on_update(game, dt):
    direcao = game.axis("left", "right")
    game.move(direcao * VELOCIDADE * dt)
```
