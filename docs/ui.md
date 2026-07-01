# 🖥️ Sistema de UI — Zennity Engine

## Arquitetura

```
UIManager  (singleton)
  └── UICanvas  (raiz, z_order)
        ├── Panel
        │     ├── Label
        │     ├── ProgressBar
        │     └── Button
        └── Label  (score, etc.)
```

| Classe | Arquivo | Responsabilidade |
|---|---|---|
| `UIElement` | `base.py` | Classe base: Anchor, Pivot, hierarquia, get_rect |
| `Label` | `label.py` | Texto estático/dinâmico com sombra |
| `Button` | `button.py` | Botão com hover/press animado e callback |
| `UIImage` | `image.py` | Exibe pygame.Surface como widget |
| `ProgressBar` | `progress_bar.py` | Barra HP/MP/XP com animação suave |
| `Panel` | `panel.py` | Container semi-transparente com borda |
| `UICanvas` | `canvas.py` | Raiz da árvore de UI |
| `UIManager` | `ui_manager.py` | Gerencia múltiplos canvases |

---

## Uso Rápido

```python
from engine.ui import UICanvas, UIManager, Panel, Label, Button, ProgressBar, Anchor, Pivot

# Na scene.start():
ui = UIManager.instance()
hud = UICanvas(name="HUD", z_order=0)

# Painel com filhos
panel = Panel(x=10, y=10, width=220, height=90)
hud.add_child(panel)

panel.add_child(Label("HP", x=10, y=8, color=(240,80,80), bold=True))
hp_bar = ProgressBar(x=35, y=10, width=170, height=16,
                     value=100, max_value=100,
                     color_fill=(200,60,60), smooth=True)
panel.add_child(hp_bar)

btn = Button("Start", x=0, y=0, on_click=lambda: print("clicked!"),
             anchor=Anchor.BOTTOM_CENTER, pivot=Pivot.BOTTOM_CENTER)
hud.add_child(btn)

ui.add_canvas(hud)

# No loop da scene:
def handle_event(self, event):
    self.ui.handle_event(event, screen)

def update(self, dt):
    self.ui.update(dt)
    hp_bar.set_value(player.hp)

def draw(self, screen):
    # ... desenha o mundo ...
    self.ui.draw(screen)  # UI por último (screen space)
```

---

## Anchor & Pivot

`Anchor` define onde no container o elemento se ancora.  
`Pivot` define qual ponto do próprio widget é o "x=0, y=0".

```python
# Score no canto superior direito
Label("Score: 0", x=-10, y=10,
      anchor=Anchor.TOP_RIGHT, pivot=Pivot.TOP_RIGHT)

# Botão centralizado na tela
Button("Play", x=0, y=0,
       anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER)

# HP bar no canto inferior esquerdo
ProgressBar(x=10, y=-30,
            anchor=Anchor.BOTTOM_LEFT, pivot=Pivot.BOTTOM_LEFT)
```

---

## Múltiplos Canvases (HUD + Pause + GameOver)

```python
hud_canvas    = UICanvas(name="HUD",      z_order=0)
pause_canvas  = UICanvas(name="Pause",    z_order=10, visible=False)
gameover_canvas = UICanvas(name="GameOver", z_order=20, visible=False)

ui.add_canvas(hud_canvas)
ui.add_canvas(pause_canvas)
ui.add_canvas(gameover_canvas)

# Para mostrar o menu de pausa:
pause_canvas.visible = True
```

---

## Rodar a Demo

```bash
python -m demos.demo_ui
```

Contrôles: `H` -HP · `M` -MP · `X` curar · `Esc` pausar · `R` resetar
