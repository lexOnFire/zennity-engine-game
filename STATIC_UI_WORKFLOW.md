# 🎨 Workflow Completo: UI Estática 100% Visual

**Zennity permite criar UIs inteiramente no editor, sem código.**

A chave: **Crie tudo no UI Builder (editor), depois manipule com nós visuais.**

---

## 📋 O Que É UI Estática?

### ✅ Você CAN fazer:
- Criar widgets (Label, Button, ProgressBar, Image, etc)
- Posicionar e dimensionar
- Mudar cores, fontes, textos
- Mostrar/ocultar
- Animar propriedades
- Responder a cliques

### ❌ Você NÃO pode fazer:
- Criar widgets **em tempo de execução** (exemplo: criar nova label ao coletar item)
- Remover widgets dinamicamente
- Gerar UI procedural

**Se precisa apenas de UI fixa, você está 100% visual!** ✨

---

## 🎯 Exemplo Prático: Jogo de Coleta

### Estrutura da UI (estática)

```
Canvas (Screen Space)
├─ Panel_HUD (painel preto com elementos do jogo)
│  ├─ Label_Score (texto: "Score: 0")
│  ├─ ProgressBar_HP (100/100)
│  ├─ Label_Timer (texto: "Tempo: 60s")
│  └─ Button_Pause (botão ESC)
├─ Panel_GameOver (oculta até fim do jogo)
│  ├─ Label_Result (texto: "GAME OVER")
│  └─ Button_Restart (botão para recomeçar)
└─ Panel_HowToPlay (dicas iniciais)
   └─ Label_Instructions (texto com instruções)
```

**Tudo criado no UI Builder - nada em código!**

---

## 🛠️ Passo a Passo: Criar HUD

### 1️⃣ Criar Layout no UI Builder

1. **Novo Layout**
   ```
   Menu → New → UI Layout
   ```

2. **Criar Canvas**
   - Aparece automaticamente
   - Configure: `Render Mode` = "Screen Space"

3. **Adicionar Panel_HUD**
   - Botão "Panel" → novo panel
   - Rename: "Panel_HUD"
   - Tamanho: 400×200
   - Posição: Top-Left
   - BG Color: Preto com transparência

4. **Adicionar Widgets dentro de Panel_HUD**

   **Label_Score:**
   - Botão "Label" → novo label
   - Rename: "Label_Score"
   - Texto: "Score: 0"
   - Posição: 10, 10
   - Tamanho: 200×40
   - Fonte: 24px

   **ProgressBar_HP:**
   - Botão "ProgressBar" → nova barra
   - Rename: "ProgressBar_HP"
   - Valor: 100
   - Valor Max: 100
   - Posição: 10, 60
   - Tamanho: 200×20
   - Cor Fill: Verde

   **Label_Timer:**
   - Botão "Label" → novo label
   - Rename: "Label_Timer"
   - Texto: "Tempo: 60s"
   - Posição: 10, 90
   - Tamanho: 200×40
   - Fonte: 18px

   **Button_Pause:**
   - Botão "Button" → novo botão
   - Rename: "Button_Pause"
   - Texto: "ESC: Pausar"
   - Posição: 220, 10
   - Tamanho: 170×50

5. **Adicionar Panel_GameOver (oculto inicialmente)**
   - Botão "Panel" → novo panel
   - Rename: "Panel_GameOver"
   - Tamanho: 600×400
   - Posição: Centro da tela
   - BG Color: Preto semitransparente
   - **Visível: FALSE** (importante!)

   **Label_Result:**
   - Label: "GAME OVER"
   - Posição: Centro
   - Fonte: 48px
   - Cor: Vermelho

   **Button_Restart:**
   - Botão: "RESTART"
   - Posição: Centro-bottom
   - Tamanho: 200×60

6. **Salvar**
   ```
   Assets/UI/game_hud.zui
   ```

---

## 🎬 Usar a UI na Cena

### 1️⃣ Criar GameObject Canvas

1. Abra **Cena do Jogo**
2. Novo GameObject
3. Rename: "UI_HUD"
4. Component → Canvas
5. Configure:
   - **Layout Path**: `Assets/UI/game_hud.zui`
   - **Render Mode**: "Screen Space"

**Pronto! UI carrega ao iniciar!** ✅

---

## 🔗 Controlar UI com Logic Graph

### Caso 1: Atualizar Score ao Coletar

**Nós:**
```
On Collision (comida)
  ├─ Get Score (variável global)
  ├─ Math Add (score + 1)
  ├─ Set UI Text
  │  ├─ Widget: "Label_Score"
  │  └─ Text: "Score: " + resultado
  └─ Play Sound (collect)
```

**Resultado:** Ao tocar comida, score aumenta e label atualiza.

---

### Caso 2: Reduzir HP ao Tomar Dano

**Nós:**
```
On Enemy Attack
  ├─ Get Health (variável)
  ├─ Math Subtract (health - 25)
  ├─ Set Health (guardar novo valor)
  ├─ Set UI Progress
  │  ├─ Widget: "ProgressBar_HP"
  │  └─ Value: novo health
  └─ If Health <= 0
     └─ Show Panel
        ├─ Widget: "Panel_GameOver"
        └─ Visible: true
```

**Resultado:** Dano reduz HP, barra visual atualiza, ao morrer mostra tela de game over.

---

### Caso 3: Timer Decrescente

**Nós:**
```
Repeat (infinito, 1x por segundo)
  ├─ Get Time Remaining (variável)
  ├─ Math Subtract (time - 1)
  ├─ Set Time (guardar)
  ├─ Set UI Text
  │  ├─ Widget: "Label_Timer"
  │  └─ Text: "Tempo: " + resultado
  └─ If Time <= 0
     └─ Trigger Game Over
```

**Resultado:** Timer visual conta regressivamente.

---

## 🎨 Best Practices: UI Estática

### 1. **Planeje Tudo Antes**
Esboce no papel ou Figma qual será a UI antes de criar no editor.

### 2. **Use Convenção de Nomes**
- Painéis: `Panel_*` (Panel_HUD, Panel_Menu, Panel_Dialog)
- Labels: `Label_*` (Label_Score, Label_Title)
- Botões: `Button_*` (Button_Start, Button_Quit)
- Barras: `ProgressBar_*` (ProgressBar_HP, ProgressBar_Mana)

### 3. **Organize em Hierarquia**
Agrupes widgets relacionados dentro de Panels/Containers.

### 4. **Teste em Várias Resoluções**
Use Âncoras (Anchor) para adaptar a diferentes tamanhos de tela.

### 5. **Limite Visibilidade de Painéis**
- HUD: sempre visível
- Menu: mostrar no Menu
- GameOver: mostrar ao game over
- Pausa: mostrar ao ESC

---

## 📐 Exemplo: Adaptação de Tela

**Como fazer UI se adaptar a diferentes resoluções:**

```
Label_Score:
├─ Anchor: Top-Left
├─ Margin X: 20
├─ Margin Y: 20
→ Sempre 20px do canto superior-esquerdo

Button_Quit:
├─ Anchor: Bottom-Right
├─ Margin X: 20
├─ Margin Y: 20
→ Sempre 20px do canto inferior-direito

ProgressBar_HP:
├─ Anchor: Top-Center
├─ Margin X: 0
├─ Margin Y: 60
→ Sempre centralizado no topo
```

---

## 🐛 Troubleshooting

### Problema: UI não aparece
- [ ] Verifique se Canvas tem `layout_path` correto
- [ ] Verifique se `.zui` existe em `Assets/UI/`
- [ ] Verifique se Canvas está Visível

### Problema: Widget não atualiza
- [ ] Verifique se nome do widget está correto (case-sensitive!)
- [ ] Verifique se nó está conectado na Logic Graph
- [ ] Veja console para erros

### Problema: Posição errada
- [ ] Verifique Anchor (Top-Left? Center? etc)
- [ ] Ajuste Margin X/Y
- [ ] Teste em diferentes resoluções

---

## 📋 Checklist: UI Estática Completa

- [ ] Planar estrutura da UI (desenhar)
- [ ] Criar Layout (.zui) no UI Builder
- [ ] Adicionar todos os Widgets necessários
- [ ] Configurar nomes (Label_*, Button_*, etc)
- [ ] Posicionar e dimensionar
- [ ] Definir cores e fontes
- [ ] Testar visibilidade de Painéis
- [ ] Salvar em `Assets/UI/`
- [ ] Criar GameObject Canvas na cena
- [ ] Configurar `layout_path`
- [ ] Criar Logic Graph para atualizar valores
- [ ] Testar tudo em Play mode

---

## 🎉 Resultado Final

✅ UI 100% visual, sem código  
✅ Atualização dinâmica de valores (texto, barras, visibilidade)  
✅ Responsiva a diferentes resoluções  
✅ Fácil de manter e editar  

**Seu jogo tem UI profissional, criada totalmente no editor!** 🎮✨

---

**Próximo:** Leia [BEHAVIOR_TREE_GUIDE.md](./BEHAVIOR_TREE_GUIDE.md) para controlar comportamentos visualmente!
