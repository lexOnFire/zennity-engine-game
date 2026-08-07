# 🎨 Zennity Engine - Guia do Editor Visual

Bem-vindo! **Zennity é um motor de jogo 100% visual**. Nenhum código Python é necessário para criar lógica - tudo é feito através do editor gráfico.

---

## 📚 Índice

1. [Primeiros Passos](#primeiros-passos)
2. [Ferramentas Visuais](#ferramentas-visuais)
3. [Fluxo de Trabalho Completo](#fluxo-de-trabalho-completo)
4. [Exemplos Práticos](#exemplos-práticos)
5. [Troubleshooting](#troubleshooting)

---

## 🚀 Primeiros Passos

### Abrir o Editor

```bash
python -m zennity_run
```

Isso abre o **Zennity Studio** com acesso a todas as ferramentas visuais.

### Estrutura de Pastas do Projeto

```
Assets/
├── Scenes/          ← Cenas (.zscene)
├── UI/              ← Layouts de UI (.zui)
├── Behaviors/       ← Árvores de comportamento (.zbehavior)
├── Logic/           ← Gráficos de lógica (.zlogic)
├── Sprites/         ← Imagens e sprites
└── Audio/           ← Áudio (MP3, WAV, OGG)
```

---

## 🎯 Ferramentas Visuais

### 1️⃣ **Scene Editor** (Cenas)
**Arquivo:** `.zscene` (formato JSON)

**O que faz:**
- Posicionar objetos no mundo
- Definir câmera e viewport
- Configurar física e colisores
- Organizar hierarquia de objetos

**Como usar:**
1. Novo → Scene
2. Adicione GameObjects (Sprite, Tilemap, UI Canvas)
3. Ajuste posição, rotação, escala
4. Salve como `Assets/Scenes/minha_cena.zscene`

---

### 2️⃣ **UI Builder** (Interface do Usuário)
**Arquivo:** `.zui` (formato JSON)

**Widgets disponíveis:**
- **Label** - Texto simples
- **Button** - Botão interativo
- **Image** - Imagem/Sprite
- **ProgressBar** - Barra de progresso (HP, stamina, etc)
- **Panel** - Painel de fundo
- **Input** - Campo de entrada
- **Container** - Agrupa widgets
- **Canvas** - Raiz da UI

**Como criar uma UI:**
1. Abra o **UI Builder**
2. Clique em "Novo"
3. Adicione widgets (Button, Label, etc)
4. Configure posição, texto, cores
5. Salve como `Assets/UI/meu_hud.zui`

**Para usar na cena:**
- Crie um GameObject do tipo "Canvas"
- Configure: `layout_path` = "Assets/UI/meu_hud.zui"

---

### 3️⃣ **Behavior Tree** (Comportamento de NPCs)
**Arquivo:** `.zbehavior` (formato JSON)

**Categorias de nós:**
- **Composite** - Selector, Sequence
- **Decorator** - Repeat, Cooldown, Inverter
- **Condition** - Target In Range, Parameter Check, Health Check
- **Action** - Move, Chase, Attack, Idle
- **UI Actions** - Set UI Text, Progress, Visible, Increment, Decrement

**Exemplo: NPC que patrulha e chasa comida**
```
Selector
├─ Sequence (quando comida perto)
│  ├─ Target In Range (tag: Food, distance: 400)
│  ├─ Chase (target: Food)
│  └─ Set UI Progress (widget: hp_bar)
└─ Patrol (entre dois pontos)
```

**Como criar:**
1. Novo → Behavior Tree
2. Clique nos nós para adicionar
3. Conecte entrada→saída com setas
4. Salve como `Assets/Behaviors/meu_comportamento.zbehavior`

**Para usar:**
- GameObject → Component → Behavior
- Configure: `controller_path` = "Assets/Behaviors/..."

---

### 4️⃣ **Logic Graph** (Lógica de Eventos)
**Arquivo:** `.zlogic` (formato JSON)

**Categorias de nós:**
- **Input** - Teclado, Mouse, Collider
- **Flow Control** - If/Else, Loop
- **Math** - Operações matemáticas
- **String** - Manipulação de texto
- **Physics** - Rigidbody, Collider
- **UI** - Set UI Text, Progress, Visible
- **Scene** - Load Scene, Find Object
- **Debug** - Log, Print

**Exemplo: Coletar comida ao tocar**
```
On Collision Enter
├─ If (tag == "Food")
│  ├─ Destroy Object
│  ├─ Set UI Text (widget: score, text: score + 1)
│  └─ Play Sound (sfx_collect)
└─ Log ("Comida coletada!")
```

**Como criar:**
1. Novo → Logic Graph
2. Arraste nós para a tela
3. Conecte portas (saída de um → entrada de outro)
4. Salve como `Assets/Logic/minha_logica.zlogic`

**Para usar:**
- GameObject → Component → Logic
- Configure: `graph_path` = "Assets/Logic/..."

---

## 🔄 Fluxo de Trabalho Completo

### Exemplo: Criar um Jogo de Coleta Simples

#### Passo 1: Cena Base
1. Novo → Scene
2. Adicione background (Sprite)
3. Adicione player (Sprite + Collider)
4. Adicione comida (Sprite + Collider as trigger)
5. Salve: `Assets/Scenes/main.zscene`

#### Passo 2: HUD
1. Novo → UI Builder
2. Adicione Label "Score: 0"
3. Adicione ProgressBar "HP: 100/100"
4. Salve: `Assets/UI/hud.zui`
5. Na Scene, crie GameObject "Canvas" e configure `layout_path`

#### Passo 3: Comportamento do NPC (Comida)
1. Novo → Behavior Tree
2. Nó Repeat (infinito)
3. Nó Patrol entre dois pontos
4. Salve: `Assets/Behaviors/comida_patrulha.zbehavior`
5. No GameObject "comida", configure Component Behavior

#### Passo 4: Lógica do Player
1. Novo → Logic Graph
2. On Key Down (SPACE) → Jump
3. On Collision (Food) → Increment Score
4. Salve: `Assets/Logic/player_controls.zlogic`
5. No GameObject "player", configure Component Logic

#### Resultado
✅ Jogo completo, 100% visual, 0% código!

---

## 💡 Exemplos Práticos

### Reduzir Barra de Progresso (HP)
**Na Behavior Tree:**
1. Nó: Decrementar Valor UI
2. Widget: `hp_bar`
3. Quantidade: `10.0`

### Trocar de Cena
**Na Logic Graph:**
1. Nó: Load Scene
2. Scene Path: `Assets/Scenes/level2.zscene`

### Verificar Distância até Inimigo
**Na Behavior Tree:**
1. Nó: Target In Range
2. Target: `Enemy`
3. Distance: `200.0`
4. Success → Chase
5. Failure → Patrol

---

## 🐛 Troubleshooting

### Problema: Nó de UI não encontra widget
**Solução:**
- Verifique se o widget está no arquivo `.zui`
- Verifique se o nome do widget é **exato** (case-sensitive)
- Se widget está em objeto diferente, adicione como filho na cena

### Problema: Behavior Tree não executa
**Solução:**
- Verifique se `start_node` está configurado no `.zbehavior`
- Verifique se o GameObject tem Component Behavior ativo
- Verifique `controller_path` aponta para arquivo válido

### Problema: UI não aparece na tela
**Solução:**
- Verifique se Canvas tem `layout_path` correto
- Verifique se Canvas está visível (check "Visible")
- Verifique se Canvas tem tamanho maior que 0

---

## 📖 Próximos Passos

- Leia [UI_BUILDER_GUIDE.md](./UI_BUILDER_GUIDE.md) para detalhes de UI
- Leia [BEHAVIOR_TREE_GUIDE.md](./BEHAVIOR_TREE_GUIDE.md) para detalhes de BT
- Leia [LOGIC_GRAPH_GUIDE.md](./LOGIC_GRAPH_GUIDE.md) para detalhes de lógica
- Explore exemplos em `Assets/Scenes/`

---

**Zennity: Crie Jogos Visualmente!** 🎮✨
