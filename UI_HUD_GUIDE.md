# 🎮 GUIA COMPLETO: SISTEMA DE UI/HUD MELHORADO

## 🚀 Antes vs. Depois

### ❌ PROBLEMA ANTERIOR
```
❌ Criar UI era complicado (UICanvas, Anchor, Pivot, etc)
❌ Não havia forma clara de mostrar/chamar UI
❌ Widgets pré-feitos não existiam
❌ Posicionamento era confuso
❌ Sem documentação ou exemplos
```

### ✅ SOLUÇÃO NOVA
```
✅ Sistema HUDSystem simples (3 linhas para um HUD básico)
✅ Widgets prontos (HP bar, Score, Texto, Botões, Painéis)
✅ Posicionamento trivial (anchor/pivot automático)
✅ Documentação + exemplos
✅ Pronto para copiar e usar
```

---

## 📚 Estrutura do Sistema

```
UIManager (singleton)
    ├─ UICanvas (container de widgets)
    │   ├─ Panel (painel com borda)
    │   ├─ Label (texto)
    │   ├─ Button (botão interativo)
    │   ├─ ProgressBar (barra de progresso)
    │   └─ UIImage (imagem)
    │
    └─ HUDSystem (WRAPPER NOVO — torna tudo fácil!)
        ├─ add_health_bar() ✨
        ├─ add_score_display() ✨
        ├─ add_text_label() ✨
        ├─ add_button() ✨
        ├─ add_panel() ✨
        └─ set_health(), add_score(), set_text()... (UPDATE)
```

---

## ⚡ Início Rápido (3 Linhas)

### Criar HUD Básico

```python
from engine.ui import Anchor
from engine.ui.hud_system import HUDSystem

# 1. Criar HUD
hud = HUDSystem().create().show()

# 2. Adicionar widgets
hud.add_health_bar(current_health=100, max_health=100)
hud.add_score_display(initial_score=0)

# 3. Atualizar no jogo
hud.set_health(50)      # HP → 50
hud.add_score(10)       # Score +10
```

**É isto! Pronto!** ✅

---

## 🎨 Widgets Disponíveis

### 1. Health Bar (Barra de Saúde)

```python
hud.add_health_bar(
    widget_id="player_hp",
    x=10, y=10,
    width=200, height=20,
    max_health=100,
    current_health=100,
    label="HP",
    show_text=True,  # Mostra "100/100"
)

# Atualizar:
hud.set_health("player_hp", 50)
hud.set_max_health("player_hp", 150)
```

### 2. Score Display (Placar)

```python
hud.add_score_display(
    widget_id="score",
    x=-10, y=10,  # Negativos = relativo ao canto oposto
    initial_score=0,
    anchor=Anchor.TOP_RIGHT,  # Canto superior direito
    color=(255, 220, 60),
    font_size=24,
)

# Atualizar:
hud.set_score("score", 500)     # Definir valor
hud.add_score("score", 10)      # Adicionar
```

### 3. Text Label (Rótulo)

```python
hud.add_text_label(
    widget_id="wave_text",
    text="Wave 1",
    x=0, y=50,
    font_size=32,
    color=(200, 200, 255),
    anchor=Anchor.TOP_CENTER,
    bold=True,
    shadow=True,
)

# Atualizar:
hud.set_text("wave_text", "Wave 2")
```

### 4. Panel (Painel/Container)

```python
panel = hud.add_panel(
    widget_id="inventory_panel",
    x=10, y=100,
    width=250, height=300,
    color=(20, 20, 40, 200),      # RGBA
    border_color=(100, 100, 200),
    border_radius=12,
)

# Adicionar widgets dentro do painel depois:
label = hud.add_text_label(
    "inventory_title",
    text="Inventário",
    x=0, y=10,
    anchor=Anchor.TOP_CENTER,
)
```

### 5. Button (Botão)

```python
def on_play_clicked():
    print("Jogador clicou em Jogar!")
    game.start()

hud.add_button(
    widget_id="play_btn",
    text="Jogar",
    on_click=on_play_clicked,
    x=0, y=200,
    width=200, height=50,
    anchor=Anchor.MIDDLE_CENTER,
    font_size=20,
)
```

---

## 📍 Posicionamento (Simples!)

### Anchors (9 pontos na tela)

```
TOP_LEFT        TOP_CENTER        TOP_RIGHT
   ●─────────────────●─────────────────●
   │                                   │
   │                                   │
MIDDLE_LEFT      MIDDLE_CENTER     MIDDLE_RIGHT
   ●                ●                   ●
   │                                   │
   │                                   │
   ●─────────────────●─────────────────●
BOTTOM_LEFT    BOTTOM_CENTER     BOTTOM_RIGHT
```

### Exemplos

```python
# Canto superior esquerdo
x=10, y=10, anchor=Anchor.TOP_LEFT

# Centro da tela
x=0, y=0, anchor=Anchor.MIDDLE_CENTER

# Canto inferior direito
x=-10, y=-10, anchor=Anchor.BOTTOM_RIGHT

# Negativo = relativo ao canto oposto
x=-100, y=50, anchor=Anchor.TOP_RIGHT  # 100px da direita
```

---

## 🎮 Exemplo Completo: Jogo RPG

```python
from engine.core import Engine, Scene
from engine.ui import Anchor, Pivot
from engine.ui.hud_system import HUDSystem

class RPGScene(Scene):
    def start(self):
        # Estado do jogo
        self.player_hp = 100
        self.max_hp = 100
        self.score = 0

        # Criar HUD
        self.hud = HUDSystem("GameHUD", z_order=0)
        self.hud.create()

        # ── Painel superior esquerdo (Status) ──
        self.hud.add_health_bar(
            widget_id="hp_bar",
            x=10, y=10,
            width=200,
            max_health=self.max_hp,
            current_health=self.player_hp,
            label="HP"
        )

        # ── Score canto superior direito ──
        self.hud.add_score_display(
            widget_id="score",
            x=-10, y=10,
            initial_score=self.score,
            anchor=Anchor.TOP_RIGHT,
        )

        # ── Dica inferior ──
        self.hud.add_text_label(
            widget_id="hint",
            text="ESC: Pause | R: Reiniciar",
            x=0, y=-20,
            font_size=14,
            anchor=Anchor.BOTTOM_CENTER,
            color=(160, 160, 180),
        )

        # ── Painel de informações centrais ──
        info_panel = self.hud.add_panel(
            widget_id="info_panel",
            x=0, y=0,
            width=300, height=100,
            anchor=Anchor.MIDDLE_CENTER,
            color=(10, 10, 30, 200),
        )

        # Mostrar o HUD
        self.hud.show()

    def update(self, dt):
        # Simular dano
        if self.input.is_key_pressed("h"):
            self.player_hp = max(0, self.player_hp - 10)
            self.hud.set_health("hp_bar", self.player_hp)

        # Simular score
        if self.input.is_key_pressed("s"):
            self.score += 100
            self.hud.add_score("score", 100)

        # Verificar game over
        if self.player_hp <= 0:
            self.hud.set_text("hint", "GAME OVER - R para reiniciar")
```

---

## 🔄 Ciclo de Vida Completo

```python
# 1. CRIAR (na scene.start())
hud = HUDSystem("MyHUD").create()

# 2. ADICIONAR WIDGETS
hud.add_health_bar(...)
hud.add_score_display(...)
hud.add_button(...)

# 3. MOSTRAR (na tela)
hud.show()

# 4. ATUALIZAR (no scene.update())
hud.set_health("hp_bar", new_value)
hud.add_score("score", 10)

# 5. ESCONDER (opcional)
hud.hide()

# 6. REMOVER COMPLETAMENTE (ao sair da cena)
hud.remove()
```

---

## 🎯 Padrões Comuns

### Padrão 1: Status HUD Simples

```python
hud = HUDSystem().create().show()

# Canto superior esquerdo
hud.add_health_bar(
    x=10, y=10,
    width=200,
    max_health=100,
)

# Canto superior direito
hud.add_score_display(
    x=-10, y=10,
    anchor=Anchor.TOP_RIGHT,
)
```

### Padrão 2: Menu Pause

```python
pause_hud = HUDSystem("PauseMenu", z_order=100)
pause_hud.create()

# Overlay escuro
pause_hud.add_panel(
    widget_id="overlay",
    x=0, y=0,
    width=800, height=600,
    color=(0, 0, 0, 150),
    border_color=None,
)

# Janela central
pause_hud.add_panel(
    widget_id="menu_panel",
    x=0, y=0,
    width=400, height=300,
    anchor=Anchor.MIDDLE_CENTER,
)

# Botões
pause_hud.add_button(
    "continue_btn",
    "Continuar",
    on_click=lambda: game.resume(),
    x=0, y=50,
    anchor=Anchor.TOP_CENTER,
)
pause_hud.add_button(
    "quit_btn",
    "Sair",
    on_click=lambda: game.quit(),
    x=0, y=120,
    anchor=Anchor.TOP_CENTER,
)

# Mostrar quando pausa
pause_hud.show()
```

### Padrão 3: HUD Dinâmico

```python
hud = HUDSystem().create().show()

# Adicionar dinamicamente
def add_floating_damage(damage):
    hud.add_text_label(
        f"damage_{time.time()}",
        text=f"-{damage}",
        x=400, y=300,
        color=(255, 100, 100),
        font_size=20,
    )
```

---

## 🐛 Debug & Troubleshooting

### "Meu HUD não aparece!"

```python
# ✅ Correto:
hud = HUDSystem().create().show()  # create() E show()

# ❌ Errado:
hud = HUDSystem()  # Falta create().show()

# ✅ Verificar:
print(hud.canvas)          # Deve ter um canvas
print(hud._is_visible)     # Deve ser True
print(len(hud._widgets))   # Deve ter widgets
```

### "Widget está fora de lugar!"

```python
# Verifique o Anchor:
x=10, y=10, anchor=Anchor.TOP_LEFT      # Canto superior esquerdo
x=-10, y=10, anchor=Anchor.TOP_RIGHT    # Canto superior direito
```

### "Texto pequeno demais / grande demais!"

```python
# Ajuste font_size:
hud.add_text_label(
    "...",
    font_size=24,  # Aumentar este valor
)
```

---

## 🎬 Integração com Scene

```python
from engine.core import Scene
from engine.ui.hud_system import HUDSystem

class GameScene(Scene):
    def start(self):
        # Criar e mostrar HUD
        self.hud = HUDSystem("GameHUD").create().show()
        self.hud.add_health_bar(x=10, y=10)
        self.hud.add_score_display(x=-10, y=10, anchor=Anchor.TOP_RIGHT)

    def update(self, dt):
        # Atualizar HUD com dados do jogo
        self.hud.set_health("health_bar", self.player.health)
        self.hud.set_score("score", self.game_score)

    def on_scene_end(self):
        # Limpar HUD
        self.hud.remove()
```

---

## 🔧 API Referência Rápida

| Método | Descrição |
|--------|-----------|
| `create()` | Cria o canvas interno |
| `show()` | Mostra na tela |
| `hide()` | Esconde |
| `toggle()` | Mostra/esconde |
| `clear()` | Remove todos widgets |
| `remove()` | Remove completamente |
| `add_health_bar()` | Adiciona barra de saúde |
| `add_score_display()` | Adiciona placar |
| `add_text_label()` | Adiciona texto |
| `add_button()` | Adiciona botão |
| `add_panel()` | Adiciona painel |
| `set_health()` | Atualiza saúde |
| `set_score()` | Define score |
| `add_score()` | Adiciona ao score |
| `set_text()` | Atualiza texto |
| `get_text()` | Lê texto |
| `get_widget()` | Acessa widget direto |

---

## ✅ Checklist

- [ ] Ler este guia
- [ ] Ver exemplo em `examples_ui_hud.py`
- [ ] Rodar testes
- [ ] Criar seu primeiro HUD
- [ ] Integrar com sua scene
- [ ] Customizar cores/tamanhos
- [ ] Celebrar! 🎉

---

**Tudo pronto para criar UIs lindas e funcionais!** 🚀

Dúvidas? Veja os exemplos em `examples_ui_hud.py`
