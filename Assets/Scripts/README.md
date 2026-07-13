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
- `game.set_hud("vida", "VIDA: 3")` cria ou atualiza texto na Game View.
- `game.remove_hud("vida")` remove um texto do HUD.
- `game.restart()` restaura a cena ao estado inicial do Play Mode.

Eventos de Collider:

```python
def on_collision(game, other):
    game.log("Colidiu com " + other.name)


def on_trigger(game, other):
    game.log("Entrou no trigger " + other.name)
```

Use `on_collision_exit` e `on_trigger_exit` para detectar a saída do contato.

Exemplo mínimo:

```python
VELOCIDADE = 200.0


def on_update(game, dt):
    direcao = game.axis("left", "right")
    game.move(direcao * VELOCIDADE * dt)
```

HUD simples:

```python
def on_start(game):
    game.set_hud("objetivo", "Colete todas as moedas", (255, 220, 80), "top-left")
```

Posições disponíveis: `top-left`, `top-right`, `bottom-left`, `bottom-right` e
`center`.
