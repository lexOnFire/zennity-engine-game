# Integração BoxCollider + RigidBody + TilemapCollider

Este documento explica como conectar o sistema de física 2D da Zennity Engine com o sistema de TileMap para fazer colisão player↔tilemap.

---

## Arquitetura da Integração

```
 ┌──────────────────────────────────────────────────────────────┐
 │  Scene.update(dt)                                            │
 │                                                              │
 │  1. Input do player  →  rb.velocity[0] = vx                 │
 │  2. RigidBody.update(dt)  →  move transform (gravity + vel) │
 │  3. TilemapCollider.resolve(player)  →  corrige penetração   │
 │     └─ seta rb.grounded = True se pousou no chão             │
 │  4. TilemapCollider.resolve_one_way(player, prev_bottom)     │
 │     └─ plataformas one-way (passáveis por baixo)             │
 │  5. BoxCollider.check_all()  →  colisões objeto↔objeto       │
 └──────────────────────────────────────────────────────────────┘
```

**Atenção:** A ordem importa. O `TilemapCollider` deve ser chamado **depois** do `RigidBody.update()` e **antes** do `BoxCollider.check_all()`.

---

## Uso Básico

### 1. Configuração do TileMap

```python
from engine.tilemap import TileMap, TileLayer, Tileset
from engine.physics import TilemapCollider

# Cria o tileset (com propriedades de colisão)
tileset = Tileset("mapa", surface, tile_w=32, tile_h=32, first_gid=1)
tileset.set_tile_property(1, "solid",   True)  # bloqueia todas as direções
tileset.set_tile_property(2, "one_way", True)  # bloqueia só de cima
tileset.set_tile_property(3, "damage",  True)  # causa dano (detecte no update)

# Cria o TilemapCollider
tm_collider = TilemapCollider(
    tilemap,
    layer_name="collision",  # nome da camada com tiles sólidos
    max_iter=4,              # iterações de resolução por frame
)
```

### 2. Configuração do Player

```python
from engine.physics import RigidBody, BoxCollider

player = GameObject("Player")
rb  = player.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
col = player.add_component(BoxCollider(width=28, height=32))
```

### 3. Loop de Update

```python
def update(self, dt: float) -> None:
    # 1. Input
    rb.velocity[0] = WALK_SPEED if key_right else (-WALK_SPEED if key_left else 0)

    # 2. Salva bottom antes do step (para one-way)
    prev_bottom = col.rect.bottom

    # 3. Física
    rb.update(dt)

    # 4. Colisão tilemap
    tm_collider.resolve(player)              # tiles sólidos
    tm_collider.resolve_one_way(player, prev_bottom)  # plataformas

    # 5. Colisão entre objetos
    BoxCollider.check_all()

    # 6. Pulo (depende do grounded que o resolve() define)
    if key_jump and rb.grounded:
        rb.velocity[1] = -440.0
```

---

## Propriedades dos Tiles

| Propriedade | GID | Comportamento |
|-------------|-----|---------------|
| `solid`     | qualquer | Bloqueia colisão em todas as direções via `resolve()` |
| `one_way`   | qualquer | Bloqueia só ao cair de cima via `resolve_one_way()` |
| `damage`    | qualquer | Não bloqueia — detecte manualmente no `update()` |
| `trigger`   | qualquer | Não bloqueia — para usar com `BoxCollider(is_trigger=True)` |

---

## Multi-objeto

Para resolver vários objetos de uma vez:

```python
tm_collider.resolve_all([player, enemy1, enemy2])
```

---

## Referência da API

### `TilemapCollider(tilemap, layer_name, max_iter)`

| Parâmetro    | Tipo  | Padrão       | Descrição |
|--------------|-------|--------------|-------------------------------------------------------------|
| `tilemap`    | TileMap | —          | O mapa usado para colisão |
| `layer_name` | str   | `"collision"` | Nome da camada com tiles sólidos |
| `max_iter`   | int   | `4`          | Máximo de iterações de resolução por frame |

### Métodos

| Método | Descrição |
|--------|-----------|
| `resolve(game_object)` | Resolve colisões com tiles `solid` para um objeto |
| `resolve_all(list)` | Resolve para uma lista de objetos |
| `resolve_one_way(game_object, prev_bottom)` | Resolve plataformas `one_way` |

---

## Demo

Rode o platformer de exemplo:

```bash
python -m demos.demo_platformer
```

### Controles da demo

| Tecla       | Ação |
|-------------|------|
| `← →` / `A D` | Mover |
| `Espaço` / `↑` / `W` | Pular (duplo pulo ativado) |
| `F1` | Toggle debug (desenha colliders e tile rects) |
| `ESC` | Sair |

---

## Diagrama de Fluxo de Colisão

```
player.rect (BoxCollider)
       │
       ▼
get_solid_rects_in_region()   ← TileMap consulta tiles sólidos ao redor
       │
       ▼
Para cada tile sólido com overlap:
  overlap_x < overlap_y?  →  resolve horizontal (empurra X)
  overlap_y ≤ overlap_x?  →  resolve vertical   (empurra Y)
       │
       ├─ vindo de cima → rb.grounded = True, rb.velocity[1] = 0
       └─ vindo de baixo → rb.velocity[1] = 0  (bate na cabeça)
```
