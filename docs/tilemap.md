# 🗺️ Sistema de Tilemap — Zennity Engine

## Visão Geral

O sistema de Tilemap é composto por três módulos principais:

| Módulo | Arquivo | Responsabilidade |
|---|---|---|
| `Tileset` | `engine/tilemap/tileset.py` | Fatia spritesheet e armazena metadata por tile |
| `TileMap` | `engine/tilemap/tilemap.py` | Mapa multi-camadas com colisão e renderização |
| `TilemapLoader` | `engine/tilemap/tilemap_loader.py` | Carrega mapas de JSON (Tiled ou formato nativo) |

---

## Uso Rápido

```python
from engine.tilemap import TileMap, TileLayer, Tileset, TileData, TilemapLoader

# 1. Carregar tileset
ts = Tileset("assets/tileset.png", tile_width=32, tile_height=32, first_gid=1)
ts.load()
ts.set_tile_data(1, TileData(tile_id=1, solid=True))
ts.set_tile_data(2, TileData(tile_id=2, solid=True, one_way=True))

# 2. Criar mapa
tilemap = TileMap(tile_width=32, tile_height=32, map_width=20, map_height=15)
tilemap.add_tileset(ts)

# 3. Criar camadas
data = [1]*20 + [0]*(20*14)   # linha de chão no topo
layer = TileLayer("collision", 20, 15, data, z_index=0)
tilemap.add_layer(layer)

# 4. Bake (mapas estáticos — opcional mas recomendado)
tilemap.bake()

# 5. Desenhar na cena
def draw(self, screen):
    self.tilemap.draw(screen, cam_x=self.cam_x, cam_y=self.cam_y)
```

---

## Carregando de JSON

### Formato Zennity Nativo

```json
{
    "tile_width":  32,
    "tile_height": 32,
    "map_width":   20,
    "map_height":  15,
    "tilesets": [
        {
            "image":       "assets/tileset.png",
            "tile_width":  32,
            "tile_height": 32,
            "first_gid":   1,
            "tile_data": {
                "1": { "solid": true },
                "2": { "solid": true, "one_way": true },
                "5": { "damage": 10 }
            }
        }
    ],
    "layers": [
        { "name": "background", "z_index": 0, "data": [3, 3, 3, ...] },
        { "name": "collision",  "z_index": 1, "data": [0, 1, 1, ...] }
    ]
}
```

```python
tilemap = TilemapLoader.load("maps/level1.json")
```

### Tiled JSON Export

Exporte seu mapa do Tiled como **JSON Map File** (sem compressão).
Use a propriedade customizada `solid = true` nos tiles para marcar colisão.

```python
tilemap = TilemapLoader.load("maps/level1.json")  # detecta Tiled automaticamente
```

---

## Colisão com o Sistema de Física

```python
# Verificar se um ponto do mundo é sólido
if tilemap.is_solid_at(player_x, player_y):
    ...

# Obter rects sólidos para resolução AABB
rects = tilemap.get_solid_rects_in_region(px, py, width, height)
for rect in rects:
    # resolver colisão com o jogador
    ...
```

---

## Propriedades dos Tiles

| Campo | Tipo | Descrição |
|---|---|---|
| `solid` | bool | Bloqueia movimento |
| `one_way` | bool | Plataforma passável por baixo |
| `damage` | int | Dano ao contato (0 = nenhum) |
| `custom` | dict | Dados livres (`{"type": "lava"}`) |

---

## Performance — Baking

Para mapas **estáticos**, chame `tilemap.bake()` após configurar todas as camadas.
Isso pré-renderiza tudo em uma única Surface e reduz drasticamente o custo de draw.

Se tiles mudarem em runtime (ex: blocos destrutíveis), chame
`tilemap.invalidate_bake()` para forçar re-render dinâmico.

---

## Debug

```python
# Desenha bordas vermelhas nos tiles sólidos
tilemap.draw_debug(screen, cam_x, cam_y, layer_name="collision")
```

Pressione **F1** no `demo_tilemap.py` para ativar o debug de colisão.
