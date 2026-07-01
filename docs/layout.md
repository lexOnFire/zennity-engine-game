# Sistema de Layout do Editor

> `editor/layout.py` · `editor/layout_constants.py` · `editor/widgets/panel_base.py`

## Objetivo

Centralizar **todas as constantes, métricas e cálculos de posição** dos painéis do editor num único módulo, eliminando _magic numbers_ espalhados pelo código e tornando o layout responsivo a redimensionamentos da janela.

---

## Estrutura dos Painéis

```
┌──────────────────────────────────────────────────────────────┐  TOP_BAR_H = 30px
│  Zennity  │ File  View  Window    ▶ PLAY     ↩ 3  ↪ 0       │
├────────────┬────────────────────────────────┬────────────────┤
│            │                                │                │
│   LEFT     │         VIEWPORT               │   RIGHT        │
│  PANEL     │       (Edit Mode)              │  INSPECTOR     │
│  232 px    │                                │   230 px       │
│            │  ← viewport_w = screen_w       │                │
│  Outliner  │       - 232 - 230 →            │  Transform     │
│  Formas    │                                │  Física        │
│  Gizmo     │                                │  Scripts       │
│  Undo/Redo │                                │  Cor / Tag     │
│            │                                │                │
├────────────┴────────────────────────────────┴────────────────┤  STATUS_BAR_H = 22px
│  2 objeto(s)  Grade: OFF  Hist: 3 undo / 0 redo    ● Salvo! │
└──────────────────────────────────────────────────────────────┘
```

### Modo Play (Split View)

```
├────────────┬───────────────────┬──────────────────┬──────────┤
│  LEFT      │   EDIT MODE       │   GAME VIEW      │  RIGHT   │
│  PANEL     │   (metade esq.)   │   (metade dir.)  │  INSP.   │
```

---

## API Rápida

```python
from editor.layout import Layout

lay = Layout(screen_w=1400, screen_h=800)

# Redimensionamento
lay.update(new_w, new_h)

# Rects principais
lay.top_bar_rect        # pygame.Rect(0, 0, w, 30)
lay.status_bar_rect     # pygame.Rect(0, h-22, w, 22)
lay.left_panel_rect     # pygame.Rect(0, 30, 232, h-30)
lay.right_panel_rect    # pygame.Rect(right_x, 30, 230, h-30)
lay.viewport_rect       # Rect entre os dois painéis
lay.viewport_edit_rect  # Metade esquerda (play mode)
lay.viewport_game_rect  # Metade direita  (play mode)

# Parâmetros da câmera
vx, vy, vw, vh = lay.viewport_camera_params(play_mode=False)

# Inspector — posição de botões
lay.insp_btn_left()          # X do '<'
lay.insp_btn_right(btn_w=28) # X do '>'
lay.insp_field_rect(y=190)   # Rect do campo entre '<' e '>'
lay.insp_color_btn_x(i)      # X do i-ésimo botão de cor
```

---

## Constantes Importantes

| Constante | Valor | Descrição |
|---|---|---|
| `TOP_BAR_H` | 30 | Altura da barra de menus |
| `STATUS_BAR_H` | 22 | Altura da status bar |
| `LEFT_PANEL_W` | 232 | Largura do painel esquerdo |
| `RIGHT_PANEL_W` | 230 | Largura do inspector |
| `TREE_Y` | 232 | Y fixo do topo do Outliner |
| `TREE_ROW_H` | 26 | Altura de cada linha do Outliner |
| `INSPECTOR_PAD` | 15 | Margem interna do inspector |
| `INSPECTOR_W` | 200 | Largura útil do inspector |

---

## Migrando `scene.py`

Substitua os atuais _magic numbers_ em `scene.py` pelas chamadas ao `Layout`:

```python
# Antes (magic numbers)
right_x = width - 230
rx = right_x + 15
vp_w = right_x - 232

# Depois (Layout)
from editor.layout import Layout
lay = Layout()            # instância única no __init__
lay.update(width, height) # chamado no update()

right_x = lay.right_x
rx       = lay.inspector_x()
vp_w     = lay.viewport_w
```

---

## `PanelBase` — Widget Base

Todo painel pode herdar de `PanelBase` para ganhar:

- `self.layout` — referência ao `Layout` atualizado
- `on_resize(layout)` — chamado automaticamente pelo editor
- `_clip(screen)` — context manager que restringe o desenho ao rect do painel
- Interface `handle_event` / `update` / `draw`

```python
from editor.widgets import PanelBase

class OutlinerPanel(PanelBase):
    @property
    def rect(self):
        return self.layout.left_panel_rect

    def draw(self, screen):
        with self._clip(screen):
            # só desenha dentro do painel esquerdo
            ...
```
