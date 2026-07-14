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

Animator Controller:

```python
def on_update(game, dt):
    direcao = game.axis("left", "right")
    game.animator.set_float("velocidade", abs(direcao))

    if game.key_pressed("space"):
        game.animator.trigger("pular")

    # Também é possível trocar diretamente para um estado:
    # game.animator.play("andar")
```

No script, use o nome do **parâmetro** ou do **estado** exatamente como aparece
no Animator Controller. O restante é decidido pelas transições configuradas na aba Animação.

Eventos de animação:

```python
def on_animation_event(game, event):
    if event == "passo":
        game.play_sound("Assets/Audio/passo.wav")
    elif event == "ataque":
        game.log("Ativar o dano do ataque")
```

O payload opcional fica disponível em `game.state["animation_event_payload"]`.

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
