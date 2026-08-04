# ⚡ EDITOR VISUAL — INÍCIO RÁPIDO (5 MINUTOS)

## 🎯 As 6 Abas do Editor

```
┌─────────────────────────────────────────────────────┐
│ ⚡ Visual Scripting Editor 2.0                      │
├──────┬────────────┬──────────┬─────────┬───────────┬───────┐
│Logic │Behavior   │Dialogue  │Material │Animator   │UI &   │
│Graph │Tree       │          │         │Graph      │HUD    │
└──────┴────────────┴──────────┴─────────┴───────────┴───────┘
```

Nos vamos focar em **2 abas principais**:
1. **Behavior Tree** - IA visual
2. **UI & HUD** - Interface visual

---

## 🧠 ABA 1: BEHAVIOR TREE (5 min)

### Passo 1: Abrir Aba
```
Clique em "Behavior Tree" (segunda aba do editor)
```

### Passo 2: Novo Arquivo
```
File → New
→ Nome: "MyEnemy"
→ Salva em Assets/Behaviors/MyEnemy.zbehavior
```

### Passo 3: Adicionar Nó Raiz
```
Painel ESQUERDO:
  ├─ Composite
  │   └─ Selector ← DRAG para o canvas
  
Coloque no MEIO do canvas
Este é o nó raiz (start_node)
```

### Passo 4: Adicionar Filhos
```
ESQUERDA:
  ├─ Condition
  │   └─ "Target In Range" ← DRAG

→ Conecte na saída do Selector (clique+arraste o pino)

ESQUERDA:
  ├─ Action
  │   └─ "Chase" ← DRAG

→ Conecte também no Selector
```

### Passo 5: Editar Propriedades
```
Clique no nó "Target In Range"
DIREITA (Inspector):
  - distance: 300.0
  - target: "Player"

Clique no nó "Chase"
DIREITA (Inspector):
  - speed: 120.0
  - stop_distance: 48.0
```

### Passo 6: Salvar
```
Ctrl+S
Pronto! Seu arquivo está em Assets/Behaviors/MyEnemy.zbehavior
```

### Resultado Final
```
        [Selector]
         ↙       ↘
[Target In Range] [Chase]
```

**Isso significa:** "Se alvo está perto, persiga. Senão, nada."

---

## 🎨 ABA 2: UI & HUD (5 min)

### Passo 1: Abrir Aba
```
Clique em "UI & HUD" (última aba do editor)
```

### Passo 2: Novo Arquivo
```
File → New
→ Nome: "GameHUD"
→ Salva em Assets/UI/GameHUD.zui
```

### Passo 3: Adicionar Painel HP
```
ESQUERDA (Widgets):
  └─ Panel ← DRAG para o canvas

Coloque no canto superior esquerdo (10, 10)

DIREITA (Inspector):
  - Name: "hp_panel"
  - Width: 200
  - Height: 60
```

### Passo 4: Adicionar Label (HP)
```
ESQUERDA:
  └─ Label ← DRAG para o hp_panel

DIREITA (Inspector):
  - Name: "hp_label"
  - Text: "HP: 100/100"
  - Font Size: 16
  - Color: (255, 0, 0) vermelho
```

### Passo 5: Adicionar Score
```
ESQUERDA:
  └─ Label ← DRAG para o canvas

DIREITA (Inspector):
  - Name: "score_label"
  - Text: "Score: 0"
  - Font Size: 24
  - Color: (255, 255, 0) amarelo
  - X: -10, Y: 10 (canto direito)
```

### Passo 6: Salvar
```
Ctrl+S
Pronto! Seu arquivo está em Assets/UI/GameHUD.zui
```

### Resultado Visual
```
┌─────────────────────────────────────────┐
│ HP: 100/100              Score: 0       │
│                                         │
└─────────────────────────────────────────┘
```

---

## 💻 Usar no Código

### Behavior Tree
```python
from engine.ai.behavior_tree_runtime import BehaviorTreeRuntime
import json

# Carregar árvore criada no editor
with open("Assets/Behaviors/MyEnemy.zbehavior") as f:
    tree_data = json.load(f)

# Executar
runtime = BehaviorTreeRuntime(tree_data, game_object=enemy)
runtime.update(dt=0.016)

# Passar dados
runtime.set_parameter("player_distance", 150)
```

### UI & HUD
```python
from engine.ui.hud_system import HUDSystem
import json

# Carregar interface criada no editor
with open("Assets/UI/GameHUD.zui") as f:
    ui_data = json.load(f)

# OPÇÃO 1: Usar HUDSystem
hud = HUDSystem().create().show()
hud.add_health_bar(current_health=100)
hud.add_score_display(initial_score=0)

# OPÇÃO 2: Carregar arquivo do editor
# (use como base/referência visual)
```

---

## 🎯 Atalhos Importantes

| Tecla | Função |
|-------|--------|
| `Ctrl+S` | Salvar |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Delete` | Deletar selecionado |
| `+` / `-` | Zoom in/out |

---

## ✅ Checklist

- [ ] Abrir editor visual
- [ ] Criar Behavior Tree (MyEnemy.zbehavior)
  - [ ] Adicionar Selector
  - [ ] Adicionar Target In Range
  - [ ] Adicionar Chase
  - [ ] Conectar nós
  - [ ] Editar propriedades
- [ ] Criar UI/HUD (GameHUD.zui)
  - [ ] Adicionar Panel (HP)
  - [ ] Adicionar Label (HP)
  - [ ] Adicionar Label (Score)
  - [ ] Posicionar widgets
- [ ] Salvar ambos (Ctrl+S)
- [ ] Usar no código

---

## 🆘 Quick Fix

### "Nó não conecta"
```
✅ Clique na SAÍDA (pino branco) do nó 1
✅ Arraste até ENTRADA (pino branco) do nó 2
✅ Solte
```

### "Widget não aparece"
```
✅ Verifique se está dentro do Canvas
✅ Marque visible = true no Inspector
✅ Ajuste X/Y/Width/Height
```

### "Arquivo não salva"
```
✅ Use Ctrl+S (não só fechar)
✅ Procure em Assets/Behaviors/ ou Assets/UI/
✅ Arquivo deve estar em disco
```

---

## 📚 Referência Rápida

### Behavior Tree Nodes
```
Selector    - Escolha 1 de N (tipo "ou")
Sequence    - Fazer 1, 2, 3 em ordem
Repeat      - Fazer N vezes
Cooldown    - Aguardar intervalo
Chase       - Perseguir alvo
Patrol      - Patrulhar A↔B
Attack      - Atacar
```

### UI Widgets
```
Panel       - Container com bordas
Label       - Texto
Button      - Botão clicável
Image       - Imagem/sprite
Input       - Campo de texto
Container   - Agrupa elementos
```

---

**Pronto! Você já sabe usar o editor visual!** 🎉

Veja guia completo:
- `EDITOR_VISUAL_GUIDE.md` (detalhado)
- `BEHAVIOR_TREE_GUIDE.md` (conceitos)
- `UI_HUD_GUIDE.md` (conceitos)
