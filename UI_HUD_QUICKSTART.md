# ⚡ UI/HUD — INÍCIO RÁPIDO (3 MINUTOS)

## 🎬 Demo: HUD Funcional em 3 Linhas

```python
from engine.ui.hud_system import HUDSystem

# 1. Criar
hud = HUDSystem().create().show()

# 2. Adicionar widgets
hud.add_health_bar(x=10, y=10, max_health=100, current_health=50)
hud.add_score_display(x=-10, y=10, anchor=Anchor.TOP_RIGHT, initial_score=0)

# 3. Atualizar
hud.set_health("health_bar", 30)  # HP → 30
hud.add_score("score", 100)       # Score +100
```

**Pronto! Seu HUD está na tela!** ✅

---

## 📚 Widgets Básicos

### Health Bar
```python
hud.add_health_bar(
    x=10, y=10,
    width=200,
    max_health=100,
    current_health=100,
    label="HP",
    show_text=True
)

# Atualizar:
hud.set_health("health_bar", 50)
```

### Score Display
```python
hud.add_score_display(
    x=-10, y=10,
    initial_score=0,
    anchor=Anchor.TOP_RIGHT,
    font_size=24
)

# Atualizar:
hud.add_score("score", 10)  # +10
hud.set_score("score", 500) # = 500
```

### Text Label
```python
hud.add_text_label(
    widget_id="level",
    text="LEVEL 1",
    x=0, y=0,
    anchor=Anchor.MIDDLE_CENTER,
    font_size=32,
    color=(200, 200, 255)
)

# Atualizar:
hud.set_text("level", "LEVEL 2")
```

### Button
```python
hud.add_button(
    widget_id="play_btn",
    text="Play",
    on_click=lambda: game.start(),
    x=0, y=0,
    anchor=Anchor.MIDDLE_CENTER,
    width=200, height=50
)
```

### Panel (Container)
```python
panel = hud.add_panel(
    widget_id="menu",
    x=0, y=0,
    width=400, height=300,
    anchor=Anchor.MIDDLE_CENTER,
    color=(20, 20, 40, 200)
)
```

---

## 📍 Positioning (9 Pontos)

```
LEFT          CENTER          RIGHT
╔─────────────────────────────╗
║  TOP_LEFT    TOP_CENTER    TOP_RIGHT
║    ●           ●             ●
║
║ MIDDLE_LEFT MIDDLE_CENTER MIDDLE_RIGHT
║    ●           ●             ●
║
║ BOTTOM_LEFT BOTTOM_CENTER BOTTOM_RIGHT
║    ●           ●             ●
╚─────────────────────────────╝
```

**Use:**
```python
anchor=Anchor.TOP_LEFT       # Canto superior esquerdo
anchor=Anchor.MIDDLE_CENTER  # Centro
anchor=Anchor.BOTTOM_RIGHT   # Canto inferior direito
x=-10, y=10                  # Negativos = da borda oposta
```

---

## 🎮 Exemplo Completo: Game with HUD

```python
from engine.core import Scene
from engine.ui import Anchor
from engine.ui.hud_system import HUDSystem

class GameScene(Scene):
    def start(self):
        # Criar HUD
        self.hud = HUDSystem("GameHUD").create().show()

        # Status
        self.hud.add_health_bar(x=10, y=10, max_health=100)
        self.hud.add_score_display(x=-10, y=10, anchor=Anchor.TOP_RIGHT)

        # Hint
        self.hud.add_text_label(
            "hint",
            text="ESC: Pause",
            x=0, y=-20,
            anchor=Anchor.BOTTOM_CENTER,
            color=(160, 160, 180)
        )

    def update(self, dt):
        # Atualizar HUD
        self.hud.set_health("health_bar", self.player.health)
        self.hud.add_score("score", self.points_this_frame)
```

---

## 🔄 Lifecycle

```python
# 1. CRIAR
hud = HUDSystem().create()

# 2. ADICIONAR widgets
hud.add_health_bar(...)
hud.add_score_display(...)

# 3. MOSTRAR na tela
hud.show()

# 4. ATUALIZAR (no game loop)
hud.set_health("health_bar", value)

# 5. ESCONDER (opcional)
hud.hide()

# 6. REMOVER (ao sair da cena)
hud.remove()
```

---

## ✅ Checklist

- [ ] Importar HUDSystem
- [ ] Criar HUD: `HUDSystem().create().show()`
- [ ] Adicionar widgets
- [ ] Atualizar valores no update()
- [ ] Testar

---

## 🆘 Quick Troubleshooting

| Problema | Solução |
|----------|---------|
| "UI não aparece!" | Chamar `.show()` após `.create()` |
| "Widget fora de lugar" | Ajustar `x, y` e `anchor` |
| "Texto muito pequeno" | Aumentar `font_size` |
| "Cor errada" | Usar RGB ou RGBA tuple |
| "Não conseguir atualizar" | Usar ID correto no `set_*` |

---

## 📚 Referência Rápida

```python
# Criar
HUDSystem(canvas_name="HUD", z_order=0)
.create()
.show()

# Widgets
.add_health_bar()
.add_score_display()
.add_text_label()
.add_button()
.add_panel()

# Atualizar
.set_health(id, value)
.set_score(id, value)
.add_score(id, value)
.set_text(id, text)
.get_text(id)
.get_widget(id)

# Lifecycle
.hide() / .toggle() / .clear() / .remove()
```

---

## 🎯 Padrões Prontos

### Padrão 1: Game HUD
```python
hud = HUDSystem().create().show()
hud.add_health_bar(x=10, y=10)
hud.add_score_display(x=-10, y=10, anchor=Anchor.TOP_RIGHT)
```

### Padrão 2: Pause Menu
```python
pause_hud = HUDSystem("Pause", z_order=100).create()
pause_hud.add_panel(...overlay...)
pause_hud.add_button("continue", "Continuar", on_click=resume)
pause_hud.add_button("quit", "Sair", on_click=quit)
pause_hud.show()  # Mostrar ao pausar
```

### Padrão 3: Inventory Panel
```python
inv_panel = hud.add_panel(...)
hud.add_text_label("inv_title", "Inventory", x=0, y=10)
# Adicionar mais widgets ao painel
```

---

## 🚀 Próximos Passos

1. **Ver exemplos:** `examples_ui_hud.py`
2. **Ler guia completo:** `UI_HUD_GUIDE.md`
3. **Criar seu HUD:** Copie padrão acima
4. **Customize:** Cores, tamanhos, posições

---

**Tudo pronto para criar UI linda!** 🎨

Dúvidas? Ver `UI_HUD_GUIDE.md` (guia completo)
