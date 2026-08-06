# Tutorial: Criar um Contador em 5 Minutos

Aprenda a criar um contador simples que incrementa e decrementa usando os novos nós de UI.

## Objetivo Final

Uma UI com:
- Label mostrando número (0-999)
- Botão "+" que incrementa
- Botão "-" que decrementa

**Tempo:** ~5 minutos
**Dificuldade:** ⭐ Iniciante

---

## Step 1: Criar Canvas e Label (2 min)

1. **Nova Scene** → File → New Scene
2. **Adiciona Canvas:**
   - Right-click na Hierarchy → Create → Canvas
   - Nome: "CounterUI"
3. **Adiciona Label:**
   - Right-click em CounterUI → Create → Label
   - Nome: "CounterLabel"
   - Propriedades:
     - Text: "0"
     - Font Size: 32
     - Color: Branco (#FFFFFF)
4. **Position:** Centro da tela (x=0, y=0)

---

## Step 2: Criar Botões (2 min)

**Botão +:**
1. Right-click em CounterUI → Create → Button
2. Nome: "IncrementButton"
3. Propriedades:
   - Text: "+"
   - Position: x=-100, y=-100
   - Size: 80x40

**Botão -:**
1. Right-click em CounterUI → Create → Button
2. Nome: "DecrementButton"
3. Propriedades:
   - Text: "-"
   - Position: x=+100, y=-100
   - Size: 80x40

---

## Step 3: Conectar Lógica com Logic Graph (1 min)

**Configurar o Botão +:**

1. Seleciona `IncrementButton` na Hierarchy
2. Na Inspector → Add Component → Logic Graph
3. Clica em "Open in Editor"
4. Na paleta (esquerda), busca: "increment" 
5. Arrasta `Increment UI Value` para o canvas
6. Configura:
   - element: "CounterLabel"
   - amount: 1
   - max_value: 999
7. Conecta:
   - Button.on_click → Increment UI Value.in
   - Increment UI Value.next → (fim)
8. Salva (Ctrl+S)

**Configurar o Botão -:**

1. Seleciona `DecrementButton`
2. Logic Graph → Open in Editor
3. Arrasta `Decrement UI Value` para o canvas
4. Configura:
   - element: "CounterLabel"
   - amount: 1
   - min_value: 0
5. Conecta:
   - Button.on_click → Decrement UI Value.in
6. Salva

---

## Step 4: Testar (Play Mode)

1. **Play** (F5 ou botão Play)
2. Clica no botão "+" → contador deve virar 1
3. Clica novamente → vira 2
4. Clica no botão "-" → volta a 1
5. **Stop** (Shift+F5)

---

## Resultado

```
        [0]
        
    [-] [+]
```

Pronto! Seu contador funciona em ~5 minutos sem escrever código.

---

## Variações (Próximos Passos)

### Variação 1: Mostrar "Pontos: X"

1. Seleciona CounterLabel
2. Adiciona Logic Graph
3. Arrasta `Format UI Text`
4. Configura:
   - element: "CounterLabel"
   - format_string: "Pontos: {value}"
   - value: (conecta com Increment/Decrement output)

**Resultado:** "Pontos: 42"

---

### Variação 2: Limite Máximo com Som

1. Depois do `Increment UI Value`, adiciona:
   - Branch (Is Value == 999?)
   - Se True → Play Sound ("limit_reached")

2. Idem para `Decrement UI Value` com min_value.

---

### Variação 3: Animação ao Incrementar

1. Depois do `Increment UI Value`, adiciona:
   - `Animate Material`
   - target: CounterLabel
   - property: "color"
   - target_value: 255 (branco)
   - duration: 0.1
   - easing: "ease_out"

**Resultado:** Label pisca branco quando incrementa.

---

## Dicas

✅ **Nomes consistentes:** Use "CounterLabel" aqui e no nó também.
✅ **Max/Min Values:** Sempre defina limites para evitar valores inválidos.
✅ **Teste incrementalmente:** Faça um botão funcionar, depois o outro.
❌ **Não:** Não tente adicionar tudo de uma vez.

---

## Troubleshooting

### "Nó vermelho" (erro):
- Verifique se o nome do elemento existe (case-sensitive)
- CounterLabel ≠ counterlabel

### Botão não responde:
- Verifique se on_click está conectado ao nó
- Teste com Print para confirmar

### Comportamento estranho:
- Verifi que valor inicial do label (deve ser "0" ou número)
- Salve (Ctrl+S) e recarregue a scene

---

## Próximo: Usar UIBinder para Auto-Sync

Se quiser sincronização automática (sem nós), leia [COMPONENT_SYSTEM_GUIDE.md](../COMPONENT_SYSTEM_GUIDE.md) seção "UIBinder".
