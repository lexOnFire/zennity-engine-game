# 🎨 GUIA DO EDITOR VISUAL — ABAS (Behavior Tree + UI/HUD)

## 📍 Onde Encontrar

Abra o **Zennity Engine Editor** e procure pelas abas na parte central da tela:

```
┌─────────────────────────────────────────────────────┐
│ ⚡ Visual Scripting Editor 2.0                      │
├──────┬────────────┬──────────┬─────────┬───────────┤
│Logic │Behavior   │Dialogue  │Material │Animator   │UI & HUD
│Graph │Tree       │          │         │Graph      │
│      │           │          │         │           │
└──────┴────────────┴──────────┴─────────┴───────────┘
```

**Total: 6 abas diferentes**

---

## 🎯 ABA 1: BEHAVIOR TREE

### O Que É?
Editor visual para criar **Árvores de Comportamento** em drag-and-drop.

### Como Abrir

```
1. Clique em "Behavior Tree" (segunda aba)
2. Crie novo arquivo (.zbehavior)
3. Arraste nós do painel esquerdo
```

### Layout da Aba

```
┌──────────────────────────────────────────────┐
│ 🧠 Behavior Tree Editor                      │
├──────────┬────────────────────┬──────────────┤
│          │                    │              │
│ Node     │  Canvas com Nós   │  Inspector   │
│ Library  │  (drag-and-drop)  │  Propriedades│
│          │                   │              │
│ • Root   │   [Selector]      │ Nome:        │
│ • Comp   │      ↙  ↘         │ Tipo:        │
│ • Cond   │  [Chase][Patrol]  │ ID: bt.sel   │
│ • Action │                   │              │
│          │                   │              │
└──────────┴────────────────────┴──────────────┘
```

### Passo a Passo: Criar Primeira Árvore

#### 1. Criar Novo Arquivo
```
File → New Behavior Tree
→ Escolha nome: "EnemyBT"
→ Salva em Assets/Behaviors/
```

#### 2. Adicionar Raiz
```
1. Drag "Selector" da biblioteca esquerda
2. Coloque no canvas (meio)
3. Este é o nó raiz (start_node)
```

#### 3. Adicionar Filhos
```
1. Drag "Condition" → "Target In Range" 
2. Conecte na saída "option_1" do Selector
3. Arraste para ajustar posição

4. Drag "Action" → "Chase"
5. Conecte na saída do Selector
```

#### 4. Conectar Nós
```
Clique em um pino de SAÍDA (•)
Arraste até um pino de ENTRADA (•)
Solte para conectar
```

#### 5. Editar Propriedades
```
1. Selecione um nó (clique nele)
2. Vá para painel "Inspector" (direita)
3. Mude valores (distance, speed, etc)
```

### Nós Disponíveis (No painel esquerdo)

#### Composite (Controlam fluxo)
```
Selector (•)       Escolher 1 de N
  ├─ Opção 1
  └─ Opção 2

Sequence (●)       Fazer 1, 2, 3 em ordem
  ├─ Passo 1
  └─ Passo 2
```

#### Decorator (Modificam)
```
Repeat            Fazer N vezes
Cooldown          Aguardar intervalo
Limiter           Máximo N vezes
Inverter          Sucesso ↔ Falha
```

#### Condition (Decidir)
```
Target In Range   Alvo perto?
Health Check      Saúde OK?
Parameter Check   Parâmetro == valor?
Random Chance     Sorte?
```

#### Action (Fazer)
```
Patrol            Patrulhar A↔B
Chase             Perseguir alvo
Attack            Atacar
Idle              Esperar
Play Animation    Tocar anim
```

### Dicas & Atalhos

| Atalho | Função |
|--------|--------|
| `Clique` | Selecionar nó |
| `Drag` | Mover nó |
| `Del` | Deletar nó |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `+/-` | Zoom in/out |
| `Space+Drag` | Pan (mover canvas) |

### Exemplo Completo: Inimigo Patrulha+Ataca

```
Crie esta estrutura:

        ┌─ [Selector]
        │     ├─ [Check Target Range]
        │     │     └─ [Chase]
        │     └─ [Patrol]
```

**Passo a passo:**

1. Novo arquivo "PatrolChase.zbehavior"
2. Add "Selector" → center → é a raiz
3. Add "Target In Range" → connect ao option_1
4. Add "Chase" → connect saída do condition
5. Add "Patrol" → connect ao option_2
6. Salve (Ctrl+S)
7. Use no jogo via código

---

## 🎨 ABA 2: UI & HUD

### O Que É?
Editor **WYSIWYG** (What You See Is What You Get) para criar interfaces visuais.

### Como Abrir

```
1. Clique em "UI & HUD" (última aba)
2. Crie novo arquivo (.zui)
3. Arraste widgets do painel esquerdo
```

### Layout da Aba

```
┌────────────────────────────────────────────────────┐
│ 🎨 UI Builder                                      │
├─────────────┬──────────────────────┬──────────────┤
│             │                      │              │
│ Widgets     │ Preview (WYSIWYG)   │ Hierarchy &  │
│ Library     │ Visualize ao vivo   │ Inspector    │
│             │                      │              │
│ ▢ Panel     │   ┌──────────────┐  │ Canvas       │
│ ▭ Label     │   │ □ HP: 100/100│  │  └─ Panel    │
│ ▣ Button    │   │ Score: 5000  │  │      └─Label │
│ □ Image     │   │ [Continue]   │  │      └─Label │
│ ▢ Container │   └──────────────┘  │  └─ Button   │
│             │                      │              │
└─────────────┴──────────────────────┴──────────────┘
```

### Widgets Disponíveis

```
Panel      - Painel com bordas (container)
Label      - Texto simples
Button     - Botão interativo
Image      - Imagem/sprite
Input      - Campo de texto
Container  - Agrupa elementos
ScrollView - Área rolável
```

### Passo a Passo: Criar HUD Simples

#### 1. Novo Arquivo
```
File → New UI
→ Escolha nome: "GameHUD"
→ Salva em Assets/UI/
```

#### 2. Adicionar Painel (HP)
```
1. Drag "Panel" → Canvas
2. Posicione no canto superior esquerdo
3. No Inspector (direita):
   - Name: "hp_panel"
   - Width: 200
   - Height: 60
   - Color: escuro (RGBA)
```

#### 3. Adicionar Label (HP)
```
1. Drag "Label" → hp_panel
2. No Inspector:
   - Text: "HP: 100/100"
   - Font Size: 16
   - Color: vermelho (255, 0, 0)
```

#### 4. Adicionar Score
```
1. Drag "Label" → Canvas
2. Posicione no canto superior direito
3. Inspector:
   - Name: "score_label"
   - Text: "Score: 0"
   - Font Size: 24
   - Color: amarelo (255, 255, 0)
```

#### 5. Adicionar Botão
```
1. Drag "Button" → Canvas
2. Posicione no centro
3. Inspector:
   - Text: "Play"
   - Width: 200
   - Height: 50
```

#### 6. Salvar
```
Ctrl+S
Arquivo pronto em Assets/UI/GameHUD.zui
```

### Editando Widgets

#### Mover
```
Clique e arraste o widget no preview
OU
Selecione → ajuste X/Y no Inspector
```

#### Redimensionar
```
Selecione → ajuste Width/Height no Inspector
OU
Arraste as bordas no preview (se suportado)
```

#### Editar Propriedades
```
Selecione o widget
Painel direito muda:
  - Name: identificador
  - X/Y: posição
  - Width/Height: tamanho
  - Text: conteúdo (Label/Button)
  - Color: cor de fundo
  - Visible: mostrado?
  - Layout: tipo de layout (Free/Stack)
```

### Estrutura Hierárquica (Esquerda Inferior)

```
Canvas (raiz)
  ├─ hp_panel (Panel)
  │   └─ hp_label (Label)
  ├─ score_label (Label)
  └─ play_button (Button)
```

- Clique para selecionar
- Arraste para reordenar
- Delete seleciona para remover

### Atalhos

| Atalho | Função |
|--------|--------|
| `Clique` | Selecionar widget |
| `Drag` | Mover na preview |
| `Del` | Deletar widget |
| `Ctrl+D` | Duplicar |
| `Ctrl+Z` | Undo |
| `Escape` | Deselecionar |

### Exemplo Completo: RPG HUD

```
Crie este layout:

┌─────────────────────────────────────────┐
│ HP: 100/100         Score: 5000         │
│                                         │
│                                         │
│          ESC: Pausar                    │
└─────────────────────────────────────────┘

Passo a passo:

1. Panel "hp_panel" (10, 10, 200, 60)
   └─ Label "HP: 100/100"

2. Label "score" (-10, 10, 200, 60)
   Anchor: TOP_RIGHT

3. Label "hint" (0, -10)
   Anchor: BOTTOM_CENTER
```

---

## 🔧 Dicas Gerais (Ambas Abas)

### Salvar
```
Ctrl+S              Salvar arquivo atual
File → Save As      Salvar com outro nome
```

### Validação
```
Clique em "Validate" (botão toolbar)
Mostra erros/avisos no seu arquivo
```

### Undo/Redo
```
Ctrl+Z              Desfazer última ação
Ctrl+Y              Refazer
```

### Debug
```
Clique "Play" para rodar o editor
Veja comportamento em tempo real
"Pause/Stop" para controlar
```

---

## 🎯 Fluxo Completo: Do Editor ao Jogo

### 1. Criar no Editor Visual
```
Behavior Tree Tab:
  → Create novo .zbehavior
  → Montar árvore visualmente
  → Salve

UI & HUD Tab:
  → Create novo .zui
  → Montar interface visualmente
  → Salve
```

### 2. Usar no Código
```python
# Behavior Tree
from engine.ai.behavior_tree_runtime import BehaviorTreeRuntime
tree = BehaviorTreeRuntime(load_json("Assets/Behaviors/MyTree.zbehavior"))
status = tree.update(dt)

# UI/HUD
from engine.ui.hud_system import HUDSystem
hud = HUDSystem().create().show()
# OU carregar arquivo visual salvo
```

### 3. Testar
```
Rode o jogo (F5 ou Play)
Veja Behavior Tree executando
Veja UI/HUD na tela
```

---

## 🆘 Troubleshooting

### "Meu Behavior Tree não conecta"
```
❌ Errado: conectar saída → entrada errada
✅ Correto: saída de um nó → entrada de outro
           Respeitar tipos (EXEC → EXEC)
```

### "Widget não aparece no preview"
```
❌ Errado: Widget fora da área visível
✅ Correto: Ajuste X/Y para estar dentro do Canvas
           Verifique se está visible=true
```

### "Arquivo não salva"
```
✅ Use Ctrl+S
✅ Verifique arquivo .zbehavior ou .zui foi criado
✅ Procure em Assets/Behaviors/ ou Assets/UI/
```

### "Não consigo usar no jogo"
```
✅ Carregue o arquivo:
   tree_data = load_json("Assets/Behaviors/MyTree.zbehavior")
✅ Crie runtime:
   runtime = BehaviorTreeRuntime(tree_data)
```

---

## 📚 Resumo Rápido

### Behavior Tree Editor
```
+ Adicionar nó: Drag da biblioteca
+ Conectar: Pino saída → Pino entrada
+ Editar: Inspector painel direito
+ Validar: Botão Validate
+ Salvar: Ctrl+S
- Usar no código: BehaviorTreeRuntime(load_json("..."))
```

### UI Builder
```
+ Adicionar widget: Drag da biblioteca
+ Posicionar: Drag no preview
+ Editar: Inspector painel direito
+ Validar: Botão Validate
+ Salvar: Ctrl+S
- Usar no código: carregar arquivo .zui ou criar via HUDSystem
```

### Atalhos Universais
```
Ctrl+S     Salvar
Ctrl+Z     Undo
Ctrl+Y     Redo
Del        Deletar selecionado
Escape     Deselecionar
+/-        Zoom
```

---

## 🚀 Próximos Passos

1. Abra o editor (Zennity Engine)
2. Vá para aba "Behavior Tree" ou "UI & HUD"
3. Crie novo arquivo
4. Arraste seus primeiros nós/widgets
5. Salve (Ctrl+S)
6. Integre no código
7. Rode e teste!

---

**Divirta-se criando comportamentos e interfaces visuais!** 🎨🧠

Dúvidas? Veja os guias de código:
- `BEHAVIOR_TREE_GUIDE.md` (código)
- `UI_HUD_GUIDE.md` (código)
