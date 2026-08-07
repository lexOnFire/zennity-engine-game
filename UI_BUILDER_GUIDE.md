# 🎨 Guia Completo: UI Builder

Crie interfaces de usuário visualmente, sem código! Deslize widgets, configure cores, tamanhos - tudo no editor.

---

## 📦 Tipos de Widget

### 📝 **Label** - Texto Simples
**Uso:** HUD, títulos, diálogos, informações

**Propriedades:**
- **Texto**: O que escrever
- **Fonte**: Tamanho em pixels
- **Cor**: RGB do texto
- **Visível**: Mostrar/ocultar

**Exemplo na Cena:**
```
Set UI Text
├─ Widget: "score_label"
└─ Texto: "Score: 1000"
```

---

### 🔘 **Button** - Botão Interativo
**Uso:** Menus, confirmações, ações

**Propriedades:**
- **Texto**: Label do botão
- **Interativo**: Pode clicar?
- **Cor Hover**: Cor ao passar mouse
- **Evento**: Ao clicar, executar ação

**Exemplo de Fluxo:**
1. Usuário clica botão "Iniciar"
2. Logic Graph detecta click
3. Carrega a cena do jogo

---

### 🖼️ **Image** - Sprite/Textura
**Uso:** Fundos, ícones, retratos

**Propriedades:**
- **Caminho**: Arquivo de imagem (ex: `Assets/Sprites/icon.png`)
- **Alfa**: Transparência (0-255)
- **Tamanho**: Largura × Altura

---

### 📊 **ProgressBar** - Barra de Progresso
**Uso:** HP, Stamina, XP, Carregamento

**Propriedades:**
- **Valor**: Valor atual (ex: 75)
- **Valor Max**: Valor máximo (ex: 100)
- **Cor Fill**: Cor do preenchimento (verde para HP)
- **BG Color**: Cor de fundo (cinza)
- **Cor Border**: Cor da borda

**Exemplo:**
```
HP Bar:
├─ Valor: 50
├─ Valor Max: 100
├─ Cor Fill: Verde (#2ECC71)
└─ BG Color: Escuro (#1C2330)
→ Mostra 50% preenchida
```

---

### 📦 **Panel** - Painel de Fundo
**Uso:** Agrupar elementos, criar áreas visuais

**Propriedades:**
- **BG Color**: Cor de fundo
- **Largura/Altura**: Tamanho
- **Visível**: Mostrar/ocultar

---

### ⌨️ **Input** - Campo de Texto
**Uso:** Nomes, senhas, chat

**Propriedades:**
- **Placeholder**: Texto cinzento quando vazio
- **Largura**: Comprimento do campo
- **Interativo**: Pode digitar?

---

### 🎁 **Container** - Agrupa Widgets
**Uso:** Auto-layout (horizontal/vertical)

**Propriedades:**
- **Layout Mode**: Vertical, Horizontal, Free
- **Filhos**: Widgets dentro do container

---

### 🖥️ **Canvas** - Raiz da UI
**Propriedades:**
- **Render Mode**: 
  - **Screen Space**: UI fixa na tela (menus, HUD)
  - **World Space**: UI no mundo do jogo (placas, letreiros)
- **Layout Path**: Arquivo `.zui` a carregar
- **Visible**: Mostrar/ocultar tudo

---

## 🎯 Workflow: Criar um HUD Completo

### Passo 1: Novo Layout
1. Menu → New → UI Layout
2. Canvas aparece automaticamente

### Passo 2: Adicionar Widgets
1. **Botão "ProgressBar"** na toolbar
   - Cria ProgressBar novo
   - Nome automático: ProgressBar, ProgressBar_1, etc
   - Rebatize para "hp_bar"

2. **Clique e arraste** na prévia para posicionar
   - X, Y: coordenadas
   - Largura, Altura: tamanho

### Passo 3: Configurar Propriedades
Na seção **Propriedades** (right panel):

```
hp_bar:
├─ X: 20
├─ Y: 20
├─ Largura: 200
├─ Altura: 20
├─ Valor: 100
├─ Valor Max: 100
├─ Cor Fill: Verde
└─ BG Color: Escuro
```

### Passo 4: Salvar
- Salve como `Assets/UI/hud.zui`

### Passo 5: Usar na Cena
1. Novo GameObject
2. Component → Canvas
3. Configure:
   - **Layout Path**: `Assets/UI/hud.zui`
   - **Render Mode**: Screen Space (se HUD)
4. Pronto! Canvas carrega a UI

---

## 🎨 Design Tips

### Cores Recomendadas
| Uso | Cor | Hex |
|---|---|---|
| Fundo | Cinza Escuro | #1C2330 |
| HP/Vida | Verde | #2ECC71 |
| Dano/Perda | Vermelho | #E74C3C |
| Texto | Branco | #FFFFFF |
| Botão | Azul | #3498DB |
| Desativado | Cinza | #7F8C8D |

### Tamanho de Fonte
- **Headers**: 32-48 px
- **Body**: 18-24 px
- **UI Pequena**: 12-16 px

### Hierarquia de UI
```
Canvas (Screen Space)
├─ Panel_Background (fundo)
├─ Panel_HUD
│  ├─ Label_Score
│  ├─ ProgressBar_HP
│  └─ Button_Pause
└─ Panel_Dialog (oculto até ser necessário)
```

---

## 🔗 Conectar UI com Behavior Tree

### Caso 1: Reduzir HP ao Tomar Dano

**Na Behavior Tree:**
```
Chase (persegue player)
  ↓
Attack (ataca)
  ↓
Decrement UI Value
├─ Widget: "hp_bar"
└─ Quantidade: 25.0
```

**Resultado:** Cada ataque reduz a barra em 25 pontos.

---

### Caso 2: Mostrar/Ocultar Painel

**Na Logic Graph:**
```
On Key Down (ESC)
  ↓
Set UI Visible
├─ Widget: "panel_pause"
└─ Visible: true (toggle)
```

**Resultado:** Pressionar ESC abre o menu de pausa.

---

### Caso 3: Atualizar Score

**Na Logic Graph:**
```
On Collision (Food)
  ↓
Increment UI Value
├─ Widget: "score_label"
└─ Quantidade: 1.0
  ↓
Play Sound (sfx_collect)
```

**Resultado:** Coletar comida +1 no score e toca som.

---

## 📐 Posicionamento Avançado

### Âncoras (Anchor)
Define o ponto de referência da UI:
- **Top-Left**: Canto superior esquerdo
- **Top-Right**: Canto superior direito
- **Bottom-Left**: Canto inferior esquerdo
- **Bottom-Right**: Canto inferior direito
- **Center**: Centro da tela

**Uso:** Label "Score" no top-right sempre fica lá mesmo com resize de tela.

---

### Margins
Espaço a partir da âncora:
- **Margin X**: Distância horizontal
- **Margin Y**: Distância vertical

**Exemplo:**
```
Label "Score"
├─ Anchor: Top-Right
├─ Margin X: 20 (20px da direita)
└─ Margin Y: 20 (20px do topo)
```

---

## 🧪 Testar UI

1. **Play** (execute a cena)
2. Observe se UI aparece corretamente
3. Se usar World Space, verifique posição no mundo
4. Clique em botões para testar interatividade

### Debug
- Se UI não aparece: Verifique "Visible"
- Se posição está errada: Verifique X, Y, Anchor
- Se muito pequeno: Verifique Largura, Altura

---

## 📋 Checklist: Criar HUD

- [ ] Novo layout (Canvas)
- [ ] Adicione widgets (Label, ProgressBar, etc)
- [ ] Configure nomes (hp_bar, score_label, etc)
- [ ] Posicione corretamente (X, Y)
- [ ] Defina cores e tamanho de fonte
- [ ] Ajuste Valores iniciais
- [ ] Salve como `.zui`
- [ ] Crie GameObject Canvas na cena
- [ ] Configure `layout_path` apontando para `.zui`
- [ ] Teste no Play mode

---

**Próximo:** Leia [BEHAVIOR_TREE_GUIDE.md](./BEHAVIOR_TREE_GUIDE.md) para controlar a UI com comportamentos! 🌳
